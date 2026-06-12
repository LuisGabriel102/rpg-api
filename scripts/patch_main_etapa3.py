"""
patch_main_etapa3.py - Etapa 3: pagina de detalhe /oficina/estrelas/{id}.

Duas mudancas:
  1. Substituir o click notify em _render_card_estrela por navegacao real
  2. Adicionar helpers + pagina de detalhe antes do MOUNT

Idempotente via sentinela "def pagina_estrela_detalhe".
"""
from pathlib import Path
import sys

MAIN = Path("main.py")
SENTINELA = "def pagina_estrela_detalhe"

# --- Substituicao 1: click handler do card ---
CLICK_OLD = """    ).on(
        "click",
        lambda nome=e["nome"]: ui.notify(
            f"Astro {nome}: pagina de habilidades chega na Etapa 3.",
            type="info",
            position="top",
        ),
    ):"""

CLICK_NEW = """    ).on(
        "click",
        lambda eid=e["id"]: ui.navigate.to(f"/oficina/estrelas/{eid}"),
    ):"""

# --- Substituicao 2: rodape da tela de estrelas ---
FOOTER_OLD = '''"Modulo 5.2 OK. Pagina de habilidades (100 por estrela) "
                "chega na Etapa 3."'''
FOOTER_NEW = '''"Módulo 5.4 OK. Clique numa estrela pra ver suas 100 habilidades."'''

# --- Insercao: helpers + pagina antes do MOUNT ---
ANCORA = "# MOUNT NICEGUI NO APP FASTAPI"

NOVO_BLOCO = '''# ====================================================================
# === ESTRELA DETALHE - ROTAS (Módulo 5.4) ===
# ====================================================================

_CAT_LABELS = {
    1: ("Raras", "amber-700", "auto_awesome"),
    2: ("Médias", "amber-500", "star_half"),
    3: ("Comuns", "zinc-500", "star_outline"),
}


async def _buscar_estrela_por_id(estrela_id: int) -> dict | None:
    """Busca uma estrela pelo id. Retorna None se nao existir."""
    async with get_session() as session:
        result = await session.exec(
            select(RefEstrelasNascimento)
            .where(RefEstrelasNascimento.id == estrela_id)
        )
        e = result.first()
        if not e:
            return None
        return {
            "id": e.id,
            "nome": e.nome,
            "epiteto": e.epiteto,
            "lema": e.lema,
            "atributos": e.atributos_primarios,
            "pct_1": e.pct_primeira_cat,
            "pct_2": e.pct_segunda_cat,
            "pct_3": e.pct_terceira_cat,
            "lendaria_nome": e.habilidade_100_nome,
        }


async def _buscar_habilidades_estrela(
    estrela_id: int,
) -> dict[int, list[dict]]:
    """
    Busca as 100 habilidades de uma estrela, agrupadas por categoria.

    Retorna {1: [...], 2: [...], 3: [...]}.
    """
    async with get_session() as session:
        result = await session.exec(
            select(RefHabilidadesEstrela)
            .where(RefHabilidadesEstrela.estrela_id == estrela_id)
            .order_by(RefHabilidadesEstrela.numero_d100)
        )
        habs = result.all()

    agrupadas: dict[int, list[dict]] = {1: [], 2: [], 3: []}
    for h in habs:
        agrupadas.setdefault(h.categoria, []).append({
            "d100": h.numero_d100,
            "nome": h.nome,
            "descricao": h.descricao_completa,
            "categoria": h.categoria,
            "tem_preco": h.tem_preco,
            "lendaria": h.numero_d100 == 100,
        })
    return agrupadas


def _render_habilidade(h: dict) -> None:
    """Renderiza uma habilidade individual."""
    is_lend = h["lendaria"]
    is_preco = h["tem_preco"]

    border = "border-amber-600" if is_lend else "border-zinc-700"
    bg = "bg-zinc-750" if not is_lend else "bg-zinc-800"

    with ui.card().classes(
        f"w-full {bg} border {border} p-4 gap-2"
    ).props("flat"):
        # Linha do cabecalho: d100 + nome + badges
        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
            ui.badge(
                f"d{h['d100']:02d}",
                color="amber-8" if is_lend else "zinc-6",
            ).props("rounded")

            nome_display = h["nome"]
            nome_cls = (
                "text-base font-bold text-amber-200"
                if is_lend
                else "text-base font-semibold text-zinc-200"
            )
            ui.label(nome_display).classes(nome_cls)

            if is_preco:
                ui.icon("local_fire_department", size="1.2rem").classes(
                    "text-orange-400"
                ).tooltip("Esta habilidade cobra um preco")
            if is_lend:
                ui.badge("LENDARIA", color="amber-9").props("rounded")

        # Descricao com expand/collapse
        desc = h["descricao"]
        if len(desc) <= 250:
            ui.label(desc).classes(
                "text-sm text-zinc-300 whitespace-pre-line leading-relaxed"
            )
        else:
            trecho = desc[:220].rsplit(" ", 1)[0] + "..."
            desc_lbl = ui.label(trecho).classes(
                "text-sm text-zinc-300 whitespace-pre-line leading-relaxed"
            )
            expandido = {"v": False}

            def toggle(
                lbl=desc_lbl, full=desc, short=trecho, state=expandido
            ):
                state["v"] = not state["v"]
                lbl.set_text(full if state["v"] else short)
                btn_expand.set_text(
                    "ver menos" if state["v"] else "ver mais..."
                )

            btn_expand = ui.button(
                "ver mais...", on_click=toggle
            ).props("flat dense size=sm color=amber-4").classes("self-start")


@ui.page("/oficina/estrelas/{estrela_id}")
async def pagina_estrela_detalhe(estrela_id: int):
    """Pagina de detalhe de uma estrela com suas 100 habilidades."""
    estrela = await _buscar_estrela_por_id(estrela_id)

    if not estrela:
        with ui.column().classes(
            "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 items-center "
            "justify-center gap-4"
        ):
            ui.label("Estrela nao encontrada.").classes(
                "text-2xl text-zinc-400"
            )
            ui.button(
                "Voltar", on_click=lambda: ui.navigate.to("/oficina/estrelas")
            ).props("color=amber-8")
        return

    habs_por_cat = await _buscar_habilidades_estrela(estrela_id)

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-6"
    ):
        # === Header ===
        with ui.row().classes("w-full items-start justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina/estrelas"),
                ).props("flat round dense color=amber-2")

                with ui.column().classes("gap-0"):
                    with ui.row().classes("items-baseline gap-3"):
                        ui.label(estrela["nome"]).classes(
                            "text-4xl font-bold text-amber-200 tracking-wide"
                        )
                        ui.label(estrela["epiteto"]).classes(
                            "text-xl text-zinc-400 italic"
                        )
                    ui.label(
                        f'\u201c{estrela["lema"]}\u201d'
                    ).classes("text-sm text-zinc-300 italic mt-1")

        # === Stats compactos ===
        with ui.row().classes("w-full items-center gap-6 flex-wrap"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("fitness_center", size="1rem").classes("text-zinc-500")
                ui.label(estrela["atributos"]).classes(
                    "text-sm font-mono text-zinc-400"
                )
            with ui.row().classes("items-center gap-4"):
                ui.label(
                    f'Raras {estrela["pct_1"]}%'
                ).classes("text-xs font-mono text-amber-300")
                ui.label(
                    f'Medias {estrela["pct_2"]}%'
                ).classes("text-xs font-mono text-zinc-500")
                ui.label(
                    f'Comuns {estrela["pct_3"]}%'
                ).classes("text-xs font-mono text-zinc-600")

        ui.separator().classes("bg-zinc-700")

        # === 3 secoes por categoria ===
        for cat in [1, 2, 3]:
            label_cat, cor_cat, icone_cat = _CAT_LABELS[cat]
            habs = habs_por_cat.get(cat, [])
            n = len(habs)

            with ui.expansion(
                f"Categoria {cat} \u2014 {label_cat} ({n} habilidades)",
                icon=icone_cat,
                value=(cat <= 2),
            ).classes(
                "w-full bg-zinc-800 rounded mb-2"
            ).props("dense header-class=text-amber-100"):
                with ui.column().classes("w-full gap-3 p-2"):
                    if not habs:
                        ui.label("Nenhuma habilidade nesta categoria.").classes(
                            "text-zinc-500 italic"
                        )
                    else:
                        for h in habs:
                            _render_habilidade(h)

        # === Rodape ===
        with ui.row().classes("w-full justify-center mt-auto pt-8"):
            total = sum(len(v) for v in habs_por_cat.values())
            ui.label(
                f"Módulo 5.4 OK. {total} habilidades de {estrela['nome']}."
            ).classes("text-xs text-zinc-600 italic")


'''


