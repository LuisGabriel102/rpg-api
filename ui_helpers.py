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


def barra_nav(ativo: str = "") -> None:
    """Barra de navegacao compartilhada da Oficina (pele zinc/amber). Fixa no topo.
    'ativo' acende o botao da pagina atual: oficina, npcs, bestiario, estrelas,
    vocacoes. (No /jogar NAO se usa esta barra - la a saida e na pele Gravura.)"""
    itens = [
        ("oficina", "Oficina", "/oficina"),
        ("npcs", "NPCs", "/oficina/npcs"),
        ("bestiario", "Bestiário", "/oficina/bestiario"),
        ("estrelas", "Estrelas", "/oficina/estrelas"),
        ("vocacoes", "Vocações", "/oficina/vocacoes"),
        ("jogar", "Jogar", "/jogar"),
    ]
    with ui.row().classes(
        "w-full items-center gap-2 px-8 py-3 bg-zinc-900 "
        "border-b border-zinc-700 sticky top-0 z-50"
    ):
        for chave, rotulo, destino in itens:
            base = ("text-sm uppercase tracking-wider px-3 py-1 rounded "
                    "transition-colors no-underline ")
            cor = "text-amber-200 font-bold" if chave == ativo else "text-zinc-400 hover:text-amber-200"
            ui.link(rotulo, destino).classes(base + cor)
