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

from nicegui import ui, run
from anthropic import Anthropic
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
body,.q-page,.q-page-container,.nicegui-content{background:var(--bg) !important;}
.nicegui-content{padding:0 !important;gap:0 !important;}
.orac-stage{width:100%;min-height:100vh;display:flex;justify-content:center;padding:5vh 18px 4vh;box-sizing:border-box;background:radial-gradient(130% 70% at 50% -8%,rgba(245,220,171,.10),rgba(245,220,171,0) 56%),var(--bg);}
.orac-pagina{position:relative;width:100%;max-width:760px;display:flex;flex-direction:column;min-height:86vh;box-sizing:border-box;padding:clamp(20px,3.2vw,34px);}
.orac-head{padding-bottom:18px;border-bottom:1px solid var(--line);margin-bottom:6px;}
.orac-head .eyebrow{display:block;font-family:var(--mono);font-size:.66rem;letter-spacing:.3em;text-transform:uppercase;color:var(--ink-2);margin:0 0 10px;}
.orac-head .ttl{display:block;font-family:var(--serif);font-weight:700;font-size:clamp(2rem,4.4vw,2.7rem);line-height:1;color:var(--bone);}
.orac-head .sub{display:block;font-family:var(--serif);font-style:italic;font-size:1.02rem;color:var(--ink);margin-top:8px;}
.orac-conversa{flex:1;overflow-y:auto;padding:24px 2px 112px;display:flex;flex-direction:column;gap:22px;}
.orac-conversa::-webkit-scrollbar{width:8px;}
.orac-conversa::-webkit-scrollbar-thumb{background:var(--line);border-radius:4px;}
.orac-conversa::-webkit-scrollbar-track{background:transparent;}
.msg{max-width:88%;}
.msg .quem{display:block;font-family:var(--mono);font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-2);margin-bottom:7px;}
.msg .texto{font-family:var(--sans);font-weight:400;font-size:1rem;line-height:1.72;color:var(--bone);white-space:pre-wrap;word-wrap:break-word;}
.msg.gabriel{align-self:flex-end;text-align:right;}
.msg.gabriel .texto{color:var(--ink);}
.msg.oraculo{align-self:flex-start;border-left:1px solid var(--line);padding-left:17px;}
.msg.erro .texto{color:#b5524a;font-style:italic;}
.orac-pensa{align-self:flex-start;font-family:var(--serif);font-style:italic;color:var(--ink-2);font-size:1rem;padding-left:17px;}
.orac-pensa span{animation:opisca 1.4s infinite ease-in-out;}
.orac-pensa span:nth-child(2){animation-delay:.2s;}
.orac-pensa span:nth-child(3){animation-delay:.4s;}
@keyframes opisca{0%,100%{opacity:.2}50%{opacity:.9}}
.orac-scrawl{position:fixed;left:0;right:0;bottom:0;margin:0 auto;width:100%;max-width:760px;box-sizing:border-box;display:flex;align-items:flex-end;gap:10px;padding:16px clamp(20px,3.2vw,34px);border-top:1px solid var(--line);background:var(--bg);z-index:50;}
.orac-scrawl .q-field{flex:1;}
.orac-scrawl input{color:var(--bone) !important;font-family:var(--sans) !important;font-size:1rem !important;}
.orac-scrawl .send{font-family:var(--mono);letter-spacing:.18em;text-transform:uppercase;font-size:.72rem;color:var(--ink-2);background:transparent;border:1px solid var(--line);border-radius:4px;padding:.6rem 1.4rem;cursor:pointer;transition:color .26s ease,border-color .26s ease,background .26s ease;}
.orac-scrawl .send:hover{border-color:var(--gold);color:var(--bone);background:rgba(244,186,60,.08);}
@media (prefers-reduced-motion:reduce){.orac-pensa span{animation:none;opacity:.7;}.orac-scrawl .send{transition:none;}}
@media (max-width:560px){.orac-pagina{padding:18px 16px;}.msg{max-width:94%;}}
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

    ui.add_head_html(_CSS)

    with ui.element("div").classes("orac-stage"):
        with ui.element("div").classes("orac-pagina"):
            ui.html(
                '<div class="orac-head">'
                '<span class="eyebrow">Vig&iacute;lia Quebrada &middot; 312</span>'
                '<span class="ttl">O Or&aacute;culo</span>'
                '<span class="sub">a mente do mundo</span>'
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

        # Lista EFEMERA pro loop de tool use: parte do historico de texto limpo e
        # acumula os turns de tool_use/tool_result so durante esta pergunta.
        mensagens: list[dict] = [
            {"role": m["role"], "content": m["content"]} for m in historico
        ]

        # indicador "o oraculo consulta..."
        with conversa:
            pensa = ui.html(
                '<div class="orac-pensa">o or&aacute;culo consulta'
                '<span>.</span><span>.</span><span>.</span></div>'
            )
        _scroll()

        final: str | None = None
        erro_fatal: str | None = None
        try:
            for _ in range(MAX_ITERACOES):
                resp = await run.io_bound(_chamar_opus, mensagens)
                if resp.stop_reason == "tool_use":
                    # anexa o turn do assistant (blocos como vieram) e roda cada
                    # consulta, devolvendo um tool_result com o tool_use_id certo.
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
                # end_turn (ou qualquer outro): pega o texto final e encerra.
                final = "".join(
                    b.text for b in resp.content if getattr(b, "type", None) == "text"
                ).strip()
                break
        except Exception as exc:  # noqa: BLE001
            import traceback
            print("[oraculo] ERRO === traceback ===")
            print(traceback.format_exc())
            erro_fatal = f"o Oráculo vacila - {type(exc).__name__}. Tente de novo."
        finally:
            pensa.delete()

        if erro_fatal:
            _render("o oraculo", "oraculo erro", erro_fatal)
            # turno falhou: tira a pergunta do historico pra nao desalinhar a
            # alternancia user/assistant na proxima pergunta.
            if historico and historico[-1]["role"] == "user":
                historico.pop()
            ocupado = False
            return

        if not final:
            # estourou as 6 iteracoes sem resposta final (PASSO 3.3).
            final = "O Oráculo se perdeu na consulta."

        historico.append({"role": "assistant", "content": final})
        _render("o oraculo", "oraculo", final)
        ocupado = False

    async def _enviar(_=None):
        await responder(campo.value)

    campo.on("keydown.enter", _enviar)
    botao.on("click", _enviar)
