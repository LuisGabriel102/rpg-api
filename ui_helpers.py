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

    placeholder.delete()


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
