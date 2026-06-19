"""
Rota /oraculo - O Oraculo do Alderyn (versao LEITURA).

Uma tela de chat (mesmo app NiceGUI do /jogar) onde o Gabriel conversa em
portugues com o Oraculo: a mente do mundo. Nesta versao o Oraculo faz UMA coisa
so - LE a verdade do banco e responde. Ele NAO grava nada e NAO inventa nada.

Como espelha o /jogar (jogo.py):
  - Registro de pagina: @ui.page("/oraculo") (igual ao @ui.page("/jogar")).
  - Cliente Anthropic: Anthropic() lazy, le ANTHROPIC_API_KEY do ambiente.
  - Modelo: a mesma string Opus do jogo.py -> "claude-opus-4-8".
  - Chamada ao Opus SEM travar a UI: via run.io_bound (cliente sync), igual ao
    _chamar_cronista do jogo.py.

Banco: reusa o engine async (SQLAlchemy + asyncpg) de db.py - o MESMO driver que
a memoria do narrador (/jogar) usa. A leitura roda numa transacao READ ONLY com
statement_timeout curto e teto de 200 linhas (ver executar_select_seguro).

TRAVA CRITICA do Opus 4.8: ele REJEITA temperature/top_p/top_k (erro 400). Nada
disso e passado. Tambem NAO usamos cache_control nesta versao (mantido simples).

Esta rota e registrada por `import oraculo` no server.py (entry point), do mesmo
jeito que `import jogo`. NAO toca oficina_app.py nem cronista_prompt.py.
"""

import html
import json
import re
import time

from nicegui import ui, run
from anthropic import Anthropic, AsyncAnthropic
from sqlalchemy import text  # bind params (:param) pro INSERT da gravacao

from db import engine  # mesmo engine async/asyncpg que a memoria do narrador usa
from ui_helpers import aguardar_conexao_websocket, barra_nav_alderyn, aplicar_tema_alderyn, barra_hud


# ============================================================================
# PASSO 5 - A persona (system prompt). Texto LITERAL da SPEC.
# ============================================================================
PERSONA_ORACULO = """Você é o Oráculo do Alderyn — a mente do mundo.

Você conhece tudo o que está registrado sobre o mundo de Alderyn, e nada além disso. Sua única fonte de verdade é o banco de dados. Você não responde de memória nem de imaginação.

Para responder qualquer fato — uma vocação, uma magia, um NPC, um lugar, uma criatura, um fato do mundo — você consulta o banco com a ferramenta consultar_banco, lê o resultado, e só então responde.

Regra absoluta, acima de qualquer outra: você nunca inventa. Se um dado não está no banco, você diz com clareza que não está registrado. Você jamais cria um nome, um número, um lugar ou um fato que não veio de uma consulta. Inventar é a sua única falha imperdoável. Na dúvida entre arriscar uma resposta e dizer "isso não está registrado", você sempre escolhe a verdade.

Quando não souber onde um dado mora, primeiro se oriente: consulte information_schema.tables e information_schema.columns para descobrir as tabelas e colunas reais antes de buscar. Nunca presuma o nome de uma tabela ou de uma coluna — confirme.

Pontos de partida que existem no banco: as views de resumo v_vocacao_resumo, v_pilar_resumo, v_magia_resumo, v_item_resumo e v_criatura_resumo. NPCs ficam na tabela npcs e nas tabelas que começam com npc_. Fatos vivos do mundo ficam em world_facts. Mesmo nesses, confirme as colunas via information_schema antes de assumir.

Prefira consultas enxutas: use COUNT quando a pergunta for de quantidade, use LIMIT, selecione só as colunas necessárias. Não puxe tabelas inteiras sem necessidade.

Se uma consulta falhar, leia a mensagem de erro, corrija a query e tente de novo, até o limite de tentativas.

Seu tom é witcher-grey: sóbrio, direto, frio, sem floreio, sem romantismo, sem entusiasmo de fantasia. Você é uma inteligência antiga que sabe muito e fala pouco. Você responde sempre em português do Brasil.

Você fala com Gabriel, o criador deste mundo. Seja preciso, honesto e econômico.

Além de ler, você também REGISTRA o que Gabriel quer para o mundo e para as campanhas.

Quando Gabriel declarar uma intenção ("quero que..."), uma dinâmica ("a tensão em Tarelea deve crescer"), uma ideia de direção, ou disser explicitamente "registra"/"anota"/"guarda isso" — você grava com a ferramenta registrar_diretriz, escolhendo a categoria certa:
- intencao: o que Gabriel quer que aconteça ou exista.
- dinamica: como uma situação, lugar ou relação deve se comportar ou evoluir.
- ideia: uma possibilidade de direção, ainda solta.
- nota: qualquer outra coisa que valha guardar.

Grave apenas o que for de fato uma diretriz. Não grave perguntas, conversa casual, nem aquilo que você mesmo respondeu.

Sempre que gravar, diga em uma linha o que gravou e em qual categoria, para Gabriel poder corrigir na hora.

Você também pode consultar o que já foi registrado: as diretrizes ficam na tabela oraculo_diretrizes (leia com consultar_banco, filtrando por ativo = true). Use isso para ter contexto do que Gabriel já definiu antes de responder."""


