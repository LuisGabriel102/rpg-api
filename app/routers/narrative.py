"""Router de narrativa (diario, conquistas, decisoes, bestiario, reputacoes) — v3."""

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional, List
import json
from app.database import get_db
from app.auth import verify_token
from app.events import record_event

router = APIRouter()


class DiaryEntryRequest(BaseModel):
    personagem_id: int
    sessao_id: int
    texto: str
    titulo: str = ""
    humor: str = "neutro"
    temas: List[str] = []
    pressao_delta: int = 0
    data_harptos: Optional[str] = None


class AchievementRequest(BaseModel):
    personagem_id: int
    titulo: str
    descricao: str
    categoria: str = "combate"
    dificuldade: str = "normal"
    sessao_id: int
    local_id: Optional[int] = None
    npc_testemunha: Optional[int] = None
    reconhecida: bool = True
    fama_ganho: int = 0
    bonus_permanente: Optional[dict] = None
    data_harptos: Optional[str] = None


class MoralDecisionRequest(BaseModel):
    personagem_id: int
    titulo: str
    situacao: str
    opcao_escolhida: str
    alinhamento_indicado: str = "neutro"
    peso_moral: int = Field(1, ge=1, le=5)
    sessao_id: int
    afeta_npc_id: Optional[int] = None
    delta_confianca: int = 0
    afeta_faccao_id: Optional[int] = None
    delta_reputacao: int = 0
    pressao_delta: int = 0
    irreversivel: bool = False
    gera_traco: bool = False
    traco_texto: Optional[str] = None
    data_harptos: Optional[str] = None


# === DIARIO ===

@router.get("/diary/{personagem_id}", operation_id="getDiary", summary="Diario do personagem",
            description="Entradas do diario. Filtre por humor ou limite.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_diary(personagem_id: int, limite: int = 10, humor: str = "",
                    conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_diario_personagem(%s, %s, %s)", (personagem_id, limite, humor))
        result = await cur.fetchone()
    return result or {"entradas": []}


@router.post("/diary", operation_id="writeDiary", summary="Escrever no diario",
             description="Registra entrada com titulo, humor e temas.",
             openapi_extra={"x-openai-isConsequential": True})
async def write_diary(payload: DiaryEntryRequest, conn: AsyncConnection = Depends(get_db),
                      _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_entrada_diario(%s,%s,%s,%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.sessao_id, payload.texto,
                           payload.titulo, payload.humor, payload.temas,
                           payload.pressao_delta, payload.data_harptos))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "DIARY_ENTRY",
                       {"titulo": payload.titulo, "humor": payload.humor},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "entrada_registrada"}


# === CONQUISTAS ===

@router.get("/achievements/{personagem_id}", operation_id="getAchievements", summary="Conquistas",
            description="Conquistas desbloqueadas. Filtre por categoria ou dificuldade.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_achievements(personagem_id: int, categoria: str = "", dificuldade: str = "",
                           conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_conquistas_personagem(%s, %s, %s)",
                          (personagem_id, categoria, dificuldade))
        result = await cur.fetchone()
    return result or {"conquistas": []}


@router.post("/achievement", operation_id="registerAchievement", summary="Registrar conquista",
             description="Registra achievement com categoria, dificuldade e bonus.",
             openapi_extra={"x-openai-isConsequential": True})
async def register_achievement(payload: AchievementRequest, conn: AsyncConnection = Depends(get_db),
                               _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_conquista(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.titulo, payload.descricao,
                           payload.categoria, payload.dificuldade, payload.sessao_id,
                           payload.local_id, payload.npc_testemunha, payload.reconhecida,
                           payload.fama_ganho,
                           json.dumps(payload.bonus_permanente) if payload.bonus_permanente else None,
                           payload.data_harptos))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "ACHIEVEMENT_UNLOCKED",
                       {"titulo": payload.titulo, "categoria": payload.categoria},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "conquista_registrada"}


# === DECISOES MORAIS ===

@router.post("/moral-decision", operation_id="registerMoralDecision", summary="Registrar decisao moral",
             description="Escolha moral com impacto em alinhamento, NPCs, faccoes e pressao.",
             openapi_extra={"x-openai-isConsequential": True})
