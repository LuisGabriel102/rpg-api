"""
Sub-aba "Auditoria" do Ateliê — Catedral do Alderyn (Módulo 4.6.4).

Mostra histórico completo de prompts gerados pra um NPC:
  - Stats agregados (total gasto, taxa de sucesso, etc)
  - Tabela com últimas 50 gerações (modelo, status, custo, duração, data)
  - Detalhe expansível: prompt completo + erro (se houver)
  - Botão copy clipboard pro prompt
"""

from __future__ import annotations

import json

from nicegui import ui

from pages.atelie_queries import (
    listar_auditoria_npc,
    estatisticas_custo_npc,
)


# =============================================================================
# RENDER PRINCIPAL
# =============================================================================

async def render_aba_auditoria(npc_id: int, dados_npc: dict) -> None:
    """Renderiza a sub-aba Auditoria."""
    try:
        stats = await estatisticas_custo_npc(npc_id)
        registros = await listar_auditoria_npc(npc_id, limite=100)
    except Exception as e:
        ui.label(f"Erro ao carregar auditoria: {e}").classes("text-red-400")
        return

    nome_npc = dados_npc.get("nome") or f"NPC #{npc_id}"

    with ui.column().classes("w-full gap-4"):

        # ─── STATS AGREGADOS ───
        with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4"):
            ui.label(f"Estatísticas — {nome_npc}").classes(
                "text-amber-200 text-lg font-semibold mb-3"
            )

            with ui.grid(columns=4).classes("w-full gap-3"):
                _card_stat(
                    "Total gasto",
                    f"${stats['total_gasto']:.3f}",
                    "USD acumulado neste NPC",
                    "amber",
                )
                _card_stat(
                    "Total de gerações",
                    str(stats["total_geracoes"]),
                    "tentativas registradas",
                    "zinc",
                )
                _card_stat(
                    "Sucessos",
                    str(stats["sucesso_count"]),
                    f"{_pct(stats['sucesso_count'], stats['total_geracoes'])}%",
                    "green",
                )
                _card_stat(
                    "Falhas",
                    str(stats["falha_count"]),
                    f"{_pct(stats['falha_count'], stats['total_geracoes'])}%",
                    "red",
                )

        # ─── TABELA DE HISTÓRICO ───
        with ui.card().classes("w-full bg-zinc-800 border border-zinc-700 p-4"):
            with ui.row().classes("w-full items-baseline gap-3 mb-3"):
                ui.label(f"Histórico (últimas {len(registros)} gerações)").classes(
                    "text-amber-200 text-lg font-semibold"
                )
                ui.label(
                    "Clique numa linha pra ver o prompt completo"
                ).classes("text-zinc-500 text-xs italic")

            if not registros:
                ui.label(
                    "Nenhuma geração registrada ainda. Use a aba 'Imagens' "
                    "pra gerar a primeira."
                ).classes("text-zinc-500 italic")
                return

            # Header da tabela
            with ui.element("div").classes(
                "w-full grid grid-cols-12 gap-2 text-xs uppercase tracking-wider "
                "text-zinc-500 border-b border-zinc-700 pb-2"
            ):
                ui.label("Data").classes("col-span-2")
                ui.label("Modelo").classes("col-span-2")
                ui.label("Status").classes("col-span-2")
                ui.label("Custo").classes("col-span-1 text-right")
                ui.label("Tempo").classes("col-span-1 text-right")
                ui.label("Tamanho").classes("col-span-1 text-right")
                ui.label("").classes("col-span-3")  # estágio falha (se houver)

            # Linhas
            for reg in registros:
                _render_linha_auditoria(reg)


# =============================================================================
# HELPERS
# =============================================================================

def _pct(parte: int, total: int) -> str:
    """Calcula porcentagem segura (sem division by zero)."""
    if not total:
        return "0"
    return f"{(parte / total * 100):.0f}"