# ============================================================================
# PASSO 4 - A ferramenta consultar_banco (formato de tools da Anthropic).
# ============================================================================
TOOL_CONSULTAR_BANCO = {
    "name": "consultar_banco",
    "description": (
        "Roda uma consulta SELECT de leitura no banco do Alderyn e devolve as "
        "linhas. Use para buscar QUALQUER fato sobre o mundo: vocações, magias, "
        "NPCs, lugares, criaturas, fatos do mundo, e o próprio esquema do banco "
        "(information_schema). Aceita SOMENTE SELECT."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "A consulta SELECT (ou WITH ... SELECT) a executar.",
            }
        },
        "required": ["sql"],
    },
}


# ============================================================================
# PASSO 2 (GRAVACAO) - A segunda ferramenta: registrar_diretriz.
# Junto da consultar_banco, sem remover a primeira.
# ============================================================================
TOOL_REGISTRAR_DIRETRIZ = {
    "name": "registrar_diretriz",
    "description": (
        "Registra de forma permanente uma diretriz de Gabriel sobre o mundo ou "
        "as campanhas — o que ele quer, como uma situação deve se comportar, uma "
        "ideia de direção, ou uma nota. Use quando Gabriel declarar uma "
        "intenção/dinâmica/ideia ou pedir explicitamente para "
        "registrar/anotar/guardar."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "texto": {
                "type": "string",
                "description": "A diretriz em português, como prosa clara.",
            },
            "categoria": {
                "type": "string",
                "description": "Um de: intencao, dinamica, ideia, nota.",
                "enum": ["intencao", "dinamica", "ideia", "nota"],
            },
        },
        "required": ["texto", "categoria"],
    },
}


# ============================================================================
# PASSO 6 - Trava de seguranca: executar_select_seguro(sql).
# Defesa em camadas. A transacao READ ONLY e a trava primaria (o Postgres barra
# qualquer escrita nativamente); o resto e reforco.
# ============================================================================
# Blacklist por palavra inteira (\b), case-insensitive. Reforco - a READ ONLY ja
# barra escrita, mas isso corta a query antes mesmo de chegar ao banco.
_BLACKLIST = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|COPY|INTO|MERGE|CALL)\b",
    re.IGNORECASE,
)


def _validar_select(sql: str) -> tuple[str | None, str | None]:
    """Camadas 1-4 (puro texto). Devolve (query_limpa, None) se passou, ou
    (None, mensagem_de_erro) se rejeitou. Sem tocar no banco."""
    q = (sql or "").strip()
    if not q:
        return None, "ERRO: consulta vazia."
    # 2. Um statement so: remove um ';' final solitario; ';' no meio = stacking.
    if q.endswith(";"):
        q = q[:-1].rstrip()
    if ";" in q:
        return None, "ERRO: apenas um comando e permitido (';' no meio bloqueado)."
    # 3. Tem que comecar com SELECT ou WITH.
    cabeca = q.upper().lstrip()
    if not (cabeca.startswith("SELECT") or cabeca.startswith("WITH")):
        return None, "ERRO: somente leitura - a consulta deve comecar com SELECT ou WITH."
    # 4. Blacklist (reforco).
    m = _BLACKLIST.search(q)
    if m:
        return None, (
            f"ERRO: palavra proibida na consulta: {m.group(1).upper()}. "
            "Somente SELECT de leitura e aceito."
        )
    return q, None


