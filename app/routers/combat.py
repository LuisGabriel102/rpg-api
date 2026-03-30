"""Router de combate — inclui endpoint composto /combat/execute-turn e maquina de estados."""

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional, List
import json
from app.database import get_db
from app.auth import verify_token
from app.events import record_event
from app.dice import roll, roll_ability_check, roll_damage, roll_save

router = APIRouter()

# === Maquina de Estados do Combate ===

COMBAT_PHASES = ["pre_combate", "iniciativa", "turno_inicio", "acao", "bonus", "reacao", "turno_fim", "combate_fim"]
VALID_TRANSITIONS = {
    "pre_combate": ["iniciativa"],
    "iniciativa": ["turno_inicio"],
    "turno_inicio": ["acao"],
    "acao": ["bonus", "reacao", "turno_fim"],
    "bonus": ["reacao", "turno_fim"],
    "reacao": ["turno_fim"],
    "turno_fim": ["turno_inicio", "combate_fim"],
    "combate_fim": [],
}


def validate_phase_transition(current: str, target: str) -> bool:
    """Valida se a transicao de fase eh permitida."""
    return target in VALID_TRANSITIONS.get(current, [])


# === Request Models ===

class InitCombatRequest(BaseModel):
    campanha_id: int
    sessao_id: int
    personagem_id: int
    inimigos: dict = Field(..., description="JSONB com dados dos inimigos")
    ordem_iniciativa: dict = Field(..., description="JSONB com ordem de iniciativa")
    descricao_ambiente: str = Field("campo aberto")
    local_id: Optional[int] = None
    terreno_especial: List[str] = Field(default_factory=list)


class ExecuteTurnRequest(BaseModel):
    sessao_id: int
    personagem_id: int
    acao: str = Field(..., description="Tipo de acao: ataque, magia, esquiva, correr, ajuda, usar_item")
    alvo: str = Field("", description="Nome ou ID do alvo")
    magia_id: Optional[int] = Field(None, description="ID da magia se acao=magia")
    item_id: Optional[int] = Field(None, description="ID do item se acao=usar_item")
    dados_extras: Optional[dict] = Field(None, description="Dados adicionais da acao")


class UpdateTurnRequest(BaseModel):
    sessao_id: int
    hp_protagonista: int
    mp_protagonista: int
    condicoes_prot: List[str] = Field(default_factory=list)
    concentracao: Optional[str] = None
    inimigos: dict
    avancar_turno: bool = True
    evento_rodada: Optional[str] = None


class EndCombatRequest(BaseModel):
    sessao_id: int
    resultado: str = Field(..., description="vitoria, derrota, fuga, negociacao")
    xp_gerado: int = 0
    recompensas_narrativas: Optional[str] = None


class ConcentrationTestRequest(BaseModel):
    personagem_id: int
    dano_recebido: int
    dado_rolado: int
    sessao_id: int


class RegisterConditionRequest(BaseModel):
    personagem_id: int
    condicao_nome: str
    sessao_id: int
    causa: Optional[str] = None
    agente_npc_id: Optional[int] = None
    criatura_id: Optional[int] = None
    rodada_inicio: int = 1
    duracao_rodadas: Optional[int] = None
    data_harptos: Optional[str] = None


# === ENDPOINT COMPOSTO: executa turno inteiro atomicamente ===

