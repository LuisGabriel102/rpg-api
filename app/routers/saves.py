"""Router de save points e historico de eventos."""

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional
import json
from app.database import get_db
from app.auth import verify_token
from app.events import get_events

router = APIRouter()


class CreateSavePointRequest(BaseModel):
    personagem_id: int
    nome: str = Field(..., description="Nome descritivo: 'Antes da dungeon do dragao'")
    sessao_id: Optional[int] = None


class RestoreSavePointRequest(BaseModel):
    save_point_id: int
    personagem_id: int


@router.post(
    "/create",
    operation_id="createSavePoint",
    summary="Criar save point",
    description="Salva snapshot completo do personagem (stats, inventario, condicoes, posicao). Usar antes de decisoes arriscadas.",
    openapi_extra={"x-openai-isConsequential": True},
)
async def create_save_point(
    payload: CreateSavePointRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    # Coleta snapshot completo do personagem
    async with conn.cursor(row_factory=dict_row) as cur:
        # Ficha
        await cur.execute('SELECT * FROM "fichaPersonagem"(%s)', (payload.personagem_id,))
        ficha = await cur.fetchone()
        if not ficha:
            raise HTTPException(status_code=404, detail="Personagem nao encontrado")

        # Inventario
        await cur.execute("SELECT * FROM get_inventario_personagem(%s, %s)", (payload.personagem_id, False))
        inventario = await cur.fetchone()

        # Condicoes
        await cur.execute(
            """SELECT pc.*, rc.nome, rc.efeito_mecanico FROM personagem_condicoes pc
               JOIN ref_condicoes rc ON pc.condicao_id = rc.id
               WHERE pc.personagem_id = %s""",
            (payload.personagem_id,),
        )
        condicoes = await cur.fetchall()

        # Maestrias
        await cur.execute("SELECT * FROM listar_maestrias_personagem(%s)", (payload.personagem_id,))
        maestrias = await cur.fetchone()

        snapshot = {
            "ficha": ficha,
            "inventario": inventario,
            "condicoes": condicoes,
            "maestrias": maestrias,
        }

        await cur.execute(
            """INSERT INTO player_save_points (personagem_id, nome, snapshot, sessao_id)
               VALUES (%s, %s, %s::jsonb, %s)
               RETURNING id, nome, created_at""",
            (payload.personagem_id, payload.nome, json.dumps(snapshot, default=str), payload.sessao_id),
        )
        result = await cur.fetchone()

    return {"status": "save_point_criado", **result}


@router.get(
    "/list/{personagem_id}",
    operation_id="listSavePoints",
    summary="Listar save points",
    description="Retorna todos os save points do personagem, do mais recente ao mais antigo.",
    openapi_extra={"x-openai-isConsequential": False},
)
async def list_save_points(
    personagem_id: int,
    limite: int = 10,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """SELECT id, nome, created_at, sessao_id
               FROM player_save_points
               WHERE personagem_id = %s
               ORDER BY created_at DESC LIMIT %s""",
            (personagem_id, limite),
        )
        saves = await cur.fetchall()
    return {"total": len(saves), "save_points": saves}


@router.get(
    "/events",
    operation_id="getEventHistory",
    summary="Historico de eventos do jogo",
    description="Retorna eventos registrados (dano, magias, level up, etc.). Filtre por tipo, sessao ou personagem.",
    openapi_extra={"x-openai-isConsequential": False},
)
async def event_history(
    aggregate_type: str = "",
    event_type: str = "",
    sessao_id: int = 0,
    personagem_id: int = 0,
    limite: int = 50,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    events = await get_events(
        conn,
        aggregate_type=aggregate_type or None,
        event_type=event_type or None,
        sessao_id=sessao_id or None,
        limite=limite,
    )
    return {"total": len(events), "events": events}
