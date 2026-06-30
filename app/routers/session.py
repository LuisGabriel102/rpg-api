"""Router de sessao — inclui endpoint composto /session/open que substitui 15 chamadas."""

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from typing import Optional, List
import json
import structlog
from app.database import get_db
from app.auth import verify_token
from app.events import record_event

router = APIRouter()


class StartSessionRequest(BaseModel):
    campanha_id: int = Field(..., description="ID da campanha")
    personagem_id: int = Field(..., description="ID do personagem")


class EndSessionRequest(BaseModel):
    sessao_id: int = Field(..., description="ID da sessao ativa")
    resumo: str = Field(..., description="Resumo narrativo da sessao")


class SessionSummaryRequest(BaseModel):
    sessao_id: int
    personagem_id: int
    campanha_id: int
    titulo: str
    resumo_curto: str
    resumo_completo: str
    combates: List[str] = []
    decisoes: List[str] = []
    relacoes: List[str] = []
    xp_ganho: int = 0
    ouro_ganho: int = 0
    ouro_gasto: int = 0
    itens: List[str] = []
    hp_final: int = 0
    mp_final: int = 0
    nivel: int = 1
    frase_sessao: str = ""
    pergunta_aberta: str = ""
    continuidade_gpt: str = ""


class OpenSessionRequest(BaseModel):
    campanha_id: int = Field(..., description="ID da campanha")
    personagem_id: int = Field(..., description="ID do personagem")
    regiao: str = Field("", description="Regiao atual para contexto enriquecido")


class CacheGptRequest(BaseModel):
    sessao_id: int
    chave: str
    valor: dict
    tipo: str = "geral"
    expira_rodada: Optional[int] = None


# === ENDPOINT COMPOSTO: substitui 15 chamadas do protocolo de abertura ===

