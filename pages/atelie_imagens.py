"""
Sub-aba "Imagens" do Ateliê — Catedral do Alderyn (Módulo 4.6.4).

Funcionalidades:
  1. Botão "Gerar imagem" com escolha de modelo + barra de progresso animada
  2. Galeria de TODAS imagens (ordenada por status: canônica → aprovada → rascunho → aposentada)
  3. Ações por imagem: aprovar / promover canônica / aposentar / deletar
  4. Comparação 2-up: canônica atual vs imagem selecionada
  5. Copy clipboard do prompt usado em cada imagem

UX da geração:
  - Botão fica disabled durante a chamada (~25s típico)
  - Spinner + mensagem "Gerando com Gemini..." (atualiza com modelo escolhido)
  - Notificação top quando termina (positive ou negative)
  - Galeria atualiza automaticamente após sucesso
"""

from __future__ import annotations

import json
from typing import Awaitable, Callable, Optional

from nicegui import ui

from pipeline_geracao import (
    gerar_imagem_npc,
    PRECO_POR_GERACAO,
)
from pages.atelie_queries import (
    listar_imagens_npc,
    buscar_canonica_atual,
    atualizar_status_imagem,
    deletar_imagem as deletar_imagem_db,
    listar_variacoes_npc,
    inserir_imagem_upload,
)
from r2_storage import (
    delete_imagem as deletar_imagem_r2,
    upload_imagem_npc,
)


# Mapeamento amigável modelo→ordem de fallback
PRESETS_MODELO = {
    "gemini_nano":  ("gemini_nano", "gpt_image", "flux_kontext"),
    "gpt_image":    ("gpt_image", "gemini_nano", "flux_kontext"),
    "flux_kontext": ("flux_kontext", "gemini_nano", "gpt_image"),
}

ROTULOS_MODELO = {
    "gemini_nano":  "Gemini (primário recomendado)",
    "gpt_image":    "GPT Image",
    "flux_kontext": "FLUX Kontext",
}

CORES_STATUS = {
    "canonica":   ("amber", "✦ Canônica"),
    "aprovada":   ("green", "✓ Aprovada"),
    "rascunho":   ("zinc",  "◷ Rascunho"),
    "aposentada": ("red",   "✕ Aposentada"),
}

# Tailwind faz purge de classes em produção: classes geradas dinamicamente via
# f-string (ex: f"border-{cor}-700") podem ser removidas. Mantemos um dicionário
# com as classes COMPLETAS hardcoded — o purge as preserva.
CLASSES_BORDER_BY_STATUS = {
    "canonica":   "border-amber-700",
    "aprovada":   "border-green-700",
    "rascunho":   "border-zinc-700",
    "aposentada": "border-red-700",
}

CLASSES_BORDER_HOVER_BY_STATUS = {
    "canonica":   "hover:border-amber-500",
    "aprovada":   "hover:border-green-500",
    "rascunho":   "hover:border-zinc-500",
    "aposentada": "hover:border-red-500",
}

CLASSES_TEXT_BY_STATUS = {
    "canonica":   "text-amber-300",
    "aprovada":   "text-green-300",
    "rascunho":   "text-zinc-300",
    "aposentada": "text-red-300",
}


# =============================================================================
# Estado da sub-aba (em memória, recarregado a cada navegação)
# =============================================================================

class EstadoImagens:
    """Estado mutável da sub-aba Imagens."""

    def __init__(self):
        self.imagens: list[dict] = []
        self.canonica: Optional[dict] = None
        self.variacoes: list[dict] = []
        self.imagem_comparacao_id: Optional[int] = None  # pra comparar 2-up
        self.modelo_escolhido: str = "gemini_nano"
        self.variacao_escolhida_id: Optional[int] = None
        self.gerando: bool = False


# =============================================================================
# RENDER PRINCIPAL
# =============================================================================

