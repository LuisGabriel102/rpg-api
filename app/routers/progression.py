"""Router de progressao (ANIMA, Maestria, Tecnicas) — v3 com event sourcing."""

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.auth import verify_token
from app.events import record_event

router = APIRouter()


class RegisterAbilityUseRequest(BaseModel):
    personagem_id: int
    habilidade: str
    categoria: str = Field(..., description="dificil ou desesperada")
    contexto: str
    sessao_id: int


class RegisterMasteryUseRequest(BaseModel):
    personagem_id: int
    habilidade: str
    tipo: str = Field(..., description="pericia, magia, recurso_classe, arma, save, ferramenta, tecnica_*")
    custo_mp_base: int = 0
    sessao_id: int
    contexto: str = ""


class UseTechniqueRequest(BaseModel):
    personagem_id: int
    tecnica_id: int
    sessao_id: int
    situacao_risco: bool = True


class RegisterLifeMilestoneRequest(BaseModel):
    personagem_id: int
    tipo: str = Field(..., description="menor, significativo, maior, unico")
    gatilho: str
    habilidade_afetada: Optional[str] = None
    efeito: str
    sessao_id: int
    tipo_unico: Optional[str] = None
    aspecto_alterado: Optional[str] = None
    delta_pressao: int = 0


@router.post("/anima/use", operation_id="registerAbilityUse", summary="Registrar uso ANIMA",
             description="Registra habilidade em situacao de risco. Cap 3 marcas/habilidade/sessao. Desesperada=2pts.",
             openapi_extra={"x-openai-isConsequential": True})
async def register_ability_use(payload: RegisterAbilityUseRequest,
                               conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_uso_habilidade(%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.habilidade, payload.categoria,
                           payload.contexto, payload.sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "ANIMA_USE",
                       {"habilidade": payload.habilidade, "categoria": payload.categoria},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "uso_registrado"}


@router.post("/mastery/use", operation_id="registerMasteryUse", summary="Registrar uso maestria",
             description="Registra uso para Maestria por Uso. 13 tipos. Graus: Familiar(5)->Lenda(80+Marco).",
             openapi_extra={"x-openai-isConsequential": True})
async def register_mastery_use(payload: RegisterMasteryUseRequest,
                               conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_uso_maestria(%s,%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.habilidade, payload.tipo,
                           payload.custo_mp_base, payload.sessao_id, payload.contexto))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "MASTERY_USE",
                       {"habilidade": payload.habilidade, "tipo": payload.tipo},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "maestria_registrada"}


@router.get("/mastery/{personagem_id}", operation_id="listMasteries", summary="Listar maestrias",
            description="Maestrias ativas com grau, usos e beneficios.",
            openapi_extra={"x-openai-isConsequential": False})
async def list_masteries(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                         _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM listar_maestrias_personagem(%s)", (personagem_id,))
        result = await cur.fetchone()
    return result or {"maestrias": []}


@router.get("/mastery/{personagem_id}/check/{habilidade}", operation_id="checkMastery",
            summary="Verificar maestria especifica",
            description="Grau e beneficios de uma habilidade.",
            openapi_extra={"x-openai-isConsequential": False})
async def check_mastery(personagem_id: int, habilidade: str,
                        conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM verificar_maestria(%s, %s)", (personagem_id, habilidade))
        result = await cur.fetchone()
    return result or {"maestria": None}


@router.post("/technique/use", operation_id="useTechnique", summary="Usar tecnica (Bloco 34)",
             description="Gasta MP, registra ANIMA e maestria automaticamente. 200 tecnicas em 8 dominios.",
             openapi_extra={"x-openai-isConsequential": True})
async def use_technique(payload: UseTechniqueRequest,
                        conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM usar_tecnica(%s,%s,%s,%s)",
                          (payload.personagem_id, payload.tecnica_id, payload.sessao_id, payload.situacao_risco))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "TECHNIQUE_USED",
                       {"tecnica_id": payload.tecnica_id},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "tecnica_usada"}


@router.get("/techniques/{personagem_id}", operation_id="getCharacterTechniques",
            summary="Tecnicas do personagem",
            description="Tecnicas desbloqueadas com maestria atual.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_techniques(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                         _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_tecnicas_personagem(%s)", (personagem_id,))
        result = await cur.fetchone()
    return result or {"tecnicas": []}


@router.get("/techniques/available/{personagem_id}", operation_id="getAvailableTechniques",
            summary="Tecnicas disponiveis para aprender",
            description="Tecnicas que pode desbloquear para uma habilidade.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_available_techniques(personagem_id: int, habilidade_id: int,
                                   conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_tecnicas_disponiveis(%s, %s)", (personagem_id, habilidade_id))
        result = await cur.fetchone()
    return result or {"tecnicas": []}


@router.get("/skills/available", operation_id="getAvailableSkills",
            summary="Habilidades aprendiveis",
            description="Habilidades por dominio (Marcial, Arcano, Fisico, etc.).",
            openapi_extra={"x-openai-isConsequential": False})
async def get_available_skills(personagem_id: int, dominio: str = "",
                               conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_habilidades_aprendiveis_disponiveis(%s, %s)", (personagem_id, dominio))
        result = await cur.fetchone()
    return result or {"habilidades": []}


@router.post("/milestone", operation_id="registerLifeMilestone", summary="Registrar marco de vida",
             description="Marco ANIMA: menor, significativo, maior ou unico.",
             openapi_extra={"x-openai-isConsequential": True})
async def register_milestone(payload: RegisterLifeMilestoneRequest,
                             conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_marco_vida(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.tipo, payload.gatilho,
                           payload.habilidade_afetada, payload.efeito, payload.sessao_id,
                           payload.tipo_unico, payload.aspecto_alterado, payload.delta_pressao))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "LIFE_MILESTONE",
                       {"tipo": payload.tipo, "gatilho": payload.gatilho},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "marco_registrado"}