def _card_stat(label: str, valor: str, sub: str, cor: str) -> None:
    """Card pequeno de estatística."""
    # Tailwind purge-safe: classes hardcoded
    BORDER_CLS = {
        "amber": "border-amber-700",
        "zinc":  "border-zinc-700",
        "green": "border-green-700",
        "red":   "border-red-700",
    }
    LABEL_CLS = {
        "amber": "text-amber-300",
        "zinc":  "text-zinc-300",
        "green": "text-green-300",
        "red":   "text-red-300",
    }
    VALOR_CLS = {
        "amber": "text-amber-100",
        "zinc":  "text-zinc-100",
        "green": "text-green-100",
        "red":   "text-red-100",
    }
    border = BORDER_CLS.get(cor, "border-zinc-700")
    label_color = LABEL_CLS.get(cor, "text-zinc-300")
    valor_color = VALOR_CLS.get(cor, "text-zinc-100")

    with ui.card().classes(
        f"bg-zinc-900 border {border} p-3 gap-1 items-center"
    ):
        ui.label(label).classes(
            f"{label_color} text-xs uppercase tracking-wider"
        )
        ui.label(valor).classes(
            f"{valor_color} text-2xl font-bold"
        )
        ui.label(sub).classes("text-zinc-500 text-xs italic")


def _render_linha_auditoria(reg: dict) -> None:
    """Renderiza UMA linha de auditoria (com expander pra ver prompt)."""
    # Mapa hardcoded pra evitar Tailwind purge issues
    STATUS_LABEL = {
        "success":  "✓ sucesso",
        "failed":   "✗ falhou",
        "rejected": "⊘ rejeitado",
    }
    STATUS_TEXT_CLS = {
        "success":  "text-green-300",
        "failed":   "text-red-300",
        "rejected": "text-amber-300",
    }
    label_st = STATUS_LABEL.get(reg["status"], reg["status"])
    text_cls = STATUS_TEXT_CLS.get(reg["status"], "text-zinc-300")

    ts = reg["criado_em"]
    modelo = reg.get("modelo_ia") or "?"
    custo = float(reg.get("custo_usd") or 0)
    duracao_ms = reg.get("duracao_ms") or 0
    duracao_str = f"{duracao_ms / 1000:.1f}s" if duracao_ms else "—"
    tamanho = reg.get("tamanho_prompt") or 0
    tamanho_str = f"{tamanho}c" if tamanho else "—"

    # Texto do header da expansão (uma linha resumida)
    header_text = (
        f"{ts.strftime('%d/%m %H:%M')}  ·  {modelo}  ·  {label_st}  "
        f"·  ${custo:.3f}  ·  {duracao_str}  ·  {tamanho_str}"
    )
    if reg["status"] == "failed" and reg.get("estagio_falha"):
        header_text += f"  ·  falha em: {reg['estagio_falha']}"

    with ui.expansion(header_text).classes(
        f"w-full bg-zinc-900 border-b border-zinc-800 {text_cls}"
    ).props("dense dark"):
        # Conteúdo expandido (prompt completo + ações)
        with ui.column().classes("w-full p-3 gap-2 bg-zinc-950"):
            ui.label("Prompt usado:").classes(
                "text-zinc-500 text-xs uppercase tracking-wider"
            )

            prompt = reg.get("texto_prompt") or "(prompt vazio)"

            with ui.element("pre").classes(
                "w-full bg-black border border-zinc-800 rounded p-3 "
                "text-zinc-300 text-xs font-mono whitespace-pre-wrap "
                "max-h-64 overflow-auto"
            ):
                ui.label(prompt)

            # Ação: copiar prompt
            async def _copiar(p=prompt):
                safe = json.dumps(p or "")
                js = f"navigator.clipboard.writeText({safe})"
                try:
                    await ui.run_javascript(js)
                    ui.notify(
                        "Prompt copiado",
                        type="info", position="bottom-right",
                    )
                except Exception as e:
                    ui.notify(f"Falha ao copiar: {e}",
                              type="negative", position="top")

            with ui.row().classes("w-full justify-end mt-2"):
                ui.button(
                    "Copiar prompt", icon="content_copy", on_click=_copiar,
                ).props("flat dense color=amber-7")
