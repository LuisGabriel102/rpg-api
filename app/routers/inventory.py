"""Router de inventario e bestiario — v3 com cache e event sourcing."""

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.auth import verify_token
from app.events import record_event
from app.cache import cache_get, cache_set

router = APIRouter()


class AddItemRequest(BaseModel):
    personagem_id: int
    item_id: Optional[int] = Field(None, description="ID do item em ref_itens (NULL se custom)")
    nome_custom: Optional[str] = Field(None, description="Nome se nao existe em ref_itens")
    quantidade: int = Field(1, ge=1)
    sessao_id: Optional[int] = None


@router.get("/character/{personagem_id}", operation_id="getInventory", summary="Inventario do personagem",
            description="Itens do personagem. apenas_equipados=true filtra equipados.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_inventory(personagem_id: int, apenas_equipados: bool = False,
                        conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_inventario_personagem(%s, %s)", (personagem_id, apenas_equipados))
        result = await cur.fetchone()
    return result or {"itens": []}


@router.post("/add", operation_id="addItem", summary="Adicionar item",
             description="Adiciona item ao inventario. Use item_id ou nome_custom.",
             openapi_extra={"x-openai-isConsequential": True})
async def add_item(payload: AddItemRequest, conn: AsyncConnection = Depends(get_db),
                   _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM adicionar_item_inventario(%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.item_id, payload.nome_custom,
                           payload.quantidade, payload.sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "ITEM_ADDED",
                       {"item_id": payload.item_id, "nome_custom": payload.nome_custom, "qtd": payload.quantidade},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "item_adicionado"}


@router.get("/items/search", operation_id="searchItems", summary="Buscar itens no catalogo",
            description="Busca em ref_itens (tabela vazia, sera populada).",
            openapi_extra={"x-openai-isConsequential": False})
async def search_items(nome: Optional[str] = Query(None), tipo: Optional[str] = Query(None),
                       raridade: Optional[str] = Query(None), limite: int = Query(20, ge=1, le=100),
                       conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    conditions, params = [], []
    if nome:
        conditions.append("(nome ILIKE %s OR nome_ptbr ILIKE %s)"); params.extend([f"%{nome}%", f"%{nome}%"])
    if tipo:
        conditions.append("tipo = %s"); params.append(tipo)
    if raridade:
        conditions.append("raridade = %s"); params.append(raridade)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limite)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""SELECT id, nome, nome_ptbr, tipo, subtipo, raridade, peso_kg,
                       preco_po, dano_dado, dano_tipo, descricao
                FROM ref_itens {where} ORDER BY nome LIMIT %s""", params)
        itens = await cur.fetchall()
    return {"total": len(itens), "itens": itens}


@router.get("/creatures/search", operation_id="searchCreatures", summary="Buscar criaturas",
            description="Busca entre 2.138 criaturas. Filtros: nome, tipo, CR, tamanho.",
            openapi_extra={"x-openai-isConsequential": False})
async def search_creatures(nome: Optional[str] = Query(None), tipo: Optional[str] = Query(None),
                           cr_min: Optional[float] = Query(None), cr_max: Optional[float] = Query(None),
                           tamanho: Optional[str] = Query(None), limite: int = Query(20, ge=1, le=100),
                           conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    cache_key = f"creatures:{nome}:{tipo}:{cr_min}:{cr_max}:{tamanho}:{limite}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    conditions, params = [], []
    if nome:
        conditions.append("(nome ILIKE %s OR nome_ptbr ILIKE %s)"); params.extend([f"%{nome}%", f"%{nome}%"])
    if tipo:
        conditions.append("tipo ILIKE %s"); params.append(f"%{tipo}%")
    if cr_min is not None:
        conditions.append("cr >= %s"); params.append(cr_min)
    if cr_max is not None:
        conditions.append("cr <= %s"); params.append(cr_max)
    if tamanho:
        conditions.append("tamanho = %s"); params.append(tamanho)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limite)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""SELECT id, nome, nome_ptbr, tipo, subtipo, tamanho, cr,
                       hp_medio, ca, ca_descricao, forca, destreza, constituicao,
                       inteligencia, sabedoria, carisma, fortitude, reflexos, vontade, xp_recompensa
                FROM ref_criaturas {where} ORDER BY cr, nome LIMIT %s""", params)
        criaturas = await cur.fetchall()
    result = {"total": len(criaturas), "criaturas": criaturas}
    cache_set(cache_key, result)
    return result


@router.get("/creatures/{criatura_id}", operation_id="getCreatureDetail", summary="Detalhes da criatura",
            description="Ficha completa com saves hibridos, resistencias e dados JSON.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_creature_detail(criatura_id: int, conn: AsyncConnection = Depends(get_db),
                              _token: str = Depends(verify_token)):
    cached = cache_get(f"creature:{criatura_id}")
    if cached:
        return cached
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM ref_criaturas WHERE id = %s", (criatura_id,))
        criatura = await cur.fetchone()
    if not criatura:
        raise HTTPException(status_code=404, detail="Criatura nao encontrada")
    cache_set(f"creature:{criatura_id}", criatura)
    return criatura
