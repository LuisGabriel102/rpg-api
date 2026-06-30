"""
Página principal do Ateliê — Catedral do Alderyn (Módulo 4.6.4).

Rota: /oficina/atelie/{npc_id}

Layout:
  ┌──────────────────────────────────────────────────────────────┐
  │  Breadcrumb: Oficina / NPCs / [Nome] / Ateliê                │
  │  ┌─ Header com nome + camada + raça + atalhos ──────────────┐│
  │  └────────────────────────────────────────────────────────────┘│
  │                                                                 │
  │  [Aparência] [Imagens] [Variações] [Auditoria]                  │
  │  ────────────────────                                           │
  │  (conteúdo da sub-aba selecionada)                              │
  │                                                                 │
  └──────────────────────────────────────────────────────────────┘

Padrão NiceGUI:
  - aguardar_conexao_websocket() ANTES de queries pesadas (ver ui_helpers.py)
  - Try/except com painel de erro estilizado
  - Paleta zinc-900/zinc-100/amber-8 (consistente com Catedral)
"""

from __future__ import annotations

import traceback

from nicegui import ui

from ui_helpers import aguardar_conexao_websocket

from pages.atelie_queries import carregar_npc_completo
from pages.atelie_aparencia import render_aba_aparencia
from pages.atelie_imagens import render_aba_imagens
from pages.atelie_variacoes import render_aba_variacoes
from pages.atelie_auditoria import render_aba_auditoria


# =============================================================================
# RENDER PRINCIPAL — chamado pela rota em main.py
# =============================================================================

async def pagina_atelie(npc_id: int) -> None:
    """Renderiza a página completa do Ateliê pra um NPC.

    Args:
        npc_id: ID do NPC.
    """
    # FIX TIMEOUT NICEGUI (mesmo padrão de oficina_npcs_42.py)
    await aguardar_conexao_websocket(f"Carregando Ateliê do NPC #{npc_id}...")

    # Carregar NPC
    try:
        npc = await carregar_npc_completo(npc_id)
    except Exception as e:
        traceback.print_exc()
        with ui.column().classes(
            "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-4"
        ):
            ui.label(f"Erro ao carregar NPC {npc_id} no Ateliê").classes(
                "text-2xl text-red-400"
            )
            ui.label(str(e)).classes("text-sm text-zinc-400 font-mono")
            ui.button(
                "Voltar à lista",
                on_click=lambda: ui.navigate.to("/oficina/npcs"),
            ).props("color=amber-8")
        return

    if not npc:
        with ui.column().classes(
            "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 "
            "items-center justify-center gap-4"
        ):
            ui.label(f"NPC id={npc_id} não encontrado.").classes(
                "text-2xl text-zinc-400"
            )
            ui.button(
                "Voltar à lista",
                on_click=lambda: ui.navigate.to("/oficina/npcs"),
            ).props("color=amber-8")
        return

    # ─── LAYOUT PRINCIPAL ───
    nome = npc.get("nome") or f"NPC #{npc_id}"
    camada = npc.get("camada") or 3
    raca = npc.get("raca") or "?"

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-6 gap-4 max-w-7xl mx-auto"
    ):

        # Breadcrumb
        with ui.row().classes("items-center gap-2 text-sm"):
            ui.link("← Oficina", "/oficina").classes(
                "text-zinc-500 hover:text-amber-200"
            )
            ui.label("/").classes("text-zinc-600")
            ui.link("NPCs", "/oficina/npcs").classes(
                "text-zinc-500 hover:text-amber-200"
            )
            ui.label("/").classes("text-zinc-600")
            ui.link(
                nome, f"/oficina/npcs/{npc_id}",
            ).classes("text-zinc-500 hover:text-amber-200")
            ui.label("/").classes("text-zinc-600")
            ui.label("Ateliê").classes("text-amber-300 font-medium")

        # Header
        with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-1"):
                    with ui.row().classes("items-baseline gap-3"):
                        ui.label("Ateliê de Geração").classes(
                            "text-amber-200 text-2xl font-bold"
                        )
                        ui.label(f"— {nome}").classes(
                            "text-zinc-200 text-xl"
                        )
                    with ui.row().classes("items-center gap-3"):
                        camada_label = {
                            1: "Camada 1 · Protagonista",
                            2: "Camada 2 · Recorrente",
                            3: "Camada 3 · Cenário",
                        }.get(camada, f"Camada {camada}")
                        ui.label(camada_label).classes("text-zinc-400 text-sm")
                        ui.label("·").classes("text-zinc-600")
                        ui.label(raca).classes("text-zinc-400 text-sm")

                with ui.row().classes("items-center gap-2"):
                    ui.button(
                        "Voltar ao NPC", icon="arrow_back",
                        on_click=lambda: ui.navigate.to(f"/oficina/npcs/{npc_id}"),
                    ).props("flat color=amber-7")

        # ─── 4 SUB-ABAS ───
        with ui.tabs().classes("w-full") as tabs:
            tab_aparencia = ui.tab("Aparência", icon="face")
            tab_imagens = ui.tab("Imagens", icon="image")
            tab_variacoes = ui.tab("Variações", icon="layers")
            tab_auditoria = ui.tab("Auditoria", icon="receipt_long")

        # Recarregar tudo quando algo muda
        async def _on_alterado():
            """Callback quando algo muda — recarrega NPC pra refletir aparência atualizada."""
            nonlocal npc
            try:
                novo = await carregar_npc_completo(npc_id)
                if novo:
                    npc = novo
            except Exception:
                pass  # Não quebrar UI se reload falhar

        # Painéis das sub-abas
        with ui.tab_panels(tabs, value=tab_imagens).classes(
            "w-full bg-zinc-900"
        ):
            # ABA APARÊNCIA
            with ui.tab_panel(tab_aparencia):
                try:
                    await render_aba_aparencia(npc_id, npc, _on_alterado)
                except Exception as e:
                    traceback.print_exc()
                    ui.label(f"Erro ao renderizar Aparência: {e}").classes(
                        "text-red-400"
                    )

            # ABA IMAGENS (default — abre primeiro)
            with ui.tab_panel(tab_imagens):
                try:
                    await render_aba_imagens(npc_id, npc, _on_alterado)
                except Exception as e:
                    traceback.print_exc()
                    ui.label(f"Erro ao renderizar Imagens: {e}").classes(
                        "text-red-400"
                    )

            # ABA VARIAÇÕES
            with ui.tab_panel(tab_variacoes):
                try:
                    await render_aba_variacoes(npc_id, npc, _on_alterado)
                except Exception as e:
                    traceback.print_exc()
                    ui.label(f"Erro ao renderizar Variações: {e}").classes(
                        "text-red-400"
                    )

            # ABA AUDITORIA
            with ui.tab_panel(tab_auditoria):
                try:
                    await render_aba_auditoria(npc_id, npc)
                except Exception as e:
                    traceback.print_exc()
                    ui.label(f"Erro ao renderizar Auditoria: {e}").classes(
                        "text-red-400"
                    )
