"""Router de personagem com event sourcing e anotacoes GPT."""

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.auth import verify_token
from app.events import record_event

router = APIRouter()


class UpdateHpRequest(BaseModel):
    personagem_id: int
    delta: int = Field(..., description="Positivo=curar, negativo=dano")
    causa: str = Field(..., description="Ex: 'dano de fogo do goblin'")
    sessao_id: int


class SpendMpRequest(BaseModel):
    personagem_id: int
    custo: int = Field(..., gt=0)
    descricao: str
    sessao_id: int


class RegisterXpRequest(BaseModel):
    personagem_id: int
    xp_ganho: int = Field(..., gt=0)
    fonte: str = Field(..., description="combate, missao, roleplay, descoberta")
    descricao: str
    sessao_id: int
    criatura_id: Optional[int] = None
    missao_id: Optional[int] = None
    data_harptos: Optional[str] = None


class LevelUpRequest(BaseModel):
    personagem_id: int
    dado_vida: int
    sessao_id: int


@router.get("/{personagem_id}", operation_id="getCharacterSheet",
            summary="Ficha completa do personagem",
            description="Retorna TODOS os dados via fichaPersonagem(): atributos, HP, CA, nivel, XP, moedas.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_character(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                        _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute('SELECT * FROM "fichaPersonagem"(%s)', (personagem_id,))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Personagem nao encontrado")
    return result


@router.get("/{personagem_id}/mana", operation_id="checkMana", summary="Verificar MP",
            description="MP atual, maximo e slots usados.",
            openapi_extra={"x-openai-isConsequential": False})
async def check_mana(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                     _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM verificar_mp(%s)", (personagem_id,))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Dados de mana nao encontrados")
    return result


@router.get("/{personagem_id}/saves", operation_id="getHybridSaves", summary="Saves hibridos",
            description="Fortitude, Reflexos e Vontade do Sistema Nexus.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_saves(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                    _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM personagem_saves_hibridos WHERE personagem_id = %s", (personagem_id,))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Saves nao encontrados")
    return result


@router.get("/{personagem_id}/conditions", operation_id="getActiveConditions",
            summary="Condicoes ativas",
            description="Condicoes com turnos restantes (envenenado, atordoado, etc.).",
            openapi_extra={"x-openai-isConsequential": False})
async def get_conditions(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                         _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """SELECT pc.id, pc.turnos_restantes, pc.fonte_condicao, pc.save_remocao,
                      pc.cd_remocao, pc.notas, rc.nome, rc.efeito_mecanico
               FROM personagem_condicoes pc JOIN ref_condicoes rc ON pc.condicao_id = rc.id
               WHERE pc.personagem_id = %s""", (personagem_id,))
        condicoes = await cur.fetchall()
    return {"personagem_id": personagem_id, "total": len(condicoes), "condicoes": condicoes}


@router.get("/{personagem_id}/resources", operation_id="getSpecialResources",
            summary="Recursos especiais",
            description="Action Surge, Wild Shape, Ki Points e usos restantes.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_resources(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                        _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_recursos_disponiveis(%s)", (personagem_id,))
        result = await cur.fetchone()
    return result or {"recursos": []}


