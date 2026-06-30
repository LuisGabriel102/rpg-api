"""Router de NPCs — v3 com anotacoes GPT e event sourcing."""

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.auth import verify_token
from app.events import record_event

router = APIRouter()


class NpcInteractionRequest(BaseModel):
    personagem_id: int
    npc_id: int
    tipo: str = Field(..., description="conversa, troca, combate, ajuda, traicao")
    descricao: str
    impacto_confianca: int = Field(0)
    sessao_id: int


class NpcTrustRequest(BaseModel):
    personagem_id: int
    npc_id: int
    delta: int
    motivo: str
    sessao_id: int


@router.get("/{npc_id}/session/{personagem_id}", operation_id="getNpcForSession",
            summary="NPC preparado para sessao",
            description="Retorna prompt_identidade, prompt_dialogo e contexto do protagonista.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_npc_for_session(npc_id: int, personagem_id: int,
                              conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_npc_para_sessao(%s, %s)", (npc_id, personagem_id))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="NPC nao encontrado")
    return result


@router.get("/{npc_id}/secrets/{trust_level}", operation_id="getNpcSecrets",
            summary="Segredos do NPC por confianca",
            description="APENAS segredos com gate_confianca <= trust_level.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_npc_secrets(npc_id: int, trust_level: int,
                          conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_npc_segredos_disponiveis(%s, %s)", (npc_id, trust_level))
        result = await cur.fetchone()
    return result or {"segredos": []}


@router.get("/{npc_id}/routine/{periodo}", operation_id="getNpcRoutine",
            summary="Rotina do NPC por periodo",
            description="Localizacao e atividade (manha, tarde, noite, madrugada).",
            openapi_extra={"x-openai-isConsequential": False})
async def get_npc_routine(npc_id: int, periodo: str,
                          conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_npc_rotina_periodo(%s, %s)", (npc_id, periodo))
        result = await cur.fetchone()
    return result or {}


@router.get("/profile/{personagem_id}", operation_id="getNarrativeProfile",
            summary="Perfil narrativo completo",
            description="Cicatrizes, bestiario pessoal e relacoes.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_narrative_profile(personagem_id: int,
                                conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_perfil_narrativo_completo(%s)", (personagem_id,))
        result = await cur.fetchone()
    return result or {}


@router.post("/interaction", operation_id="registerNpcInteraction",
             summary="Registrar interacao com NPC",
             description="Registra conversa, troca ou evento. Atualiza confianca.",
             openapi_extra={"x-openai-isConsequential": True})
async def register_interaction(payload: NpcInteractionRequest,
                               conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_interacao_npc(%s,%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.npc_id, payload.tipo,
                           payload.descricao, payload.impacto_confianca, payload.sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "npc", payload.npc_id, "NPC_INTERACTION",
                       {"tipo": payload.tipo, "impacto": payload.impacto_confianca},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "interacao_registrada"}


@router.post("/trust", operation_id="updateNpcTrust", summary="Atualizar confianca",
             description="Ajusta confianca entre personagem e NPC.",
             openapi_extra={"x-openai-isConsequential": True})
async def update_trust(payload: NpcTrustRequest,
                       conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM atualizar_confianca_npc(%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.npc_id, payload.delta, payload.motivo, payload.sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "npc", payload.npc_id, "TRUST_CHANGED",
                       {"delta": payload.delta, "motivo": payload.motivo},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "confianca_atualizada"}


@router.get("/search", operation_id="searchNpcs", summary="Buscar NPCs",
            description="Busca por nome, localizacao ou camada.",
            openapi_extra={"x-openai-isConsequential": False})
async def search_npcs(nome: Optional[str] = Query(None), localizacao: Optional[str] = Query(None),
                      camada: Optional[int] = Query(None, ge=1, le=3), limite: int = Query(20, ge=1, le=100),
                      conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    conditions, params = [], []
    if nome:
        _nome = nome.replace("%", "\\%").replace("_", "\\_")
        conditions.append("nome ILIKE %s"); params.append(f"%{_nome}%")
    if localizacao:
        _loc = localizacao.replace("%", "\\%").replace("_", "\\_")
        conditions.append("localizacao_atual ILIKE %s"); params.append(f"%{_loc}%")
    if camada is not None:
        conditions.append("camada = %s"); params.append(camada)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limite)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""SELECT id, nome, nome_curto, epiteto, raca, localizacao_atual,
                       profissao, camada, status, personality_summary
                FROM npcs {where} ORDER BY nome LIMIT %s""", params)
        npcs = await cur.fetchall()
    return {"total": len(npcs), "npcs": npcs}