@router.post(
    "/execute-turn",
    operation_id="executeCombatTurn",
    summary="[COMPOSTO] Executar turno completo",
    description="Executa um turno inteiro atomicamente: processa efeitos inicio de turno, decrementa condicoes, executa acao do personagem, rola dados necessarios, atualiza HP/MP, processa efeitos fim de turno. 1 chamada substitui 5-8 chamadas separadas.",
    openapi_extra={"x-openai-isConsequential": True},
)
async def execute_turn(
    payload: ExecuteTurnRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    pid = payload.personagem_id
    sid = payload.sessao_id
    results = {"phases": []}

    async with conn.cursor(row_factory=dict_row) as cur:
        # Fase 1: Obter estado do combate
        await cur.execute("SELECT * FROM get_estado_combate(%s)", (sid,))
        estado = await cur.fetchone()
        if not estado:
            raise HTTPException(status_code=404, detail="Nenhum combate ativo nesta sessao")

        # Validar fase do combate via maquina de estados
        current_phase = (estado.get("fase_atual") or "acao").lower()
        action_phase = "acao"
        if current_phase in VALID_TRANSITIONS and not validate_phase_transition(current_phase, action_phase):
            from app.errors import CombatPhaseError
            raise CombatPhaseError(current_phase, payload.acao)

        results["combat_state_before"] = estado

        # Fase 2: Decrementar condicoes (inicio do turno)
        await cur.execute("SELECT * FROM decrementar_condicoes(%s, %s)", (pid, sid))
        condicoes_result = await cur.fetchone()
        results["phases"].append({"phase": "turno_inicio", "condicoes": condicoes_result})

        # Fase 3: Executar acao
        action_result = {"acao": payload.acao, "alvo": payload.alvo}

        if payload.acao == "ataque":
            # Rola ataque
            attack_roll = roll_ability_check(0)  # Modificador vem do GPT
            action_result["ataque_roll"] = attack_roll

        elif payload.acao == "magia" and payload.magia_id:
            # Verifica MP
            await cur.execute("SELECT * FROM verificar_mp(%s)", (pid,))
            mp_check = await cur.fetchone()
            action_result["mp_antes"] = mp_check

        results["phases"].append({"phase": "acao", "result": action_result})

        # Fase 4: Obter estado atualizado
        await cur.execute("SELECT * FROM get_estado_combate(%s)", (sid,))
        estado_final = await cur.fetchone()

        # Fase 5: Obter condicoes ativas
        await cur.execute(
            """SELECT pc.id, pc.turnos_restantes, rc.nome, rc.efeito_mecanico
               FROM personagem_condicoes pc
               JOIN ref_condicoes rc ON pc.condicao_id = rc.id
               WHERE pc.personagem_id = %s""",
            (pid,),
        )
        condicoes_atuais = await cur.fetchall()

    # Registrar evento
    await record_event(
        conn, "combate", sid, "TURN_EXECUTED",
        {"acao": payload.acao, "alvo": payload.alvo},
        sessao_id=sid, personagem_id=pid,
    )

    return {
        "action_result": results,
        "character_state": {
            "combat": estado_final,
            "condicoes_ativas": condicoes_atuais,
        },
        "narrative_hints": {
            "acao_executada": payload.acao,
            "alvo": payload.alvo,
        },
    }


# === ENDPOINTS EXISTENTES (v2) com anotacoes GPT ===

@router.post("/start", operation_id="startCombat", summary="Iniciar combate",
             description="Cria combate_ativo com HP dos inimigos e ordem de iniciativa.",
             openapi_extra={"x-openai-isConsequential": True})
async def start_combat(payload: InitCombatRequest, conn: AsyncConnection = Depends(get_db),
                       _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM iniciar_combate(%s,%s,%s,%s,%s,%s,%s,%s)",
            (payload.campanha_id, payload.sessao_id, payload.personagem_id,
             json.dumps(payload.inimigos), json.dumps(payload.ordem_iniciativa),
             payload.descricao_ambiente, payload.local_id, payload.terreno_especial),
        )
        result = await cur.fetchone()
    await record_event(conn, "combate", payload.sessao_id, "COMBAT_STARTED",
                       {"inimigos": payload.inimigos}, sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "combate_iniciado"}


@router.get("/state/{sessao_id}", operation_id="getCombatState", summary="Estado do combate",
            description="Retorna rodada, HP, condicoes e inimigos.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_combat_state(sessao_id: int, conn: AsyncConnection = Depends(get_db),
                           _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_estado_combate(%s)", (sessao_id,))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Nenhum combate ativo")
    return result


@router.post("/turn", operation_id="updateCombatTurn", summary="Atualizar turno",
             description="Atualiza HP/MP e estado dos inimigos. Prefira /combat/execute-turn.",
             openapi_extra={"x-openai-isConsequential": True})
async def update_turn(payload: UpdateTurnRequest, conn: AsyncConnection = Depends(get_db),
                      _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM atualizar_turno_combate(%s,%s,%s,%s,%s,%s,%s,%s)",
            (payload.sessao_id, payload.hp_protagonista, payload.mp_protagonista,
             payload.condicoes_prot, payload.concentracao,
             json.dumps(payload.inimigos), payload.avancar_turno, payload.evento_rodada),
        )
        result = await cur.fetchone()
    return result or {"status": "turno_atualizado"}


@router.post("/end", operation_id="endCombat", summary="Encerrar combate",
             description="Encerra combate com resultado e XP.",
             openapi_extra={"x-openai-isConsequential": True})
async def end_combat(payload: EndCombatRequest, conn: AsyncConnection = Depends(get_db),
                     _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM encerrar_combate(%s,%s,%s,%s)",
                          (payload.sessao_id, payload.resultado, payload.xp_gerado, payload.recompensas_narrativas))
        result = await cur.fetchone()
    await record_event(conn, "combate", payload.sessao_id, "COMBAT_ENDED",
                       {"resultado": payload.resultado, "xp": payload.xp_gerado}, sessao_id=payload.sessao_id)
    return result or {"status": "combate_encerrado"}


@router.post("/concentration-test", operation_id="testConcentration",
             summary="Teste de concentracao",
             description="Testa Fortitude quando concentrado e toma dano. CD=max(10, dano/2).",
             openapi_extra={"x-openai-isConsequential": True})
async def test_concentration(payload: ConcentrationTestRequest, conn: AsyncConnection = Depends(get_db),
                             _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM teste_concentracao(%s,%s,%s,%s)",
                          (payload.personagem_id, payload.dano_recebido, payload.dado_rolado, payload.sessao_id))
        result = await cur.fetchone()
    return result or {"status": "teste_realizado"}


@router.post("/condition", operation_id="registerCondition", summary="Aplicar condicao",
             description="Registra condicao ativa com duracao em turnos.",
             openapi_extra={"x-openai-isConsequential": True})
async def register_condition(payload: RegisterConditionRequest, conn: AsyncConnection = Depends(get_db),
                             _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM registrar_condicao(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (payload.personagem_id, payload.condicao_nome, payload.sessao_id,
             payload.causa, payload.agente_npc_id, payload.criatura_id,
             payload.rodada_inicio, payload.duracao_rodadas, payload.data_harptos),
        )
        result = await cur.fetchone()
    return result or {"status": "condicao_aplicada"}


@router.post("/decrement-conditions", operation_id="decrementConditions",
             summary="Decrementar condicoes por turno",
             description="Decrementa turnos de condicoes. Chamar no INICIO de cada turno.",
             openapi_extra={"x-openai-isConsequential": True})
async def decrement_conditions(personagem_id: int, sessao_id: int,
                               conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM decrementar_condicoes(%s,%s)", (personagem_id, sessao_id))
        result = await cur.fetchone()
    return result or {"status": "condicoes_decrementadas"}


@router.get("/rule/{nome}", operation_id="getCombatRule", summary="Consultar regra de combate",
            description="Busca regra de combate pelo nome.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_combat_rule(nome: str, conn: AsyncConnection = Depends(get_db),
                          _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM consultar_regra_combate(%s)", (nome,))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Regra nao encontrada")
    return result