@router.post(
    "/open",
    operation_id="openSession",
    summary="[COMPOSTO] Abrir sessao com todo o contexto",
    description="Inicia sessao E retorna TUDO que o GPT precisa em 1 chamada: ficha, inventario, condicoes, aliados, maestrias, contexto do mundo, missoes, cache, regras, habilidades inatas, ANIMA, world facts, sessao anterior e tecnicas. Substitui as 15 chamadas do protocolo antigo.",
    openapi_extra={"x-openai-isConsequential": True},
)
async def open_session(
    payload: OpenSessionRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    pid = payload.personagem_id
    cid = payload.campanha_id

    async with conn.cursor(row_factory=dict_row) as cur:
        # 1. Iniciar sessao (OBRIGATORIO — se falhar, aborta)
        await cur.execute('SELECT * FROM "iniciarSessao"(%s, %s)', (cid, pid))
        sessao = await cur.fetchone()
        if not sessao:
            raise HTTPException(status_code=500, detail="Falha ao iniciar sessao")

        # 2. Ficha completa (OBRIGATORIA — se falhar, aborta)
        await cur.execute('SELECT * FROM "fichaPersonagem"(%s)', (pid,))
        ficha = await cur.fetchone()
        if not ficha:
            raise HTTPException(status_code=404, detail="Personagem nao encontrado")

        # Queries 3-15: degradacao graceful — se uma falhar, retorna vazio
        # Cada query usa cursor proprio para isolamento de erros
        _log = structlog.get_logger()

        async def safe_query(query, params, fallback=None):
            try:
                async with conn.cursor(row_factory=dict_row) as c:
                    await c.execute(query, params)
                    return await c.fetchone()
            except Exception as e:
                _log.warning("safe_query_failed", query=query[:80], error=str(e)[:200])
                return fallback if fallback is not None else {}

        async def safe_query_all(query, params):
            try:
                async with conn.cursor(row_factory=dict_row) as c:
                    await c.execute(query, params)
                    return await c.fetchall()
            except Exception as e:
                _log.warning("safe_query_all_failed", query=query[:80], error=str(e)[:200])
                return []

        # 3. Verificar MP
        mana = await safe_query("SELECT * FROM verificar_mp(%s)", (pid,))

        # 4. Condicoes ativas
        condicoes = await safe_query_all(
            """SELECT pc.id, pc.turnos_restantes, pc.fonte_condicao, rc.nome, rc.efeito_mecanico
               FROM personagem_condicoes pc
               JOIN ref_condicoes rc ON pc.condicao_id = rc.id
               WHERE pc.personagem_id = %s""", (pid,))

        # 5. Recursos especiais
        recursos = await safe_query("SELECT * FROM get_recursos_disponiveis(%s)", (pid,))

        # 6. Aliados ativos
        aliados = await safe_query("SELECT * FROM get_aliados_ativos(%s, %s)", (pid, 0))

        # 7. Maestrias
        maestrias = await safe_query("SELECT * FROM listar_maestrias_personagem(%s)", (pid,))

        # 8. Contexto do mundo
        mundo = await safe_query("SELECT * FROM get_contexto_mundo(%s, %s)", (cid, pid))

        # 9. Missoes ativas
        missoes = await safe_query_all(
            """SELECT m.*, (SELECT json_agg(row_to_json(o)) FROM missao_objetivos o WHERE o.missao_id = m.id) as objetivos
               FROM missoes m WHERE m.campanha_id = %s AND m.status = 'ativa' ORDER BY m.criado_em DESC""", (cid,))

        # 10. Sessao anterior
        sessao_anterior = await safe_query('SELECT * FROM "historicoSessoes"(%s, %s)', (cid, 1))

        # 11. Habilidades inatas
        inatas = await safe_query_all(
            "SELECT * FROM personagem_habilidades_innatas WHERE personagem_id = %s ORDER BY nivel_obtido", (pid,))

        # 12. Progresso ANIMA
        anima = await safe_query_all(
            "SELECT * FROM anima_habilidades_progresso WHERE personagem_id = %s ORDER BY grau_atual DESC", (pid,))

        # 13. World facts
        facts = await safe_query_all(
            "SELECT * FROM world_facts WHERE campanha_id = %s AND ativo = true ORDER BY criado_em DESC LIMIT 30", (cid,))

        # 14. Contexto enriquecido
        contexto_enriquecido = await safe_query(
            "SELECT * FROM get_contexto_enriquecido(%s, %s, %s)", (cid, pid, payload.regiao))

        # 15. Tecnicas do personagem
        tecnicas = await safe_query("SELECT * FROM get_tecnicas_personagem(%s)", (pid,))

    # Registra evento de abertura
    await record_event(
        conn, "sessao", sessao.get("id", 0) if sessao else 0,
        "SESSION_OPENED", {"campanha_id": cid, "personagem_id": pid},
        personagem_id=pid,
    )

    return {
        "sessao": sessao,
        "ficha": ficha,
        "mana": mana,
        "condicoes": {"total": len(condicoes), "lista": condicoes},
        "recursos": recursos,
        "aliados": aliados,
        "maestrias": maestrias,
        "mundo": mundo,
        "missoes": {"total": len(missoes), "lista": missoes},
        "sessao_anterior": sessao_anterior,
        "habilidades_inatas": {"total": len(inatas), "lista": inatas},
        "anima_progresso": {"total": len(anima), "lista": anima},
        "world_facts": {"total": len(facts), "lista": facts},
        "contexto_enriquecido": contexto_enriquecido,
        "tecnicas": tecnicas,
    }


# === ENDPOINTS EXISTENTES (v2) ===

@router.post(
    "/start",
    operation_id="startSession",
    summary="Iniciar sessao simples",
    description="Cria sessao sem carregar contexto. Prefira /session/open que faz tudo em 1 chamada.",
    openapi_extra={"x-openai-isConsequential": True},
)
async def start_session(
    payload: StartSessionRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute('SELECT * FROM "iniciarSessao"(%s, %s)', (payload.campanha_id, payload.personagem_id))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=500, detail="Falha ao iniciar sessao")
    return result


@router.post(
    "/end",
    operation_id="endSession",
    summary="Encerrar sessao",
    description="Encerra a sessao ativa com resumo narrativo.",
    openapi_extra={"x-openai-isConsequential": True},
)
async def end_session(
    payload: EndSessionRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute('SELECT * FROM "encerrarSessao"(%s, %s)', (payload.sessao_id, payload.resumo))
        result = await cur.fetchone()
    if not result:
        raise HTTPException(status_code=500, detail="Falha ao encerrar sessao")

    await record_event(conn, "sessao", payload.sessao_id, "SESSION_CLOSED", {"resumo": payload.resumo[:200]})
    return result


@router.post(
    "/summary",
    operation_id="registerSessionSummary",
    summary="Registrar resumo da sessao",
    description="Registra resumo detalhado com combates, decisoes, XP, ouro e itens.",
    openapi_extra={"x-openai-isConsequential": True},
)
async def register_summary(
    payload: SessionSummaryRequest,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM registrar_resumo_sessao(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                payload.sessao_id, payload.personagem_id, payload.campanha_id,
                payload.titulo, payload.resumo_curto, payload.resumo_completo,
                payload.combates, payload.decisoes, payload.relacoes,
                payload.xp_ganho, payload.ouro_ganho, payload.ouro_gasto,
                payload.itens, payload.hp_final, payload.mp_final,
                payload.nivel, payload.frase_sessao, payload.pergunta_aberta,
                payload.continuidade_gpt,
            ),
        )
        result = await cur.fetchone()
    return result or {"status": "resumo_registrado"}


@router.get(
    "/history/{campanha_id}",
    operation_id="getSessionHistory",
    summary="Historico de sessoes",
    description="Retorna ultimas sessoes da campanha com resumos.",
    openapi_extra={"x-openai-isConsequential": False},
)
async def get_history(
    campanha_id: int,
    quantidade: int = 5,
    conn: AsyncConnection = Depends(get_db),
    _token: str = Depends(verify_token),
):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute('SELECT * FROM "historicoSessoes"(%s, %s)', (campanha_id, quantidade))
        result = await cur.fetchone()
    return result or {"sessoes": []}


@router.get("/cache/{sessao_id}", operation_id="getGptCache", summary="Ler cache GPT",
            description="Retorna dados cacheados da sessao.",
            openapi_extra={"x-openai-isConsequential": False})
async def get_cache(sessao_id: int, chave: str = "", tipo: str = "",
                    conn: AsyncConnection = Depends(get_db), _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM get_cache_gpt(%s, %s, %s)", (sessao_id, chave, tipo))
        result = await cur.fetchone()
    return result or {}


@router.post("/cache", operation_id="setGptCache", summary="Salvar no cache GPT",
             description="Salva dados temporarios da sessao.",
             openapi_extra={"x-openai-isConsequential": False})
async def set_cache(payload: CacheGptRequest, conn: AsyncConnection = Depends(get_db),
                    _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM set_cache_gpt(%s, %s, %s::jsonb, %s, %s)",
            (payload.sessao_id, payload.chave, json.dumps(payload.valor), payload.tipo, payload.expira_rodada),
        )
        result = await cur.fetchone()
    return result or {"status": "cache_salvo"}


@router.delete("/cache/{sessao_id}", operation_id="clearGptCache", summary="Limpar cache GPT",
               description="Limpa todo o cache da sessao.",
               openapi_extra={"x-openai-isConsequential": False})
async def clear_cache(sessao_id: int, conn: AsyncConnection = Depends(get_db),
                      _token: str = Depends(verify_token)):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM limpar_cache_gpt(%s)", (sessao_id,))
        result = await cur.fetchone()
    return result or {"status": "cache_limpo"}