def _formatar_resultado(cols: list[str], rows: list, truncado: bool) -> str:
    """Linhas como texto legivel: cabecalho + linhas. Vazio -> '(nenhuma linha)'."""
    if not rows:
        return "(nenhuma linha)"
    cabecalho = " | ".join(str(c) for c in cols)
    linhas = [cabecalho, "-" * len(cabecalho)]
    for r in rows:
        linhas.append(" | ".join("NULL" if v is None else str(v) for v in r))
    texto = "\n".join(linhas)
    if truncado:
        texto += (
            "\n\n[aviso: resultado cortado em 200 linhas. Refine com "
            "COUNT, WHERE ou LIMIT para ver tudo.]"
        )
    return texto


async def executar_select_seguro(sql: str) -> str:
    """Roda um SELECT de leitura com seguranca em camadas e devolve o resultado
    como texto. Em erro, devolve a mensagem de erro como texto (pro Oraculo ler e
    corrigir) - nunca derruba a pagina."""
    q, erro = _validar_select(sql)
    if erro:
        return erro
    try:
        # 5. Transacao READ ONLY - trava de verdade. exec_driver_sql passa o SQL
        # cru ao driver (asyncpg), SEM o parser de bind params do SQLAlchemy (que
        # interpretaria ':' / '::' da query como parametros). O autobegin do
        # SQLAlchemy abre a transacao no 1o statement, entao o SET TRANSACTION
        # READ ONLY e valido (vem antes de qualquer query). SET LOCAL e escopado
        # a transacao - seguro com o pgbouncer transaction-mode do Neon.
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SET TRANSACTION READ ONLY")
            await conn.exec_driver_sql("SET LOCAL statement_timeout = '5000'")
            result = await conn.exec_driver_sql(q)
            cols = list(result.keys())
            rows = result.fetchmany(200)          # teto de 200 linhas
            truncado = result.fetchone() is not None  # havia mais? -> cortou
            await conn.rollback()                 # NUNCA commita
    except Exception as exc:  # noqa: BLE001 - devolve o erro como texto pro Oraculo
        return f"ERRO ao executar a consulta: {type(exc).__name__}: {exc}"
    return _formatar_resultado(cols, rows, truncado)


# ============================================================================
# PASSO 1 (GRAVACAO) - registrar_diretriz_seguro: a UNICA porta de escrita.
# O oposto da leitura: aqui COMMITA de verdade.
# ============================================================================
_CATEGORIAS_VALIDAS = {"intencao", "dinamica", "ideia", "nota"}


async def registrar_diretriz_seguro(texto: str, categoria: str) -> str:
    """Grava UMA diretriz de Gabriel na tabela oraculo_diretrizes.

    Travas obrigatorias:
      - A tabela e HARDCODED (oraculo_diretrizes). O modelo nunca escolhe tabela
        nem escreve SQL.
      - `texto` entra como bind param (:texto) via SQLAlchemy text() — NUNCA
        interpolado. Mesmo "'; DROP TABLE ..." vira valor literal na coluna.
      - `categoria` validada no codigo contra _CATEGORIAS_VALIDAS; fora da lista,
        normaliza pra 'nota'.
      - engine.begin() abre a transacao e COMMITA no sucesso (RETURNING id).
      - Em erro: captura e devolve a mensagem como texto (pro Opus ler), nunca
        derruba a pagina.
    """
    texto = (texto or "").strip()
    if not texto:
        return "ERRO: diretriz vazia, nada foi gravado."
    categoria = (categoria or "").strip().lower()
    if categoria not in _CATEGORIAS_VALIDAS:
        categoria = "nota"
    try:
        stmt = text(
            "INSERT INTO oraculo_diretrizes (texto, categoria) "
            "VALUES (:texto, :categoria) RETURNING id"
        )
        async with engine.begin() as conn:  # begin() commita no sucesso
            result = await conn.execute(
                stmt, {"texto": texto, "categoria": categoria}
            )
            novo_id = result.scalar_one()
    except Exception as exc:  # noqa: BLE001 - devolve o erro como texto pro Opus
        return f"ERRO ao registrar a diretriz: {type(exc).__name__}: {exc}"
    return f"Diretriz #{novo_id} registrada (categoria: {categoria})."