async def register_moral_decision(payload: MoralDecisionRequest, conn: AsyncConnection = Depends(get_db),
                                  _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM registrar_decisao_moral(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                          (payload.personagem_id, payload.titulo, payload.situacao,
                           payload.opcao_escolhida, payload.alinhamento_indicado,
                           payload.peso_moral, payload.sessao_id, payload.afeta_npc_id,
                           payload.delta_confianca, payload.afeta_faccao_id,
                           payload.delta_reputacao, payload.pressao_delta,
                           payload.irreversivel, payload.gera_traco,
                           payload.traco_texto, payload.data_harptos))
        result = await cur.fetchone()
    await record_event(conn, "personagem", payload.personagem_id, "MORAL_DECISION",
                       {"titulo": payload.titulo, "alinhamento": payload.alinhamento_indicado, "irreversivel": payload.irreversivel},
                       sessao_id=payload.sessao_id, personagem_id=payload.personagem_id)
    return result or {"status": "decisao_registrada"}


# === BESTIARIO, REPUTACOES, OBJETIVOS, WORLD FACTS, MISSOES, INATAS, ANIMA ===

@router.get("/bestiary/{personagem_id}", operation_id="getPersonalBestiary", summary="Bestiario pessoal",
            description="Criaturas encontradas com notas sobre fraquezas.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_personal_bestiary(personagem_id: int, nivel_perigo: str = "",
                                conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_bestiario_personagem(%s, %s)", (personagem_id, nivel_perigo))
        result = await cur.fetchone()
    return result or {"criaturas_encontradas": []}


@router.get("/reputations/{personagem_id}", operation_id="getReputations", summary="Reputacoes",
            description="Reputacao com todas as faccoes.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_reputations(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                          _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_reputacoes_personagem(%s)", (personagem_id,))
        result = await cur.fetchone()
    return result or {"reputacoes": []}


@router.get("/objectives/{personagem_id}", operation_id="getPersonalObjectives", summary="Objetivos pessoais",
            description="Objetivos ativos ou concluidos.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_objectives(personagem_id: int, apenas_ativos: bool = True,
                         conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_objetivos_pessoais(%s, %s)", (personagem_id, apenas_ativos))
        result = await cur.fetchone()
    return result or {"objetivos": []}


@router.get("/world-facts/{campanha_id}", operation_id="getWorldFacts", summary="World facts",
            description="Memoria persistente entre sessoes (tracos, pressao, segredos, vinculos).",
            openapi_extra={"x-openai-isConsequential": False})
async def get_world_facts(campanha_id: int, tipo: Optional[str] = Query(None), limite: int = 50,
                          conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    conditions = ["campanha_id = %s", "ativo = true"]
    params = [campanha_id]
    if tipo:
        conditions.append("tipo = %s"); params.append(tipo)
    where = "WHERE " + " AND ".join(conditions)
    params.append(limite)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(f"SELECT * FROM world_facts {where} ORDER BY criado_em DESC LIMIT %s", params)
        facts = await cur.fetchall()
    return {"total": len(facts), "facts": facts}


@router.get("/missions/{campanha_id}", operation_id="getActiveMissions", summary="Missoes ativas",
            description="Missoes ativas com objetivos e recompensas.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_active_missions(campanha_id: int, conn: AsyncConnection = Depends(get_db),
                              _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """SELECT m.*,
                      (SELECT json_agg(row_to_json(o)) FROM missao_objetivos o WHERE o.missao_id = m.id) as objetivos,
                      (SELECT json_agg(row_to_json(r)) FROM missao_recompensas r WHERE r.missao_id = m.id) as recompensas
               FROM missoes m WHERE m.campanha_id = %s AND m.status = 'ativa' ORDER BY m.criado_em DESC""",
            (campanha_id,))
        missoes = await cur.fetchall()
    return {"total": len(missoes), "missoes": missoes}


@router.get("/innate-abilities/{personagem_id}", operation_id="getInnateAbilities",
            summary="Habilidades inatas",
            description="Habilidades de estrela, raca e talentos.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_innate_abilities(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                               _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM personagem_habilidades_innatas WHERE personagem_id = %s ORDER BY nivel_obtido",
                          (personagem_id,))
        habilidades = await cur.fetchall()
    return {"personagem_id": personagem_id, "total": len(habilidades), "habilidades": habilidades}


@router.get("/anima-progress/{personagem_id}", operation_id="getAnimaProgress", summary="Progresso ANIMA",
            description="Progresso de habilidades ANIMA com grau e pontos.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_anima_progress(personagem_id: int, conn: AsyncConnection = Depends(get_db),
                             _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM anima_habilidades_progresso WHERE personagem_id = %s ORDER BY grau_atual DESC, pontos_totais DESC",
            (personagem_id,))
        progresso = await cur.fetchall()
    return {"personagem_id": personagem_id, "total": len(progresso), "habilidades": progresso}
