"""Event sourcing — registra cada acao de jogo como evento imutavel.
Permite replay, undo e historico completo."""

import json
from psycopg import AsyncConnection
from psycopg.rows import dict_row
import structlog

logger = structlog.get_logger()


async def record_event(
    conn: AsyncConnection,
    aggregate_type: str,
    aggregate_id: int,
    event_type: str,
    payload: dict,
    sessao_id: int = None,
    personagem_id: int = None,
) -> dict:
    """Registra um evento no log de eventos.

    aggregate_type: 'personagem', 'combate', 'npc', 'campanha'
    event_type: 'DAMAGE_TAKEN', 'SPELL_CAST', 'ITEM_EQUIPPED', 'LEVEL_UP', etc.

    NON-FATAL: se a tabela rpg_events nao existir ou der erro,
    loga warning mas NAO crasheia o endpoint principal.
    """
    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """INSERT INTO rpg_events (aggregate_type, aggregate_id, event_type, payload, sessao_id, personagem_id)
                   VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                   RETURNING id, created_at""",
                (aggregate_type, aggregate_id, event_type, json.dumps(payload), sessao_id, personagem_id),
            )
            result = await cur.fetchone()

        logger.info("event_recorded", event_type=event_type, aggregate=f"{aggregate_type}:{aggregate_id}")
        return result
    except Exception as e:
        logger.warning("event_recording_failed", event_type=event_type, error=str(e)[:200])
        return {}


async def get_events(
    conn: AsyncConnection,
    aggregate_type: str = None,
    aggregate_id: int = None,
    event_type: str = None,
    sessao_id: int = None,
    limite: int = 50,
) -> list:
    """Busca eventos com filtros opcionais."""
    conditions = []
    params = []

    if aggregate_type:
        conditions.append("aggregate_type = %s")
        params.append(aggregate_type)
    if aggregate_id:
        conditions.append("aggregate_id = %s")
        params.append(aggregate_id)
    if event_type:
        conditions.append("event_type = %s")
        params.append(event_type)
    if sessao_id:
        conditions.append("sessao_id = %s")
        params.append(sessao_id)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limite)

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"SELECT * FROM rpg_events {where} ORDER BY created_at DESC LIMIT %s",
            params,
        )
        return await cur.fetchall()
