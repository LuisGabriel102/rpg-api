"""
Sub-aba "Variações" do Ateliê — Catedral do Alderyn (Módulo 4.6.4).

CRUD de variações nomeadas de aparência:
  - "Almareth aposentado" (+6 anos, mais cabelo branco, postura mais curva)
  - "Almareth ferido" (corte na bochecha esquerda, olho roxo)
  - "Almareth em gala" (camisa limpa, sem avental)

Apenas UMA variação pode ser "prioritária" por NPC (constrainted via
índice único parcial idx_variacao_prioritaria_unica). Quando prioritária,
a sub-aba Imagens default usa ela ao gerar.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from nicegui import ui
import asyncpg

from pages.atelie_queries import (
    listar_variacoes_npc,
    criar_variacao,
    atualizar_variacao,
    deletar_variacao,
    marcar_variacao_prioritaria,
    desmarcar_variacao_prioritaria,
)


class EstadoVariacoes:
    """Estado da sub-aba Variações."""

    def __init__(self):
        self.variacoes: list[dict] = []


# =============================================================================
# RENDER PRINCIPAL
# =============================================================================

async def render_aba_variacoes(
    npc_id: int,
    dados_npc: dict,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Renderiza a sub-aba Variações."""
    estado = EstadoVariacoes()

    try:
        estado.variacoes = await listar_variacoes_npc(npc_id)
    except Exception as e:
        ui.label(f"Erro ao carregar variações: {e}").classes("text-red-400")
        return

    nome_npc = dados_npc.get("nome") or f"NPC #{npc_id}"

    with ui.column().classes("w-full gap-4"):

        # ─── HEADER ───
        with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4 gap-2"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Variações nomeadas").classes(
                    "text-amber-200 text-lg font-semibold"
                )
                ui.button(
                    "+ Nova variação",
                    on_click=lambda: _abrir_dialog_criar(
                        npc_id, estado, lista_refresh, on_alterado,
                    ),
                ).props("color=amber-8 unelevated")

            ui.label(
                "Cada variação é uma versão nomeada de aparência (ex: 'aposentado', "
                "'ferido', 'em gala'). Use a 'descrição da modificação' pra dizer "
                "o que muda em relação à âncora canônica. Marque uma como ★ prioritária "
                "pra ser usada por padrão ao gerar imagens."
            ).classes("text-zinc-400 text-sm")

        # ─── LISTA DE VARIAÇÕES ───
        @ui.refreshable
        def lista_refresh():
            if not estado.variacoes:
                with ui.card().classes(
                    "w-full bg-zinc-800/50 border border-dashed border-zinc-700 p-8"
                ):
                    ui.label("Nenhuma variação criada ainda.").classes(
                        "text-zinc-500 italic text-center"
                    )
                    ui.label(
                        f"Use o botão '+ Nova variação' acima pra criar a primeira "
                        f"versão alternativa de {nome_npc}."
                    ).classes("text-zinc-600 text-sm text-center")
                return

            for var in estado.variacoes:
                _render_card_variacao(
                    var, npc_id, estado, lista_refresh, on_alterado,
                )

        lista_refresh()


# =============================================================================
# Card de uma variação
# =============================================================================