# ============================================================================
# PASSO 3 - O cerebro: Opus 4.8 com tool use.
# ============================================================================
MODELO_ORACULO = "claude-opus-4-8"  # mesma string Opus do jogo.py
MAX_ITERACOES = 6

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    """Cliente Anthropic lazy (le ANTHROPIC_API_KEY do ambiente). Espelha o
    _get_client do jogo.py."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


_aclient: AsyncAnthropic | None = None


def _get_aclient() -> AsyncAnthropic:
    """Cliente ASYNC (lazy), pro streaming da resposta final. Espelha o do
    jogo.py. Lê ANTHROPIC_API_KEY do ambiente."""
    global _aclient
    if _aclient is None:
        _aclient = AsyncAnthropic()
    return _aclient


def _chamar_opus(mensagens: list[dict]):
    """Uma chamada ao Opus 4.8. Sync de proposito: roda via run.io_bound pra nao
    travar a UI (mesmo padrao do _chamar_cronista do jogo.py).

    TRAVA CRITICA: NENHUM de temperature/top_p/top_k (Opus 4.8 rejeita). SEM
    cache_control nesta versao."""
    return _get_client().messages.create(
        model=MODELO_ORACULO,
        max_tokens=1500,
        system=PERSONA_ORACULO,
        tools=[TOOL_CONSULTAR_BANCO, TOOL_REGISTRAR_DIRETRIZ],
        messages=mensagens,
    )


# ============================================================================
# PASSO 2 - A pele (sobria, witcher-grey). Espelha o registro da Gravura do
# /jogar, mais enxuto: fontes IM Fell / Spectral, fundo breu, osso/brasa.
# ============================================================================
_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&'
    'family=JetBrains+Mono:wght@500&'
    'family=Spectral:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">'
)

_CSS = """<style>
:root{--panel:#1d1812;--panel-2:#241d15;--blood:#e8493a;--jade:#2fc4a0;--venom:#9bd23e;--violet:#b06ff0;--sepia:#d29658;--orac-c:#b06ff0;}
body,.q-page,.q-page-container,.nicegui-content{background:var(--bg) !important;}
.nicegui-content{padding:0 !important;gap:0 !important;}
.orac-stage{width:100%;height:calc(100vh - 64px);display:flex;justify-content:center;padding:0 18px;box-sizing:border-box;background:radial-gradient(130% 70% at 50% -8%,rgba(245,220,171,.10),rgba(245,220,171,0) 56%),var(--bg);overflow:hidden;}
.orac-pagina{position:relative;width:100%;max-width:760px;height:100%;display:flex;flex-direction:column;box-sizing:border-box;padding:clamp(20px,3.2vw,34px) clamp(20px,3.2vw,34px) 0;}
.orac-head{padding-bottom:18px;border-bottom:1px solid var(--line);margin-bottom:6px;}
.orac-head .eyebrow{display:block;font-family:var(--mono);font-size:.66rem;letter-spacing:.3em;text-transform:uppercase;color:var(--ink-2);margin:0 0 10px;}
.orac-head .ttl{display:block;font-family:var(--serif);font-weight:700;font-size:clamp(2rem,4.4vw,2.7rem);line-height:1;color:var(--bone);}
.orac-head .sub{display:block;font-family:var(--serif);font-style:italic;font-size:1.02rem;color:var(--ink);margin-top:8px;}
.orac-conversa{flex:1;min-height:0;overflow-y:auto;padding:24px 2px 8px;display:flex;flex-direction:column;gap:22px;}
.orac-conversa::-webkit-scrollbar{width:8px;}
.orac-conversa::-webkit-scrollbar-thumb{background:var(--line);border-radius:4px;}
.orac-conversa::-webkit-scrollbar-track{background:transparent;}
.msg{max-width:88%;}
.msg .quem{display:block;font-family:var(--mono);font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-2);margin-bottom:7px;}
.msg .texto{font-family:var(--sans);font-weight:400;font-size:1rem;line-height:1.72;color:var(--bone);white-space:pre-wrap;word-wrap:break-word;}
.msg.gabriel{align-self:flex-end;text-align:right;background:linear-gradient(180deg,var(--panel-2),var(--panel));border:1px solid var(--line);border-right:2px solid var(--gold);border-radius:4px;padding:14px 18px;}
.msg.gabriel .texto{color:var(--ink);}
.msg.oraculo{align-self:flex-start;background:linear-gradient(180deg,var(--panel-2),var(--panel));border:1px solid var(--line);border-left:2px solid var(--orac-c);border-radius:4px;padding:14px 18px;box-shadow:0 0 22px -10px var(--orac-c);}
.msg.erro .texto{color:#b5524a;font-style:italic;}
.orac-caret{display:inline-block;width:.5ch;height:1.05em;margin-left:2px;background:var(--gold);vertical-align:text-bottom;opacity:.7;animation:orac-blink 1.05s steps(1) infinite;}
@keyframes orac-blink{0%,55%{opacity:.7;}55.01%,100%{opacity:0;}}
.orac-modelo{align-self:flex-end;margin:0 0 6px;min-width:130px;}
.orac-modelo .q-field__native,.orac-modelo .q-field__native span{font-family:var(--mono);font-size:.62rem;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-2);}
.orac-pensa{align-self:flex-start;font-family:var(--serif);font-style:italic;color:var(--ink-2);font-size:1rem;padding-left:17px;}
.orac-pensa span{animation:opisca 1.4s infinite ease-in-out;}
.orac-pensa span:nth-child(2){animation-delay:.2s;}
.orac-pensa span:nth-child(3){animation-delay:.4s;}
@keyframes opisca{0%,100%{opacity:.2}50%{opacity:.9}}
.orac-scrawl{flex-shrink:0;display:flex;align-items:flex-end;gap:10px;padding:16px 0 18px;border-top:1px solid var(--line);background:var(--bg);}
.orac-scrawl .q-field{flex:1;}
.orac-scrawl input{color:var(--bone) !important;font-family:var(--sans) !important;font-size:1rem !important;}
.orac-scrawl .send{font-family:var(--mono);letter-spacing:.18em;text-transform:uppercase;font-size:.72rem;color:var(--ink-2);background:transparent;border:1px solid var(--line);border-radius:4px;padding:.6rem 1.4rem;cursor:pointer;transition:color .26s ease,border-color .26s ease,background .26s ease;}
.orac-scrawl .send:hover{border-color:var(--gold);color:var(--bone);background:rgba(244,186,60,.08);}
@media (prefers-reduced-motion:reduce){.orac-pensa span{animation:none;opacity:.7;}.orac-scrawl .send{transition:none;}}
@media (max-width:560px){.orac-pagina{padding:18px 16px;}.msg{max-width:94%;}}