@router.get("/{personagem_id}/allies", operation_id="getActiveAllies", summary="Aliados ativos",
            description="Companheiros acompanhando o personagem.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_allies(personagem_id: int, sessao_id: int = 0,
                     conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_aliados_ativos(%s, %s)", (personagem_id, sessao_id))
        result = await cur.fetchone()
    return result or {"aliados": []}


@router.post("/hp", operation_id="updateHp", summary="Atualizar HP",
             description="Dano (delta negativo) ou cura (delta positivo). Gerencia HP 0 automaticamente.",
             openapi_extra={"x-openai-isConsequential": True})
async def update_hp(payload: UpdateHpRequest, conn: AsyncConnection = Depends(get_db),
                    _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute('SELECT * FROM "atualizarHp"(%s,%s,%s,%s)',
                          (payload.personagem_id, payload.delta, payload.causa, payload.sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id,
                       "HP_CHANGED", {"delta": payload.delta, "causa": payload.causa},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "hp_atualizado"}


@router.post("/mp/spend", operation_id="spendMana", summary="Gastar MP",
             description="Gasta MP para magia ou tecnica. Valida MP suficiente.",
             openapi_extra={"x-openai-isConsequential": True})
async def spend_mp(payload: SpendMpRequest, conn: AsyncConnection = Depends(get_db),
                   _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM gastar_mp(%s,%s,%s,%s)",
                          (payload.personagem_id, payload.custo, payload.descricao, payload.sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id,
                       "MP_SPENT", {"custo": payload.custo, "descricao": payload.descricao},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "mp_gasto"}


@router.post("/xp", operation_id="registerXp", summary="Registrar XP",
             description="Registra XP ganho. Verifica proximo nivel automaticamente.",
             openapi_extra={"x-openai-isConsequential": True})
async def register_xp(payload: RegisterXpRequest, conn: AsyncConnection = Depends(get_db),
                      _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_xp(%s,%s,%s,%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.xp_ganho, payload.fonte,
                           payload.descricao, payload.sessao_id, payload.criatura_id,
                           payload.missao_id, payload.data_harptos))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id,
                       "XP_GAINED", {"xp": payload.xp_ganho, "fonte": payload.fonte},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "xp_registrado"}


@router.post("/level-up", operation_id="levelUp", summary="Subir de nivel",
             description="Level up: novo HP, saves, habilidades desbloqueadas.",
             openapi_extra={"x-openai-isConsequential": True})
async def level_up(payload: LevelUpRequest, conn: AsyncConnection = Depends(get_db),
                   _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute('SELECT * FROM "levelUp"(%s,%s,%s)',
                          (payload.personagem_id, payload.dado_vida, payload.sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id,
                       "LEVEL_UP", {"dado_vida": payload.dado_vida},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "level_up_concluido"}


@router.post("/rest", operation_id="rest", summary="Descanso curto ou longo",
             description="Tipo: 'descanso_curto' ou 'descanso_longo'.",
             openapi_extra={"x-openai-isConsequential": True})
async def rest(personagem_id: int, tipo_descanso: str, sessao_id: int,
               conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM recuperar_recursos(%s,%s,%s)", (personagem_id, tipo_descanso, sessao_id))
        result = await cur.fetchone()
    await record_event(conn, "personagem", personagem_id, "REST",
                       {"tipo": tipo_descanso}, sessao_id=sessao_id, personagem_id=personagem_id)
    return result or {"status": "recursos_recuperados"}


@router.get("/{personagem_id}/gold", operation_id="getGold", summary="Saldo de moedas",
            description="Ouro, prata, cobre e platina.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_gold(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                   _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_saldo_personagem(%s)", (personagem_id,))
        result = await cur.fetchone()
    return result or {}


@router.get("/{personagem_id}/class-sheet", operation_id="getClassSheet",
            summary="Ficha de classe completa",
            description="Vocacao, caminho, habilidades desbloqueadas.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_class_sheet(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                          _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_ficha_classe_completa(%s)", (personagem_id,))
        result = await cur.fetchone()
    return result or {}


@router.get("/{personagem_id}/actions", operation_id="getAllAvailableActions",
            summary="Tudo que pode fazer",
            description="Lista completa: ataques, magias, tecnicas, habilidades, itens.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_all_actions(personagem_id: int, tipo: str = "", contexto: str = "",
                          conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_tudo_que_personagem_pode_fazer(%s,%s,%s)",
                          (personagem_id, tipo, contexto))
        result = await cur.fetchone()
    return result or {}


@router.get("/{personagem_id}/enriched-context/{campanha_id}", operation_id="getEnrichedContext",
            summary="Contexto enriquecido para GPT",
            description="Contexto completo do personagem na campanha.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_enriched_context(personagem_id: int, campanha_id: int, regiao: str = "",
                               conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_contexto_enriquecido(%s,%s,%s)", (campanha_id, personagem_id, regiao))
        result = await cur.fetchone()
    return result or {}
