"""Router de mundo e campanha — v3 com SSE para site companion."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from typing import Optional
from sse_starlette.sse import EventSourceResponse
from app.database import get_db, pool
from app.auth import verify_token
import asyncio
import json

router = APIRouter()


@router.get("/rule", operation_id="getRule", summary="Consultar regra",
            description="Busca regra do Sistema Nexus por titulo e/ou categoria. 29 regras.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_rule(titulo: str = "", categoria: str = "",
                   conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_regra(%s, %s)", (titulo, categoria))
        result = await cur.fetchone()
    return result or {}


@router.get("/rules/{categoria}", operation_id="getRulesByCategory", summary="Regras por categoria",
            description="Todas as regras de uma categoria.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_rules_by_category(categoria: str, conn: AsyncConnection = Depends(get_db),
                                _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_regras_categoria(%s)", (categoria,))
        result = await cur.fetchone()
    return result or {"regras": []}


@router.get("/context/{campanha_id}/{personagem_id}", operation_id="getWorldContext",
            summary="Contexto do mundo",
            description="Contexto enriquecido: localizacao, NPCs proximos, missoes, clima.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_world_context(campanha_id: int, personagem_id: int,
                            conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_contexto_mundo(%s, %s)", (campanha_id, personagem_id))
        result = await cur.fetchone()
    return result or {}


@router.get("/campaign/{campanha_id}", operation_id="getCampaignState", summary="Estado da campanha",
            description="Localizacao, data narrativa, clima, eventos ativos.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_campaign_state(campanha_id: int, conn: AsyncConnection = Depends(get_db),
                             _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_estado_campanha(%s)", (campanha_id,))
        result = await cur.fetchone()
    return result or {}


@router.get("/pressure/{campanha_id}", operation_id="getEmotionalPressure",
            summary="Pressao emocional ativa",
            description="Estado de pressao para calibrar tom narrativo.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_emotional_pressure(campanha_id: int, conn: AsyncConnection = Depends(get_db),
                                 _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute('SELECT * FROM "pressaoAtiva"(%s)', (campanha_id,))
        result = await cur.fetchone()
    return result or {}


@router.get("/diagnostic", operation_id="getDiagnostic", summary="Diagnostico do banco",
            description="Contagens de tabelas e estado geral.", include_in_schema=False)
async def get_diagnostic(conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_diagnostico_completo()")
        result = await cur.fetchone()
    return result or {}


@router.get("/version", operation_id="getBankVersion", summary="Versao do banco",
            description="Versao e metadata.", include_in_schema=False)
async def get_version(conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_versao_banco()")
        result = await cur.fetchone()
    return result or {}


# === SSE: Atualizacoes em tempo real para o site NiceGUI ===

@router.get("/sse/{personagem_id}", operation_id="subscribeUpdates",
            summary="[SSE] Stream de atualizacoes em tempo real",
            description="Server-Sent Events para o site companion. NAO para o GPT.",
            include_in_schema=False)
async def sse_updates(personagem_id: int, request: Request):
    """Envia atualizacoes do personagem via SSE a cada 3 segundos."""

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                async with pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute('SELECT * FROM "fichaPersonagem"(%s)', (personagem_id,))
                        ficha = await cur.fetchone()
                        if ficha:
                            yield {"event": "character_update", "data": json.dumps(ficha, default=str)}
            except Exception:
                yield {"event": "error", "data": "connection_failed"}
            await asyncio.sleep(3)

    return EventSourceResponse(event_generator())