/* ---- Pacote 2: gamificacao (decorativo, aditivo) ---- */

/* glifo no titulo */
.orac-head .ttl-glifo{color:var(--gold);font-size:.62em;vertical-align:.22em;margin-right:.42rem;opacity:.92;font-weight:400;}

/* cantos dourados na folha (4 colchetes via ::before/::after da .orac-pagina) */
.orac-pagina::before,.orac-pagina::after{content:"";position:absolute;width:18px;height:18px;pointer-events:none;z-index:2;opacity:.55;transition:opacity .3s ease;}
.orac-pagina::before{top:8px;left:8px;border-top:1.5px solid var(--orac-c);border-left:1.5px solid var(--orac-c);}
.orac-pagina::after{bottom:8px;right:8px;border-bottom:1.5px solid var(--orac-c);border-right:1.5px solid var(--orac-c);}
.orac-pagina:hover::before,.orac-pagina:hover::after{opacity:1;}
.orac-pagina>.orac-head{position:relative;}
.orac-head::after{content:"";position:absolute;top:-12px;right:-12px;width:18px;height:18px;border-top:1.5px solid var(--orac-c);border-right:1.5px solid var(--orac-c);pointer-events:none;z-index:2;opacity:.55;}
.orac-scrawl{position:relative;}
.orac-scrawl::after{content:"";position:absolute;bottom:8px;left:-12px;width:18px;height:18px;border-bottom:1.5px solid var(--orac-c);border-left:1.5px solid var(--orac-c);pointer-events:none;z-index:2;opacity:.55;}

/* marca d'agua: losango gigante fantasma atras de tudo */
.orac-pagina>.orac-marca{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(45deg);width:min(46vh,360px);height:min(46vh,360px);border:1px solid var(--orac-c);opacity:.04;pointer-events:none;z-index:0;}
.orac-conversa,.orac-head,.orac-scrawl,.orac-modelo,.orac-status{position:relative;z-index:1;}

