"""Router de magia com cache em memoria e paginacao."""

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from typing import Optional
from app.database import get_db
from app.auth import verify_token
from app.cache import cache_get, cache_set

router = APIRouter()


@router.get("/grimoire/{personagem_id}", operation_id="getGrimoire", summary="Grimorio do personagem",
            description="Magias conhecidas. apenas_preparadas=true filtra preparadas.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_grimoire(personagem_id: int, apenas_preparadas: bool = False,
                       conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_grimorio(%s, %s)", (personagem_id, apenas_preparadas))
        result = await cur.fetchone()
    return result or {"magias": []}


@router.post("/prepare", operation_id="prepareSpell", summary="Preparar magia",
             description="Marca magia como preparada ou remove da lista.",
             openapi_extra={"x-openai-isConsequential": True})
async def prepare_spell(personagem_id: int, magia_id: int, preparar: bool = True,
                        conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM preparar_magia(%s,%s,%s)", (personagem_id, magia_id, preparar))
        result = await cur.fetchone()
    return result or {"status": "magia_atualizada"}


@router.post("/concentrate", operation_id="startConcentration", summary="Iniciar concentracao",
             description="Registra concentracao em magia. Cancela anterior automaticamente.",
             openapi_extra={"x-openai-isConsequential": True})
async def start_concentration(personagem_id: int, magia_id: int, sessao_id: int,
                              conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM iniciar_concentracao(%s,%s,%s)", (personagem_id, magia_id, sessao_id))
        result = await cur.fetchone()
    return result or {"status": "concentracao_iniciada"}


@router.get("/search", operation_id="searchSpells", summary="Buscar magias",
            description="Busca entre as 2.126 magias. Filtre por familia, nivel (0-9), escola ou nome. Paginado.",
            openapi_extra={"x-openai-isConsequential": False})
async def search_spells(
    familia: Optional[str] = Query(None, description="Familia magica (ex: Piromancia)"),
    nivel: Optional[int] = Query(None, ge=0, le=9, description="Nivel da magia (0-9)"),
    escola: Optional[str] = Query(None, description="Escola (ex: Evocacao)"),
    nome: Optional[str] = Query(None, description="Busca parcial no nome"),
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, description="Paginacao: pular N resultados"),
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    # Cache para buscas frequentes sem filtros
    cache_key = f"spells:{familia}:{nivel}:{escola}:{nome}:{limite}:{offset}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    conditions = []
    params = []

    if familia:
        conditions.append("familia_magica = %s")
        params.append(familia)
    if nivel is not None:
        conditions.append("nivel_original = %s")
        params.append(nivel)
    if escola:
        conditions.append("escola = %s")
        params.append(escola)
    if nome:
        _nome = nome.replace("%", "\\%").replace("_", "\\_")
        conditions.append("nome ILIKE %s")
        params.append(f"%{_nome}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.extend([limite, offset])

    async with conn.cursor(row_factory=dict_row) as cur:
        # Count total
        await cur.execute(f"SELECT COUNT(*) as total FROM magias {where}", params[:-2])
        count_result = await cur.fetchone()
        total = count_result["total"] if count_result else 0

        await cur.execute(
            f"""SELECT id, nome, nivel_original, mp_custo, escola, familia_magica,
                       alcance, duracao, requer_concentracao, salvar_hibrido
                FROM magias {where}
                ORDER BY nivel_original, nome
                LIMIT %s OFFSET %s""",
            params,
        )
        magias = await cur.fetchall()

    result = {"total": total, "returned": len(magias), "offset": offset, "limit": limite, "magias": magias}
    cache_set(cache_key, result)
    return result


@router.get("/{magia_id}", operation_id="getSpellDetail", summary="Detalhes da magia",
            description="Campos completos: descricao, maestria, potencializacao, componentes, combos.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_spell_detail(magia_id: int, conn: AsyncConnection = Depends(get_db),
                           _token: str = Depends(verify_token)):
    cached = cache_get(f"spell:{magia_id}")
    if cached:
        return cached

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """SELECT id, nome, nivel_original, mp_custo, escola, familia_magica,
                      descricao, alcance, duracao, tempo_conjuracao, requer_concentracao,
                      componentes, tem_material, material_desc, salvar_hibrido,
                      tipo_dano, enhancements, raiz_id, nome_original, fonte
               FROM magias WHERE id = %s""", (magia_id,))
        magia = await cur.fetchone()
    if not magia:
        raise HTTPException(status_code=404, detail="Magia nao encontrada")
    cache_set(f"spell:{magia_id}", magia)
    return magia


@router.get("/families/list", operation_id="listMagicFamilies", summary="Listar familias magicas",
            description="42 familias com contagem de magias.",
            openapi_extra={"x-openai-isConsequential": False})
async def list_families(conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    cached = cache_get("magic_families")
    if cached:
        return cached

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """SELECT familia_magica, COUNT(*) as total FROM magias
               WHERE familia_magica IS NOT NULL GROUP BY familia_magica ORDER BY familia_magica""")
        familias = await cur.fetchall()

    result = {"total_familias": len(familias), "familias": familias}
    cache_set("magic_families", result)
    return result