def main() -> int:
    if not MAIN.exists():
        print(f"[ERRO] {MAIN} nao encontrado.")
        return 1

    conteudo = MAIN.read_text(encoding="utf-8")
    tam_antes = len(conteudo)

    if SENTINELA in conteudo:
        print("=" * 72)
        print("  [IDEMPOTENTE] Etapa 3 ja aplicada.")
        print(f"  Tamanho atual: {tam_antes} bytes")
        print("=" * 72)
        return 0

    # --- Passo 1: substituir click handler ---
    if CLICK_OLD not in conteudo:
        print("[ERRO 1] Click handler antigo nao encontrado.")
        print(f"  preview: {CLICK_OLD[:80]!r}")
        return 2
    conteudo = conteudo.replace(CLICK_OLD, CLICK_NEW, 1)
    print("  [1] Click handler atualizado: navega pra /oficina/estrelas/{id}")

    # --- Passo 2: substituir rodape ---
    if FOOTER_OLD not in conteudo:
        print("[ERRO 2] Rodape antigo nao encontrado.")
        return 3
    conteudo = conteudo.replace(FOOTER_OLD, FOOTER_NEW, 1)
    print("  [2] Rodape atualizado: Modulo 5.4")

    # --- Passo 3: inserir bloco antes do MOUNT ---
    if ANCORA not in conteudo:
        print(f"[ERRO 3] Ancora nao encontrada: {ANCORA!r}")
        return 4

    linhas = conteudo.split("\n")
    idx_ancora = None
    for i, linha in enumerate(linhas):
        if ANCORA in linha:
            idx_ancora = i
            break

    idx_inicio = idx_ancora
    while idx_inicio > 0 and not linhas[idx_inicio - 1].startswith("# ===="):
        idx_inicio -= 1
    idx_inicio -= 1

    linhas_novas = (
        linhas[:idx_inicio]
        + NOVO_BLOCO.split("\n")
        + linhas[idx_inicio:]
    )
    conteudo = "\n".join(linhas_novas)

    MAIN.write_text(conteudo, encoding="utf-8")
    tam_depois = len(conteudo)

    print(f"  [3] Bloco de detalhe inserido ({len(NOVO_BLOCO)} chars)")
    print()
    print("=" * 72)
    print(f"  [OK] Etapa 3 aplicada com sucesso.")
    print(f"  Tamanho antes:  {tam_antes:>6} bytes")
    print(f"  Tamanho depois: {tam_depois:>6} bytes ({tam_depois - tam_antes:+d})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())