/* console: prompt dourado antes do campo */
.orac-scrawl::before{content:"❯";font-family:var(--mono);color:var(--gold);font-size:1.05rem;align-self:center;opacity:.9;margin-right:6px;flex-shrink:0;}

/* status diegetico */
.orac-status{flex-shrink:0;display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.58rem;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-2);padding:0 2px 10px;}
.orac-status b,.orac-status .on{color:var(--orac-c);}
.orac-status-dot{width:5px;height:5px;border-radius:50%;background:var(--orac-c);box-shadow:0 0 6px var(--orac-c);animation:orac-pulse 2.4s ease-in-out infinite;}
@keyframes orac-pulse{0%,100%{opacity:.35;}50%{opacity:1;}}

/* scanline: textura de tela ultra-sutil sobre o stage */
.orac-stage::after{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:repeating-linear-gradient(to bottom,rgba(236,224,198,.018) 0,rgba(236,224,198,.018) 1px,transparent 1px,transparent 3px);mix-blend-mode:overlay;}

/* respeita reduced-motion: para o pulso */
@media (prefers-reduced-motion: reduce){
.orac-status-dot{animation:none;opacity:.8;}
}

/* realce violeta do oraculo — masthead na cor de assinatura */
.orac-head .ttl{color:var(--orac-c);}
.orac-head .ttl-glifo{color:var(--orac-c);}
.msg.oraculo{border-left:3px solid var(--orac-c);box-shadow:0 0 30px -6px var(--orac-c);}
</style>
"""


# ============================================================================
# PASSO 1 + 2 - A pagina /oraculo.
# ============================================================================
@ui.page("/oraculo")
async def pagina_oraculo():
    await aguardar_conexao_websocket("Despertando o Oraculo...")

    aplicar_tema_alderyn()
    barra_hud("oraculo")

    # Estado da conversa EM MEMORIA (sem persistencia nesta versao). Cada item e
    # um turno de texto limpo {role, content} - o que o usuario ve. O loop de
    # tool use roda numa lista efemera derivada deste historico a cada pergunta.
    historico: list[dict] = []
    ocupado = False  # trava: barra perguntas concorrentes enquanto o Oraculo pensa
    modelo_atual = MODELO_ORACULO   # seletor de modelo (UI): vale na proxima pergunta

    ui.add_head_html(_CSS)

    with ui.element("div").classes("orac-stage"):
        with ui.element("div").classes("orac-pagina"):
            ui.html('<div class="orac-marca"></div>')
            ui.html(
                '<div class="orac-head">'
                '<span class="eyebrow">Vig&iacute;lia Quebrada &middot; 312</span>'
                '<span class="ttl"><span class="ttl-glifo">&#9671;</span>O Or&aacute;culo</span>'
                '<span class="sub">a mente do mundo</span>'
                '</div>'
            )
            _MODELOS_ORAC = {
                "claude-opus-4-8": "Opus 4.8",
                "claude-opus-4-6": "Opus 4.6",
                "claude-sonnet-4-6": "Sonnet 4.6",
                "claude-haiku-4-5-20251001": "Haiku 4.5",
                "claude-fable-5": "Fable 5",
            }

            def _troca_modelo(e):
                nonlocal modelo_atual
                if e.value:
                    modelo_atual = e.value

            _sel = ui.select(
                options=_MODELOS_ORAC, value=modelo_atual, on_change=_troca_modelo
            )
            _sel.props("borderless dense options-dense").classes("orac-modelo")

            ui.html(
                '<div class="orac-status">'
                '<span class="orac-status-dot"></span>'
                'ARQUIVO &middot; <b>ABERTO</b>'
                '</div>'
            )

            conversa = ui.element("div").classes("orac-conversa")
            with conversa:
                ui.html(
                    '<div class="msg oraculo"><span class="quem">o or&aacute;culo</span>'
                    '<div class="texto">Pergunte. Eu leio o que est&aacute; registrado '
                    'sobre Alderyn — e nada al&eacute;m disso.</div></div>'
                )
            with ui.element("div").classes("orac-scrawl"):
                campo = ui.input(placeholder="Pergunte ao Oraculo...")
                campo.props('borderless dense input-class=text-base').classes("flex-1")
                botao = ui.html('<button class="send" type="button">consultar</button>')

    def _scroll():
        ui.run_javascript(
            "var c=document.querySelector('.orac-conversa');"
            "if(c)c.scrollTop=c.scrollHeight;"
        )

    def _render(quem_label: str, classe: str, texto: str):
        with conversa:
            ui.html(
                f'<div class="msg {classe}"><span class="quem">{html.escape(quem_label)}</span>'
                f'<div class="texto">{html.escape(texto)}</div></div>'
            )
        _scroll()

    def _orac_stream_iniciar() -> None:
        # Motor de revelacao no cliente (espelha o do jogo.py). O Python so seta
        # window.__orev.target; um requestAnimationFrame digita os chars numa
        # bolha .msg.oraculo viva. Scroller = .orac-conversa.
        ui.run_javascript(
            "(function(){"
            "var PISO=3, DIV=6;"
            "var conv=document.querySelector('.orac-conversa');if(!conv)return;"
            "var msg=document.createElement('div');msg.className='msg oraculo streaming';msg.id='__orac_stream';"
            "var quem=document.createElement('span');quem.className='quem';quem.textContent='o oráculo';"
            "var texto=document.createElement('div');texto.className='texto';"
            "var tn=document.createTextNode('');"
            "var caret=document.createElement('span');caret.className='orac-caret';"
            "texto.appendChild(tn);texto.appendChild(caret);"
            "msg.appendChild(quem);msg.appendChild(texto);conv.appendChild(msg);"
            "var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
            "window.__orev={tn:tn,target:'',shown:0,raf:0,cancel:false};"
            "function frame(){"
            "var r=window.__orev;if(!r||r.cancel)return;"
            "if(r.shown>r.target.length)r.shown=r.target.length;"
            "var pend=r.target.length-r.shown;"
            "if(pend>0){"
            "var passo=reduce?pend:Math.max(PISO,Math.ceil(pend/DIV));"
            "r.shown=Math.min(r.target.length,r.shown+passo);"
            "r.tn.nodeValue=r.target.slice(0,r.shown);"
            "var perto=(conv.scrollHeight-conv.scrollTop-conv.clientHeight)<80;"
            "if(perto)conv.scrollTop=conv.scrollHeight;"
            "}"
            "r.raf=requestAnimationFrame(frame);"
            "}"
            "window.__orev.raf=requestAnimationFrame(frame);"
            "})();"
        )

    def _orac_stream_update(texto: str) -> None:
        ui.run_javascript(
            f"(function(){{if(window.__orev)window.__orev.target={json.dumps(texto)};}})();"
        )

    def _orac_stream_finalizar() -> None:
        # Revela o resto, para o motor, sela o texto puro no .texto (pre-wrap
        # respeita os \n) e tira o caret + id. Scroll no fim.
        ui.run_javascript(
            "(function(){"
            "var r=window.__orev;var o=document.getElementById('__orac_stream');"
            "var txt=r?r.target:(o?o.textContent:'');"
            "if(r){r.cancel=true;if(r.raf)cancelAnimationFrame(r.raf);}"
            "if(o){var t=o.querySelector('.texto');if(t)t.textContent=txt;"
            "o.classList.remove('streaming');o.removeAttribute('id');"
            "var conv=document.querySelector('.orac-conversa');if(conv)conv.scrollTop=conv.scrollHeight;}"
            "window.__orev=null;})();"
        )

    def _orac_stream_abortar() -> None:
        ui.run_javascript(
            "(function(){var r=window.__orev;"
            "if(r){r.cancel=true;if(r.raf)cancelAnimationFrame(r.raf);}"
            "window.__orev=null;"
            "var o=document.getElementById('__orac_stream');if(o)o.remove();})();"
        )

    async def responder(pergunta: str):
        nonlocal ocupado
        if ocupado:
            return
        pergunta = (pergunta or "").strip()
        if not pergunta:
            return
        ocupado = True
        campo.value = ""

        historico.append({"role": "user", "content": pergunta})
        _render("gabriel", "gabriel", pergunta)

        # Lista EFEMERA pro loop de tool use: parte do historico limpo.
        mensagens: list[dict] = [
            {"role": m["role"], "content": m["content"]} for m in historico
        ]

        pensa = None

        def _mostra_pensa():
            nonlocal pensa
            if pensa is None:
                with conversa:
                    pensa = ui.html(
                        '<div class="orac-pensa">o or&aacute;culo consulta'
                        '<span>.</span><span>.</span><span>.</span></div>'
                    )
                _scroll()

        def _tira_pensa():
            nonlocal pensa
            if pensa is not None:
                pensa.delete()
                pensa = None

        _mostra_pensa()

        final: str | None = None
        erro_fatal: str | None = None
        selado_na_tela = False
        bolha_viva = False
        try:
            for _ in range(MAX_ITERACOES):
                bolha_viva = False
                texto_parcial = ""
                ultimo = 0.0
                async with _get_aclient().messages.stream(
                    model=modelo_atual,
                    max_tokens=1500,
                    system=PERSONA_ORACULO,
                    tools=[TOOL_CONSULTAR_BANCO, TOOL_REGISTRAR_DIRETRIZ],
                    messages=mensagens,
                ) as stream:
                    async for delta in stream.text_stream:
                        if not bolha_viva:
                            # primeiro pedaco de prosa: tira "consulta...", abre a
                            # bolha viva e comeca a digitar.
                            _tira_pensa()
                            _orac_stream_iniciar()
                            bolha_viva = True
                        texto_parcial += delta
                        agora = time.monotonic()
                        if agora - ultimo >= 0.06:
                            ultimo = agora
                            _orac_stream_update(texto_parcial)
                    resp = await stream.get_final_message()

                if resp.stop_reason == "tool_use":
                    # raro: a IA escreveu prosa antes de consultar. Descarta a
                    # bolha parcial e volta o "consulta...".
                    if bolha_viva:
                        _orac_stream_abortar()
                        bolha_viva = False
                        _mostra_pensa()
                    mensagens.append({"role": "assistant", "content": resp.content})
                    resultados = []
                    for bloco in resp.content:
                        if getattr(bloco, "type", None) != "tool_use":
                            continue
                        if bloco.name == "consultar_banco":
                            sql = (bloco.input or {}).get("sql", "")
                            print(f"[oraculo] consultar_banco: {sql}")
                            saida = await executar_select_seguro(sql)
                        elif bloco.name == "registrar_diretriz":
                            ent = bloco.input or {}
                            texto = ent.get("texto", "")
                            categoria = ent.get("categoria", "nota")
                            print(f"[oraculo] registrar_diretriz: [{categoria}] {texto}")
                            saida = await registrar_diretriz_seguro(texto, categoria)
                        else:
                            saida = f"ERRO: ferramenta desconhecida: {bloco.name}"
                        resultados.append({
                            "type": "tool_result",
                            "tool_use_id": bloco.id,
                            "content": saida,
                        })
                    mensagens.append({"role": "user", "content": resultados})
                    continue

                # end_turn (ou outro): texto final.
                final = "".join(
                    b.text for b in resp.content if getattr(b, "type", None) == "text"
                ).strip()
                if bolha_viva:
                    _orac_stream_update(final)
                    _orac_stream_finalizar()
                    selado_na_tela = True
                break
        except Exception as exc:  # noqa: BLE001
            import traceback
            print("[oraculo] ERRO === traceback ===")
            print(traceback.format_exc())
            if bolha_viva:
                _orac_stream_abortar()
            erro_fatal = f"o Oráculo vacila - {type(exc).__name__}. Tente de novo."
        finally:
            _tira_pensa()

        if erro_fatal:
            _render("o oraculo", "oraculo erro", erro_fatal)
            # turno falhou: tira a pergunta do historico pra nao desalinhar.
            if historico and historico[-1]["role"] == "user":
                historico.pop()
            ocupado = False
            return

        if final is None:
            # estourou as iteracoes sem resposta final.
            final = "O Oráculo se perdeu na consulta."

        historico.append({"role": "assistant", "content": final})
        if not selado_na_tela:
            # nunca digitou na tela (estourou iteracoes, ou end_turn sem prosa):
            # renderiza estatico pra resposta aparecer.
            _render("o oraculo", "oraculo", final)
        ocupado = False

    async def _enviar(_=None):
        await responder(campo.value)

    campo.on("keydown.enter", _enviar)
    botao.on("click", _enviar)