async def render_aba_imagens(
    npc_id: int,
    dados_npc: dict,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Renderiza a sub-aba Imagens.

    Args:
        npc_id: ID do NPC.
        dados_npc: dict com dados do NPC (pra mostrar nome).
        on_alterado: callback chamado quando algo muda no banco (pra refresh).
    """
    estado = EstadoImagens()

    # Carregar dados iniciais
    try:
        estado.imagens = await listar_imagens_npc(npc_id)
        estado.canonica = await buscar_canonica_atual(npc_id)
        estado.variacoes = await listar_variacoes_npc(npc_id)
    except Exception as e:
        ui.label(f"Erro ao carregar imagens: {e}").classes("text-red-400")
        return

    nome_npc = dados_npc.get("nome") or f"NPC #{npc_id}"
    tem_ancora = bool(
        dados_npc.get("descricao_ancora_en") or dados_npc.get("descricao_ancora_pt")
    )

    with ui.column().classes("w-full gap-4"):

        # ─── BLOCO DE GERAÇÃO ───
        with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4 gap-3"):
            ui.label("Gerar nova imagem").classes(
                "text-amber-200 text-lg font-semibold"
            )

            if not tem_ancora:
                ui.label(
                    "⚠ NPC sem âncora de identidade. Vá pra aba 'Aparência' e "
                    "preencha 'Âncora EN' (ou PT) antes de gerar."
                ).classes("text-red-300 text-sm")
            else:
                # Linha de configuração
                with ui.row().classes("w-full items-end gap-3 flex-wrap"):
                    # Seletor de modelo
                    def _on_modelo(e):
                        estado.modelo_escolhido = e.value

                    seletor_modelo = (
                        ui.select(
                            options={
                                k: f"{ROTULOS_MODELO[k]} — ${PRECO_POR_GERACAO[k]:.3f}"
                                for k in PRESETS_MODELO.keys()
                            },
                            value="gemini_nano",
                            label="Modelo primário",
                            on_change=_on_modelo,
                        )
                        .props("outlined dense color=amber-8 dark")
                        .classes("w-80")
                    )

                    # Seletor de variação (opcional)
                    if estado.variacoes:
                        opcoes_var = {None: "(nenhuma — usa âncora pura)"}
                        for v in estado.variacoes:
                            label = v["nome_variacao"]
                            if v["e_uso_prioritario"]:
                                label += " ★"
                            opcoes_var[v["id"]] = label

                        # Default: variação prioritária se houver
                        var_default = next(
                            (v["id"] for v in estado.variacoes if v["e_uso_prioritario"]),
                            None,
                        )
                        estado.variacao_escolhida_id = var_default

                        def _on_var(e):
                            estado.variacao_escolhida_id = e.value

                        sel_var = (
                            ui.select(
                                options=opcoes_var,
                                value=var_default,
                                label="Variação",
                                on_change=_on_var,
                            )
                            .props("outlined dense color=amber-8 dark")
                            .classes("w-72")
                        )

                    # Spacer + botões
                    ui.element("div").classes("flex-1")

                    # Botão Upload (do computador)
                    btn_upload = ui.button(
                        "Upload do PC", icon="upload_file",
                    ).props("color=zinc-6 outline dense").classes("min-w-[140px]")

                    # Botão de gerar (IA)
                    btn_gerar = ui.button(
                        "Gerar imagem", icon="auto_awesome",
                    ).props("color=amber-8 unelevated").classes("min-w-[160px]")

                # Barra de progresso (oculta inicialmente)
                progresso_box = ui.row().classes("w-full items-center gap-3 hidden")
                with progresso_box:
                    spinner = ui.spinner(size="md", color="amber-8")
                    msg_progresso = ui.label("Gerando...").classes(
                        "text-amber-300 text-sm"
                    )

                # Função de geração
                async def _on_gerar():
                    if estado.gerando:
                        return
                    estado.gerando = True
                    btn_gerar.props("disabled loading")
                    progresso_box.classes(remove="hidden")

                    modelo = estado.modelo_escolhido
                    msg_progresso.text = (
                        f"Chamando {ROTULOS_MODELO[modelo]} (~25s)..."
                    )

                    # Buscar descrição de modificação se variação escolhida
                    desc_mod = ""
                    ilum_over = ""
                    if estado.variacao_escolhida_id:
                        var = next(
                            (v for v in estado.variacoes
                             if v["id"] == estado.variacao_escolhida_id),
                            None,
                        )
                        if var:
                            desc_mod = var.get("descricao_modificacao") or ""
                            ilum_over = var.get("iluminacao_override") or ""

                    try:
                        resultado = await gerar_imagem_npc(
                            npc_id=npc_id,
                            rotulo=f"{nome_npc} - {modelo}",
                            modelos_preferidos=PRESETS_MODELO[modelo],
                            variacao_id=estado.variacao_escolhida_id,
                            descricao_modificacao=desc_mod,
                            iluminacao_override=ilum_over,
                            usar_referencia_canonica=True,
                        )
                    except Exception as e:
                        ui.notify(
                            f"Erro inesperado: {e}",
                            type="negative", position="top", timeout=8000,
                        )
                        estado.gerando = False
                        btn_gerar.props(remove="disabled loading")
                        progresso_box.classes("hidden")
                        return

                    if resultado.status == "success":
                        ui.notify(
                            f"✓ Imagem gerada com {resultado.modelo_usado} "
                            f"em {resultado.duracao_total_ms / 1000:.1f}s "
                            f"(${resultado.custo_usd:.3f})",
                            type="positive", position="top", timeout=5000,
                        )
                        # Recarregar galeria
                        try:
                            estado.imagens = await listar_imagens_npc(npc_id)
                            estado.canonica = await buscar_canonica_atual(npc_id)
                            galeria.refresh()
                            comparacao.refresh()
                            await on_alterado()
                        except Exception as e:
                            ui.notify(
                                f"Imagem gerada mas falhou ao recarregar galeria: {e}",
                                type="warning", position="top",
                            )
                    else:
                        ui.notify(
                            f"✗ Falhou em '{resultado.estagio_falha}': "
                            f"{resultado.mensagem_erro}",
                            type="negative", position="top", timeout=10000,
                        )

                    estado.gerando = False
                    btn_gerar.props(remove="disabled loading")
                    progresso_box.classes("hidden")

                btn_gerar.on("click", _on_gerar)

                # Handler do botao Upload - abre dialog com selector de arquivo
                def _on_upload_click():
                    _abrir_dialog_upload(
                        npc_id=npc_id,
                        estado=estado,
                        galeria_refresh=galeria,
                        comparacao_refresh=comparacao,
                        on_alterado=on_alterado,
                    )

                btn_upload.on("click", _on_upload_click)

        # ─── COMPARAÇÃO 2-UP ───
        @ui.refreshable
        def comparacao():
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4"):
                ui.label("Comparação canônica vs selecionada").classes(
                    "text-amber-200 text-lg font-semibold mb-2"
                )

                if not estado.canonica:
                    ui.label(
                        "Sem imagem canônica ainda. Gere uma e promova "
                        "(✦ Canônica) pra usar comparação."
                    ).classes("text-zinc-400 italic")
                    return

                # Imagem selecionada (default: primeira não-canônica)
                outras = [i for i in estado.imagens if i["status"] != "canonica"]
                if estado.imagem_comparacao_id is None and outras:
                    estado.imagem_comparacao_id = outras[0]["id"]

                img_selecionada = next(
                    (i for i in estado.imagens
                     if i["id"] == estado.imagem_comparacao_id),
                    None,
                )

                with ui.row().classes("w-full gap-4"):
                    # Esquerda: canônica
                    with ui.column().classes("flex-1 items-center"):
                        ui.label("✦ Canônica atual").classes(
                            "text-amber-300 text-sm uppercase tracking-wider"
                        )
                        ui.image(estado.canonica["url"]).classes(
                            "w-full max-w-md rounded border-2 border-amber-700"
                        ).style("height: auto; object-fit: contain;")
                        ui.label(
                            f"{estado.canonica.get('modelo_ia', '?')} · "
                            f"{estado.canonica['criado_em'].strftime('%d/%m/%Y')}"
                        ).classes("text-zinc-500 text-xs italic")

                    # Direita: selecionada
                    with ui.column().classes("flex-1 items-center"):
                        if not img_selecionada:
                            ui.label("(nenhuma outra imagem ainda)").classes(
                                "text-zinc-500 italic"
                            )
                        else:
                            border_cls = CLASSES_BORDER_BY_STATUS.get(
                                img_selecionada["status"], "border-zinc-700"
                            )
                            text_cls = CLASSES_TEXT_BY_STATUS.get(
                                img_selecionada["status"], "text-zinc-300"
                            )
                            label_status = CORES_STATUS.get(
                                img_selecionada["status"], ("", "?")
                            )[1]
                            ui.label(label_status).classes(
                                f"{text_cls} text-sm uppercase tracking-wider"
                            )
                            ui.image(img_selecionada["url"]).classes(
                                f"w-full max-w-md rounded border-2 {border_cls}"
                            ).style("height: auto; object-fit: contain;")
                            ui.label(
                                f"{img_selecionada.get('modelo_ia', '?')} · "
                                f"{img_selecionada['criado_em'].strftime('%d/%m/%Y')}"
                            ).classes("text-zinc-500 text-xs italic")

        comparacao()

        # ─── GALERIA COMPLETA ───
        @ui.refreshable
        def galeria():
            total = len(estado.imagens)
            with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4"):
                with ui.row().classes("w-full items-baseline gap-3 mb-3"):
                    ui.label(f"Galeria ({total} imagens)").classes(
                        "text-amber-200 text-lg font-semibold"
                    )
                    ui.label(
                        "Ações: clicar em uma thumb compara · "
                        "✓ aprovar · ✦ promover canônica · ✕ aposentar · 🗑 deletar"
                    ).classes("text-zinc-500 text-xs italic")

                if not estado.imagens:
                    ui.label(
                        "Nenhuma imagem ainda. Use 'Gerar imagem' acima."
                    ).classes("text-zinc-400 italic")
                    return

                # Grid 4 colunas (responsivo)
                with ui.grid(columns=4).classes("w-full gap-3"):
                    for img in estado.imagens:
                        _render_card_imagem(img, npc_id, estado, galeria, comparacao)

        galeria()


# =============================================================================
# Card de uma imagem na galeria
# =============================================================================

def _render_card_imagem(
    img: dict,
    npc_id: int,
    estado: EstadoImagens,
    galeria_refresh,
    comparacao_refresh,
) -> None:
    """Renderiza UM card de imagem dentro da galeria."""
    label_status = CORES_STATUS.get(img["status"], ("", img["status"]))[1]
    border_cls = CLASSES_BORDER_BY_STATUS.get(img["status"], "border-zinc-700")
    border_hover_cls = CLASSES_BORDER_HOVER_BY_STATUS.get(
        img["status"], "hover:border-zinc-500"
    )
    text_cls = CLASSES_TEXT_BY_STATUS.get(img["status"], "text-zinc-300")

    with ui.card().classes(
        f"bg-zinc-900 border-2 {border_cls} p-2 gap-2 {border_hover_cls}"
    ):
        # Thumb (clicável pra selecionar pra comparação)
        def _selecionar_pra_comparar(img_id=img["id"]):
            estado.imagem_comparacao_id = img_id
            comparacao_refresh.refresh()
            ui.notify(
                "Selecionada pra comparação 2-up acima",
                type="info", position="bottom-right",
            )

        thumb = ui.image(img["url"]).classes(
            "w-full rounded cursor-pointer object-cover"
        ).style("aspect-ratio: 2/3;")
        thumb.on("click", lambda e, fid=img["id"]: _selecionar_pra_comparar(fid))

        # Status badge
        ui.label(label_status).classes(
            f"{text_cls} text-xs uppercase tracking-wider text-center"
        )

        # Metadados curtos
        modelo = img.get("modelo_ia") or "(sem modelo)"
        custo = float(img.get("custo_usd") or 0)
        ts = img["criado_em"].strftime("%d/%m %H:%M")
        ui.label(f"{modelo} · ${custo:.3f}").classes(
            "text-zinc-400 text-xs text-center"
        )
        ui.label(ts).classes("text-zinc-500 text-xs text-center")

        # Ações (botões)
        with ui.row().classes("w-full justify-center gap-1 flex-wrap"):
            # Promover canônica (se não for já)
            if img["status"] != "canonica":
                async def _promover(fid=img["id"]):
                    try:
                        await atualizar_status_imagem(fid, "canonica", npc_id)
                        ui.notify("✦ Promovida a canônica",
                                  type="positive", position="top")
                        await _recarregar_apos_acao(
                            npc_id, estado, galeria_refresh, comparacao_refresh
                        )
                    except Exception as e:
                        ui.notify(f"Erro: {e}", type="negative", position="top")

                ui.button(icon="star", on_click=_promover).props(
                    "flat dense round color=amber-7"
                ).tooltip("Promover a canônica")

            # Aprovar (se for rascunho)
            if img["status"] == "rascunho":
                async def _aprovar(fid=img["id"]):
                    try:
                        await atualizar_status_imagem(fid, "aprovada", npc_id)
                        ui.notify("✓ Aprovada", type="positive", position="top")
                        await _recarregar_apos_acao(
                            npc_id, estado, galeria_refresh, comparacao_refresh
                        )
                    except Exception as e:
                        ui.notify(f"Erro: {e}", type="negative", position="top")

                ui.button(icon="check", on_click=_aprovar).props(
                    "flat dense round color=green-7"
                ).tooltip("Aprovar")

            # Aposentar (se não for aposentada)
            if img["status"] != "aposentada":
                async def _aposentar(fid=img["id"]):
                    try:
                        await atualizar_status_imagem(fid, "aposentada", npc_id)
                        ui.notify("✕ Aposentada",
                                  type="warning", position="top")
                        await _recarregar_apos_acao(
                            npc_id, estado, galeria_refresh, comparacao_refresh
                        )
                    except Exception as e:
                        ui.notify(f"Erro: {e}", type="negative", position="top")

                ui.button(icon="archive", on_click=_aposentar).props(
                    "flat dense round color=red-7"
                ).tooltip("Aposentar")

            # Copiar prompt (se houver)
            if img.get("prompt_usado"):
                async def _copiar_prompt(prompt=img["prompt_usado"]):
                    # Escape pra JS string literal
                    safe = json.dumps(prompt or "")
                    js = f"navigator.clipboard.writeText({safe})"
                    try:
                        await ui.run_javascript(js)
                        ui.notify(
                            "Prompt copiado pra clipboard",
                            type="info", position="bottom-right",
                        )
                    except Exception as e:
                        ui.notify(f"Falha ao copiar: {e}",
                                  type="negative", position="top")

                ui.button(icon="content_copy", on_click=_copiar_prompt).props(
                    "flat dense round color=zinc-5"
                ).tooltip("Copiar prompt usado")

            # Deletar (com confirmação)
            async def _deletar(fid=img["id"], url=img["url"]):
                with ui.dialog() as confirm, ui.card().classes(
                    "bg-zinc-900 border border-red-700 p-4 gap-3"
                ):
                    ui.label(
                        "Deletar permanentemente esta imagem do banco e do R2?"
                    ).classes("text-zinc-200")
                    ui.label("(Não pode ser desfeito.)").classes(
                        "text-red-400 text-sm italic"
                    )
                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button("Cancelar", on_click=confirm.close).props(
                            "flat color=zinc-5"
                        )

                        async def _do_delete():
                            confirm.close()
                            try:
                                # Deleta do banco primeiro
                                url_apagada = await deletar_imagem_db(fid)
                                # Depois tenta deletar do R2 (best effort)
                                if url_apagada:
                                    try:
                                        await deletar_imagem_r2(url_apagada)
                                    except Exception as e_r2:
                                        ui.notify(
                                            f"Banco OK mas R2 falhou: {e_r2}",
                                            type="warning", position="top",
                                        )
                                ui.notify("Deletada", type="positive",
                                          position="top")
                                await _recarregar_apos_acao(
                                    npc_id, estado,
                                    galeria_refresh, comparacao_refresh,
                                )
                            except Exception as e:
                                ui.notify(f"Erro: {e}",
                                          type="negative", position="top")

                        ui.button("Deletar", on_click=_do_delete).props(
                            "color=red-7 unelevated"
                        )
                confirm.open()

            ui.button(icon="delete", on_click=_deletar).props(
                "flat dense round color=red-9"
            ).tooltip("Deletar permanentemente")


def _abrir_dialog_upload(
    npc_id,
    estado,
    galeria_refresh,
    comparacao_refresh,
    on_alterado,
):
    """Abre dialog pra upload de imagem externa (arquivo do PC).

    A imagem sobe pro R2 + salva no banco como 'rascunho'. Usuario depois
    promove/aprova/aposenta igual a uma imagem gerada pela IA.
    """
    with ui.dialog() as dialog, ui.card().classes(
        "bg-zinc-900 border border-zinc-700 p-6 gap-3 min-w-[500px]"
    ):
        ui.label("Upload de imagem externa").classes(
            "text-amber-200 text-xl font-semibold"
        )
        ui.label(
            "Envia uma imagem do teu computador (JPG, PNG ou WEBP, ate 5MB). "
            "Ela entra na galeria como 'rascunho' - tu decide depois se promove."
        ).classes("text-zinc-400 text-sm")

        rotulo_input = (
            ui.input(
                label="Rotulo narrativo (opcional)",
                placeholder="ex: referencia externa, edicao manual",
            )
            .props("outlined dense color=amber-8 dark")
            .classes("w-full")
        )

        status_label = ui.label("").classes("text-sm")

        async def _on_upload(e):
            """Callback do ui.upload - dispara quando arquivo e selecionado."""
            file = e.file
            file_bytes = await file.read()

            content_type = (
                getattr(file, 'content_type', None)
                or getattr(file, 'mime_type', None)
                or getattr(file, 'type', None)
            )

            if not content_type:
                fname = (
                    getattr(file, 'filename', None)
                    or getattr(file, 'name', None)
                    or ""
                ).lower()
                if fname.endswith(('.jpg', '.jpeg')):
                    content_type = "image/jpeg"
                elif fname.endswith('.png'):
                    content_type = "image/png"
                elif fname.endswith('.webp'):
                    content_type = "image/webp"
                else:
                    content_type = "application/octet-stream"

            tamanho_kb = len(file_bytes) / 1024
            status_label.text = f"Enviando {tamanho_kb:.0f} KB..."
            status_label.classes(replace="text-sm text-amber-300")

            try:
                url = await upload_imagem_npc(npc_id, file_bytes, content_type)

                rotulo = (rotulo_input.value or "").strip() or None
                imagem_id = await inserir_imagem_upload(npc_id, url, rotulo)

                ui.notify(
                    f"Imagem adicionada (ID {imagem_id})",
                    type="positive", position="top", timeout=4000,
                )
                dialog.close()

                estado.imagens = await listar_imagens_npc(npc_id)
                estado.canonica = await buscar_canonica_atual(npc_id)
                galeria_refresh.refresh()
                comparacao_refresh.refresh()
                await on_alterado()

            except ValueError as ex:
                status_label.text = f"Rejeitada: {ex}"
                status_label.classes(replace="text-sm text-red-400")
                ui.notify(f"Rejeitada: {ex}", type="negative", position="top")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                status_label.text = f"Erro: {ex}"
                status_label.classes(replace="text-sm text-red-400")
                ui.notify(f"Erro: {ex}", type="negative", position="top", timeout=8000)

        ui.upload(
            label="Selecionar arquivo",
            on_upload=_on_upload,
            max_file_size=5 * 1024 * 1024,
            auto_upload=True,
        ).props(
            "accept='image/jpeg,image/png,image/webp' "
            "color=amber-8 flat dense"
        ).classes("w-full mt-2")

        with ui.row().classes("w-full justify-end mt-2"):
            ui.button("Fechar", on_click=dialog.close).props(
                "flat color=zinc-5"
            )

    dialog.open()


async def _recarregar_apos_acao(
    npc_id: int,
    estado: EstadoImagens,
    galeria_refresh,
    comparacao_refresh,
) -> None:
    """Helper pra recarregar galeria + comparação após qualquer ação."""
    estado.imagens = await listar_imagens_npc(npc_id)
    estado.canonica = await buscar_canonica_atual(npc_id)
    galeria_refresh.refresh()
    comparacao_refresh.refresh()
