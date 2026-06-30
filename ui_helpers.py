"""
Helpers reutilizaveis pra UI da Oficina do Mestre.

==============================================================================
aguardar_conexao_websocket: padrao Two-Phase Loading do NiceGUI 3.x
==============================================================================

PROBLEMA QUE RESOLVE:

NiceGUI tem um response_timeout de 3 segundos por padrao em handlers @ui.page
async. Se a coroutine handler nao retornar uma resposta HTTP em 3s (porque
esta presa em await session.execute() ou similar), o NiceGUI:

  1. Cancela a coroutine (task.cancel() injeta CancelledError, que e
     BaseException — NAO Exception. try/except Exception NAO captura.)
  2. Deleta o client do servidor (client.delete() remove de Client.instances)
  3. Manda HTML vazio com status 200 OK pro browser
  4. Browser tenta abrir WebSocket com client_id que ja nao existe no servidor
  5. Handshake do WebSocket falha
  6. JavaScript do NiceGUI 3.x recarrega a pagina automaticamente
  7. Loop infinito de "Response not ready after 3.0 seconds" no log

SINTOMA NO LOG (confirma esse bug):
    Response for /sua/rota not ready after 3.0 seconds
    "GET /sua/rota HTTP/1.1" 200 OK
    "WebSocket /socket.io/..." [accepted]
    connection open
    connection closed
    Response for /sua/rota not ready after 3.0 seconds   <-- repete em loop

SOLUCAO:

Chamar await ui.context.client.connected() ANTES das queries pesadas.
Isso forca o NiceGUI a:
  - Enviar a UI atual (placeholder com spinner) imediatamente como resposta HTTP
  - Aguardar o WebSocket abrir
  - Apos o WS abrir, qualquer mudanca na UI vai por la, sem limite de tempo

Depois disso, queries de 5s, 10s, 30s funcionam normal — porque ja nao estao
mais bloqueando a fase HTTP da resposta.

USO:

    @ui.page("/oficina/npcs/{npc_id}")
    async def detalhe(npc_id: int):
        await aguardar_conexao_websocket("Buscando NPC...")
        # daqui pra frente, sem medo de timeout
        data = await buscar_dados_pesados(npc_id)
        with ui.column():
            ui.label(data["nome"])

REFERENCIAS:
- https://github.com/zauberzeug/nicegui/discussions/2429
- https://github.com/zauberzeug/nicegui/discussions/3477
- nicegui/page.py source (asyncio.wait com FIRST_COMPLETED + timeout=3.0)

REGRA DE OURO:
Toda @ui.page async que faz I/O (banco, API externa, leitura de arquivo)
deve chamar este helper como PRIMEIRA acao. Sem excecao. Mesmo se hoje a
query roda em 1s — amanha com mais dados ela vai pra 4s e quebra.
==============================================================================
"""

from nicegui import ui


async def aguardar_conexao_websocket(titulo: str = "Carregando...") -> None:
    """
    Cria placeholder com spinner, manda pro browser, aguarda WebSocket conectar.

    Apos retornar, qualquer elemento criado/alterado na UI sera transmitido
    via WebSocket sem o limite de 3 segundos do response_timeout do NiceGUI.

    Args:
        titulo: Texto exibido sob o spinner enquanto carrega. Pode ser usado
                pra dar pista ao usuario do que esta sendo buscado
                (ex: "Buscando NPC #33...", "Catalogando vocacoes...").
    """
    placeholder = ui.column().classes(
        "w-full min-h-screen bg-zinc-900 items-center justify-center gap-4"
    )
    with placeholder:
        ui.spinner("bars", size="4em", color="amber-6")
        ui.label(titulo).classes("text-sm text-zinc-500 italic mt-2 font-mono")

    # Esta linha divide as duas fases:
    # - Fase 1 (acima): UI placeholder enviada como resposta HTTP imediata
    # - Fase 2 (abaixo): WebSocket aberto, mudancas vao por ele sem timeout
    await ui.context.client.connected()

    try:
        placeholder.delete()
    except (ValueError, KeyError):
        pass  # cliente reconectou/re-renderizou durante connected(): placeholder ja saiu da arvore