def _render_card_variacao(
    var: dict,
    npc_id: int,
    estado: EstadoVariacoes,
    lista_refresh,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Renderiza UM card de variação."""
    # Tailwind purge-safe: classes completas hardcoded
    border_cls = (
        "border-amber-700" if var["e_uso_prioritario"] else "border-zinc-700"
    )

    with ui.card().classes(
        f"w-full bg-zinc-800 border-2 {border_cls} p-4 gap-2"
    ):
        # Header: nome + flags
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.label(var["nome_variacao"]).classes(
                    "text-amber-100 text-lg font-semibold"
                )
                if var["e_uso_prioritario"]:
                    ui.label("★ PRIORITÁRIA").classes(
                        "text-amber-400 text-xs uppercase tracking-wider"
                    )
                if var["e_permanente"]:
                    ui.label("✓ PERMANENTE").classes(
                        "text-zinc-400 text-xs uppercase tracking-wider"
                    )
                ui.label(
                    var["criado_em"].strftime("criada %d/%m/%Y")
                ).classes("text-zinc-500 text-xs italic")

            # Botões de ação
            with ui.row().classes("items-center gap-2"):
                # Toggle prioritária
                if var["e_uso_prioritario"]:
                    async def _desmarcar_pri(npc=npc_id):
                        try:
                            await desmarcar_variacao_prioritaria(npc)
                            ui.notify("Removida prioridade", type="info")
                            await _recarregar(npc, estado, lista_refresh, on_alterado)
                        except Exception as e:
                            ui.notify(f"Erro: {e}", type="negative", position="top")

                    ui.button(
                        "Remover ★", on_click=_desmarcar_pri,
                    ).props("flat dense color=amber-5")
                else:
                    async def _marcar_pri(vid=var["id"], npc=npc_id):
                        try:
                            await marcar_variacao_prioritaria(vid, npc)
                            ui.notify("★ Marcada prioritária", type="positive")
                            await _recarregar(npc, estado, lista_refresh, on_alterado)
                        except Exception as e:
                            ui.notify(f"Erro: {e}", type="negative", position="top")

                    ui.button(
                        "Tornar ★", on_click=_marcar_pri,
                    ).props("flat dense color=amber-7")

                # Editar
                ui.button(icon="edit", on_click=lambda v=var: _abrir_dialog_editar(
                    v, npc_id, estado, lista_refresh, on_alterado,
                )).props("flat dense round color=zinc-3").tooltip("Editar")

                # Deletar
                ui.button(icon="delete", on_click=lambda v=var: _confirmar_deletar(
                    v, npc_id, estado, lista_refresh, on_alterado,
                )).props("flat dense round color=red-7").tooltip("Deletar variação")

        # Contexto narrativo
        if var.get("contexto_narrativo"):
            ui.label(f"Contexto: {var['contexto_narrativo']}").classes(
                "text-zinc-400 text-sm italic"
            )

        # Descrição da modificação (campo principal)
        ui.label("Modificação:").classes(
            "text-zinc-500 text-xs uppercase tracking-wider mt-1"
        )
        ui.label(var["descricao_modificacao"]).classes(
            "text-zinc-200 text-sm leading-relaxed"
        )

        # Overrides (se houver)
        if var.get("wardrobe_override"):
            with ui.row().classes("w-full gap-2 items-baseline mt-1"):
                ui.label("Roupa:").classes("text-zinc-500 text-xs uppercase")
                ui.label(var["wardrobe_override"]).classes(
                    "text-zinc-300 text-sm flex-1"
                )

        if var.get("iluminacao_override"):
            with ui.row().classes("w-full gap-2 items-baseline mt-1"):
                ui.label("Iluminação:").classes("text-zinc-500 text-xs uppercase")
                ui.label(var["iluminacao_override"]).classes(
                    "text-zinc-300 text-sm flex-1"
                )


# =============================================================================
# Dialogs (criar / editar)
# =============================================================================

def _abrir_dialog_criar(
    npc_id: int,
    estado: EstadoVariacoes,
    lista_refresh,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Abre dialog pra criar nova variação."""
    _abrir_dialog_form(
        titulo="Nova variação",
        npc_id=npc_id,
        var_existente=None,
        estado=estado,
        lista_refresh=lista_refresh,
        on_alterado=on_alterado,
    )


def _abrir_dialog_editar(
    var: dict,
    npc_id: int,
    estado: EstadoVariacoes,
    lista_refresh,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Abre dialog pra editar variação existente."""
    _abrir_dialog_form(
        titulo=f"Editar: {var['nome_variacao']}",
        npc_id=npc_id,
        var_existente=var,
        estado=estado,
        lista_refresh=lista_refresh,
        on_alterado=on_alterado,
    )


def _abrir_dialog_form(
    titulo: str,
    npc_id: int,
    var_existente: dict | None,
    estado: EstadoVariacoes,
    lista_refresh,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Form genérico (criar ou editar)."""
    with ui.dialog() as dialog, ui.card().classes(
        "bg-zinc-900 border border-zinc-700 p-6 gap-3 min-w-[600px] max-w-[900px]"
    ):
        ui.label(titulo).classes(
            "text-amber-200 text-xl font-semibold"
        )

        # Campos
        inp_nome = (
            ui.input(
                label="Nome da variação *",
                placeholder="ex: aposentado, ferido, em gala",
                value=var_existente["nome_variacao"] if var_existente else "",
            )
            .props("outlined dense color=amber-8 dark")
            .classes("w-full")
        )

        inp_contexto = (
            ui.input(
                label="Contexto narrativo (opcional)",
                placeholder="ex: usado quando NPC perde Mesa Circular",
                value=var_existente["contexto_narrativo"] if var_existente else "",
            )
            .props("outlined dense color=amber-8 dark")
            .classes("w-full")
        )

        inp_modificacao = (
            ui.textarea(
                label="Descrição da modificação *",
                placeholder="ex: +6 anos, mais cabelo branco, postura ainda mais "
                            "curvada, olhos mais cansados, mãos trêmulas",
                value=var_existente["descricao_modificacao"] if var_existente else "",
            )
            .props("outlined dense color=amber-8 dark rows=4")
            .classes("w-full")
        )

        inp_wardrobe = (
            ui.input(
                label="Roupa override (opcional)",
                placeholder="ex: roupa simples sem avental",
                value=var_existente["wardrobe_override"] if var_existente else "",
            )
            .props("outlined dense color=amber-8 dark")
            .classes("w-full")
        )

        inp_iluminacao = (
            ui.input(
                label="Iluminação override (opcional)",
                placeholder="ex: luz cinza fria de janela, sem brasa",
                value=var_existente["iluminacao_override"] if var_existente else "",
            )
            .props("outlined dense color=amber-8 dark")
            .classes("w-full")
        )

        chk_permanente = (
            ui.checkbox(
                "Mudança permanente (cicatriz, perda de membro, etc — é canônico daqui em diante)",
                value=bool(var_existente["e_permanente"]) if var_existente else False,
            )
            .props("color=amber-8 dark dense")
            .classes("text-zinc-300 text-sm")
        )

        # Botões
        with ui.row().classes("w-full justify-end items-center gap-2 mt-2"):
            ui.button("Cancelar", on_click=dialog.close).props(
                "flat color=zinc-5"
            )

            async def _salvar():
                nome = (inp_nome.value or "").strip()
                modificacao = (inp_modificacao.value or "").strip()

                if not nome:
                    ui.notify("Nome é obrigatório",
                              type="negative", position="top")
                    return
                if not modificacao:
                    ui.notify("Descrição da modificação é obrigatória",
                              type="negative", position="top")
                    return

                btn_salvar.props("loading disabled")
                try:
                    if var_existente:
                        await atualizar_variacao(
                            variacao_id=var_existente["id"],
                            nome_variacao=nome,
                            descricao_modificacao=modificacao,
                            contexto_narrativo=(inp_contexto.value or "").strip(),
                            wardrobe_override=(inp_wardrobe.value or "").strip(),
                            iluminacao_override=(inp_iluminacao.value or "").strip(),
                            e_permanente=bool(chk_permanente.value),
                        )
                        ui.notify("Variação atualizada",
                                  type="positive", position="top")
                    else:
                        await criar_variacao(
                            npc_id=npc_id,
                            nome_variacao=nome,
                            descricao_modificacao=modificacao,
                            contexto_narrativo=(inp_contexto.value or "").strip(),
                            wardrobe_override=(inp_wardrobe.value or "").strip(),
                            iluminacao_override=(inp_iluminacao.value or "").strip(),
                            e_permanente=bool(chk_permanente.value),
                        )
                        ui.notify("Variação criada",
                                  type="positive", position="top")

                    dialog.close()
                    await _recarregar(npc_id, estado, lista_refresh, on_alterado)

                except asyncpg.UniqueViolationError:
                    ui.notify(
                        f"Já existe uma variação com nome '{nome}' pra esse NPC.",
                        type="negative", position="top",
                    )
                except Exception as e:
                    ui.notify(f"Erro: {e}", type="negative", position="top")
                finally:
                    btn_salvar.props(remove="loading disabled")

            btn_salvar = ui.button("Salvar", on_click=_salvar).props(
                "color=amber-8 unelevated"
            )

    dialog.open()


def _confirmar_deletar(
    var: dict,
    npc_id: int,
    estado: EstadoVariacoes,
    lista_refresh,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Confirma antes de deletar variação."""
    with ui.dialog() as confirm, ui.card().classes(
        "bg-zinc-900 border border-red-700 p-4 gap-3"
    ):
        ui.label(f"Deletar variação '{var['nome_variacao']}'?").classes(
            "text-zinc-200"
        )
        ui.label(
            "Imagens já geradas com esta variação ficarão órfãs (variacao_id "
            "vira NULL), mas não são deletadas. Não pode ser desfeito."
        ).classes("text-red-400 text-sm italic")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", on_click=confirm.close).props(
                "flat color=zinc-5"
            )

            async def _do_delete():
                confirm.close()
                try:
                    await deletar_variacao(var["id"])
                    ui.notify("Variação deletada",
                              type="positive", position="top")
                    await _recarregar(npc_id, estado, lista_refresh, on_alterado)
                except Exception as e:
                    ui.notify(f"Erro: {e}", type="negative", position="top")

            ui.button("Deletar", on_click=_do_delete).props(
                "color=red-7 unelevated"
            )

    confirm.open()


async def _recarregar(
    npc_id: int,
    estado: EstadoVariacoes,
    lista_refresh,
    on_alterado: Callable[[], Awaitable[None]],
) -> None:
    """Recarrega lista após qualquer mutação."""
    estado.variacoes = await listar_variacoes_npc(npc_id)
    lista_refresh.refresh()
    await on_alterado()