_VITRAL_NAV_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&display=swap" rel="stylesheet">
<style>
.cat-nav{display:flex;align-items:center;gap:2px;padding:14px 30px;background:#0a0c14;border-bottom:1px solid #b8902f;width:100%;box-sizing:border-box;}
.cat-navicon{margin-right:12px;flex:none;}
.cat-navlink{font-family:'IM Fell English SC',serif;letter-spacing:.12em;font-size:15px;color:#b3a06f;text-decoration:none;padding:4px 12px;white-space:nowrap;}
.cat-navlink:hover{color:#e8c66a;}
.cat-navlink.on{color:#f0d98a;border-bottom:1px solid #e8c66a;padding-bottom:3px;}
.cat-enter{font-family:'IM Fell English',serif;font-style:italic;letter-spacing:.04em;color:#e8c66a;text-decoration:none;font-size:16px;}
.cat-enter:hover{color:#f6d98a;}
</style>
"""


def barra_nav(ativo: str = "") -> None:
    """Barra de navegação compartilhada — pele vitral de catedral.
    'ativo' acende a aba atual. Aceita os argumentos antigos:
    oficina, npcs, bestiario, estrelas, vocacoes (e historias).
    Emite HTML próprio + injeta o CSS escopado da barra (classes .cat-*),
    sem regras globais — não afeta o corpo zinc/amber abaixo."""
    ui.add_head_html(_VITRAL_NAV_CSS)
    icone = ('<svg class="cat-navicon" width="16" height="14" viewBox="0 0 24 20" fill="none" '
             'stroke="#c9a227" stroke-width="1.1" aria-hidden="true">'
             '<path d="M12 3c3 0 5 2 5 5s-2 7-5 9c-3-2-5-6-5-9s2-5 5-5z"/><path d="M3 10h6M15 10h6"/></svg>')
    # (rotulo_exibido, chave_de_comparacao, destino) — a chave bate com o arg antigo
    itens = [
        ("oficina", "oficina", "/oficina"),
        ("personagens", "npcs", "/oficina/npcs"),
        ("bestiário", "bestiario", "/oficina/bestiario"),
        ("estrelas", "estrelas", "/oficina/estrelas"),
        ("vocações", "vocacoes", "/oficina/vocacoes"),
        ("histórias", "historias", "/oficina/historias"),
    ]
    links = "".join(
        f'<a class="cat-navlink{" on" if chave == ativo else ""}" href="{destino}">{rotulo}</a>'
        for rotulo, chave, destino in itens
    )
    html = (f'<div class="cat-nav">{icone}{links}<span style="flex:1"></span>'
            f'<a class="cat-enter" href="/jogar">entrar no mundo</a></div>')
    ui.html(html).classes("w-full sticky top-0 z-50")


def barra_nav_alderyn(pagina_atual: str) -> None:
    """Barra de navegacao fina no topo das paginas do Alderyn (Versao A: so navega).

    pagina_atual: 'oficina' | 'jogo' | 'oraculo' -> marca qual link fica destacado.
    Versao A: cada link so chama ui.navigate.to. Nada de dado viaja junto.
    """
    destinos = [
        ("oficina", "Oficina", "/oficina"),
        ("jogo",    "Jogo",    "/jogar"),
        ("oraculo", "Oráculo", "/oraculo"),
        ("sistema", "Sistema", "/sistema"),
    ]
    with ui.row().style(
        "width:100%; gap:20px; align-items:center; "
        "padding:8px 18px; margin:0; "
        "background:rgba(18,18,20,0.94); "
        "border-bottom:1px solid rgba(255,255,255,0.08); "
        "position:sticky; top:0; z-index:1000;"
    ):
        for chave, rotulo, rota in destinos:
            ativo = (chave == pagina_atual)
            cor = "#e9e6dd" if ativo else "rgba(233,230,221,0.50)"
            peso = "600" if ativo else "400"
            base = (
                f"color:{cor}; font-weight:{peso}; font-size:15px; "
                "padding:2px 0; letter-spacing:0.3px;"
            )
            if ativo:
                ui.label(rotulo).style(
                    base + " border-bottom:2px solid #e9e6dd; cursor:default;"
                )
            else:
                lk = ui.label(rotulo).style(
                    base + " border-bottom:2px solid transparent; cursor:pointer;"
                )
                lk.on("click", lambda r=rota: ui.navigate.to(r))


# =========================================================
#  TEMA ÚNICO DA CATEDRAL + BARRA HUD  (casca visual unificada)
#  Fonte de verdade: _CATEDRAL_TPL em oficina_app.py.
#  Aditivo — não substitui barra_nav_alderyn nem barra_nav (legados).
# =========================================================

CSS_ALDERYN = """<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@300;400;500&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root{
  --bg:#131110; --panel:#1d1812; --panel-2:#241d15;
  --line:#352c22; --line-soft:#282017;
  --bone:#ece0c6; --ink:#a0957d; --ink-2:#7a6e59; --glow:#f5dcab;
  --blood:#e8493a; --amber:#f4ba3c; --jade:#2fc4a0;
  --venom:#9bd23e; --violet:#b06ff0; --sepia:#d29658;
  --lock:#5c5448; --gold:#f4ba3c;
  --serif:'Cormorant Garamond',Georgia,serif;
  --sans:'Inter',system-ui,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
}
html,body{height:100%;margin:0;}
body{overflow:hidden;}
.ald-hud{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;padding:13px 26px;background:rgba(19,17,16,.94);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:1000;-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px);}
.ald-brand{display:flex;align-items:center;gap:10px;text-decoration:none;}
.ald-brand .ald-rune{color:var(--gold);font-size:15px;line-height:1;}
.ald-brand .ald-mark{font-family:var(--mono);font-size:.78rem;letter-spacing:.34em;text-transform:uppercase;color:var(--bone);}
.ald-links{display:flex;align-items:center;gap:4px;flex-wrap:wrap;}
.ald-link{position:relative;text-decoration:none;font-family:var(--mono);font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-2);padding:9px 16px;transition:color .26s ease,transform .26s ease,text-shadow .26s ease;}
.ald-cnr{position:absolute;width:11px;height:11px;opacity:0;transition:opacity .26s ease;pointer-events:none;}
.ald-cnr.tl{top:-1px;left:-1px;border-top:2px solid var(--c);border-left:2px solid var(--c);}
.ald-cnr.tr{top:-1px;right:-1px;border-top:2px solid var(--c);border-right:2px solid var(--c);}
.ald-cnr.bl{bottom:-1px;left:-1px;border-bottom:2px solid var(--c);border-left:2px solid var(--c);}
.ald-cnr.br{bottom:-1px;right:-1px;border-bottom:2px solid var(--c);border-right:2px solid var(--c);}
.ald-link:hover{color:var(--bone);transform:translateY(-2px);text-shadow:0 0 10px rgba(244,186,60,.4);}
.ald-link:hover .ald-cnr{opacity:1;}
.ald-link.on{color:var(--c);text-shadow:0 0 10px rgba(244,186,60,.4);}
.ald-link.on .ald-cnr{opacity:1;}
@media (max-width:560px){.ald-hud{padding:12px 16px;}}
@media (prefers-reduced-motion:reduce){.ald-hud *{transition:none !important;}.ald-link:hover{transform:none;}}
</style>"""


def aplicar_tema_alderyn() -> None:
    """Injeta no <head> as fontes, os tokens da Catedral e o CSS da barra HUD.
    Chamar UMA vez no setup de cada pagina migrada (antes de barra_hud)."""
    ui.add_head_html(CSS_ALDERYN)


def barra_hud(pagina_atual: str) -> None:
    """Barra de navegacao HUD — a casca unica do sistema.
    pagina_atual: 'catedral' | 'jogar' | 'oraculo' | 'sistema'.
    Requer aplicar_tema_alderyn() ja chamado na pagina."""
    destinos = [
        ("catedral", "Catedral",       "/oficina"),
        ("jogar",    "Jogar",          "/jogar"),
        ("oraculo",  "Or&aacute;culo", "/oraculo"),
        ("sistema",  "Sistema",        "/sistema"),
    ]
    cnr = ('<i class="ald-cnr tl"></i><i class="ald-cnr tr"></i>'
           '<i class="ald-cnr bl"></i><i class="ald-cnr br"></i>')
    links = ""
    for chave, rotulo, href in destinos:
        on = " on" if chave == pagina_atual else ""
        links += (f'<a class="ald-link{on}" style="--c:var(--gold)" '
                  f'href="{href}">{cnr}{rotulo}</a>')
    html = (
        '<nav class="ald-hud" role="navigation" aria-label="Navega&ccedil;&atilde;o principal">'
        '<a class="ald-brand" href="/oficina">'
        '<span class="ald-rune">&#9671;</span>'
        '<span class="ald-mark">Alderyn</span></a>'
        f'<div class="ald-links">{links}</div>'
        '</nav>'
    )
    ui.html(html).classes("w-full")
