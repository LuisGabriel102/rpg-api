"""
patch_main_estrelas.py - Adiciona helper + rota /oficina/estrelas ao main.py.

Duas mudancas:
  1. Import de models: adiciona RefEstrelasNascimento, RefHabilidadesEstrela
  2. Inserta bloco de rotas antes de "# MOUNT NICEGUI NO APP FASTAPI"

Idempotente via sentinela. Se ja aplicado, nao faz nada.
"""
from pathlib import Path
import sys

MAIN = Path("main.py")
SENTINELA = "# === ESTRELAS DO VEU - ROTAS (Modulo 5.2) ==="
IMPORT_ANTIGO = "from models import Npcs"
IMPORT_NOVO = "from models import Npcs, RefEstrelasNascimento, RefHabilidadesEstrela"
ANCORA_INSERCAO = "# MOUNT NICEGUI NO APP FASTAPI"

NOVAS_ROTAS = '''# ====================================================================
# === ESTRELAS DO VEU - ROTAS (Modulo 5.2) ===
# ====================================================================

async def _buscar_estrelas() -> list[dict]:
    """Busca as 12 estrelas ordenadas por id com tudo que o card precisa."""
    async with get_session() as session:
        statement = select(RefEstrelasNascimento).order_by(
            RefEstrelasNascimento.id
        )
        result = await session.exec(statement)
        estrelas = result.all()
    return [
        {
            "id": e.id,
            "nome": e.nome,
            "epiteto": e.epiteto,
            "lema": e.lema,
            "atributos": e.atributos_primarios,
            "pct_1": e.pct_primeira_cat,
            "pct_2": e.pct_segunda_cat,
            "pct_3": e.pct_terceira_cat,
            "lendaria": e.habilidade_100_nome,
        }
        for e in estrelas
    ]


def _render_card_estrela(e: dict) -> None:
    """Renderiza um card individual de estrela no grid."""
    with ui.card().classes(
        "w-full bg-zinc-800 border border-zinc-700 p-5 cursor-pointer "
        "hover:border-amber-700 transition-colors gap-3"
    ).on(
        "click",
        lambda nome=e["nome"]: ui.notify(
            f"Astro {nome}: pagina de habilidades chega na Etapa 3.",
            type="info",
            position="top",
        ),
    ):
        # Cabecalho: nome + epiteto
        with ui.column().classes("w-full gap-0"):
            ui.label(e["nome"]).classes(
                "text-2xl font-bold text-amber-200 tracking-wide"
            )
            ui.label(e["epiteto"]).classes(
                "text-sm text-zinc-400 italic"
            )

        # Lema
        ui.label(f"\u201c{e[\u0027lema\u0027]}\u201d").classes(
            "text-xs text-zinc-300 italic leading-snug"
        )

        # Atributos primarios
        with ui.row().classes("w-full items-center gap-2"):
            ui.icon("fitness_center", size="1rem").classes("text-zinc-500")
            ui.label(e["atributos"]).classes(
                "text-xs font-mono text-zinc-400"
            )

        # Distribuicao visual
        with ui.column().classes("w-full gap-1"):
            ui.label("Distribuicao").classes(
                "text-xs uppercase tracking-wider text-zinc-500"
            )
            with ui.row().classes("w-full items-center gap-0 h-2"):
                ui.element("div").classes(
                    "h-2 bg-amber-700 rounded-l"
                ).style(f"width: {e[\u0027pct_1\u0027]}%")
                ui.element("div").classes("h-2 bg-amber-500").style(
                    f"width: {e[\u0027pct_2\u0027]}%"
                )
                ui.element("div").classes(
                    "h-2 bg-amber-300 rounded-r"
                ).style(f"width: {e[\u0027pct_3\u0027]}%")
            with ui.row().classes("w-full justify-between"):
                ui.label(f"Raras {e[\u0027pct_1\u0027]}%").classes(
                    "text-xs text-amber-300 font-mono"
                )
                ui.label(f"Medias {e[\u0027pct_2\u0027]}%").classes(
                    "text-xs text-zinc-500 font-mono"
                )
                ui.label(f"Comuns {e[\u0027pct_3\u0027]}%").classes(
                    "text-xs text-zinc-600 font-mono"
                )

        ui.separator().classes("bg-zinc-700")

        # Lendaria (d100=100)
        with ui.column().classes("w-full gap-0"):
            ui.label("Lendaria (d100=100)").classes(
                "text-xs uppercase tracking-wider text-zinc-500"
            )
            ui.label(e["lendaria"]).classes(
                "text-sm text-amber-200 font-semibold italic"
            )


@ui.page("/oficina/estrelas")
async def pagina_estrelas():
    """Grid 4x3 das 12 estrelas do Veu. Primeira tela real da Catedral."""
    estrelas = await _buscar_estrelas()

    with ui.column().classes(
        "w-full min-h-screen bg-zinc-900 text-zinc-100 p-8 gap-6"
    ):
        # Header com botao voltar
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/oficina"),
                ).props("flat round dense color=amber-2")

                with ui.column().classes("gap-0"):
                    ui.label("Estrelas do Veu").classes(
                        "text-3xl font-bold text-amber-200"
                    )
                    ui.label(
                        f"{len(estrelas)} astros sob os quais as almas nascem"
                    ).classes("text-sm text-zinc-400 italic")

        ui.separator().classes("bg-zinc-700")

        # Grid responsivo 4x3
        with ui.element("div").classes(
            "w-full grid grid-cols-1 md:grid-cols-2 "
            "lg:grid-cols-3 xl:grid-cols-4 gap-4"
        ):
            for e in estrelas:
                _render_card_estrela(e)

        with ui.row().classes("w-full justify-center mt-auto pt-8"):
            ui.label(
                "Modulo 5.2 OK. Pagina de habilidades (100 por estrela) "
                "chega na Etapa 3."
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
        print("  [IDEMPOTENTE] Rotas ja existem em main.py. Nada a fazer.")
        print(f"  Tamanho atual: {tam_antes} bytes")
        print("=" * 72)
        return 0

    # --- Passo 1: atualizar import ---
    if IMPORT_ANTIGO not in conteudo:
        print(f"[ERRO] Linha de import nao encontrada: {IMPORT_ANTIGO!r}")
        return 2
    conteudo = conteudo.replace(IMPORT_ANTIGO, IMPORT_NOVO, 1)
    print(f"  [1] Import atualizado: adicionadas 2 classes de estrelas")

    # --- Passo 2: inserir bloco de rotas antes da ancora ---
    if ANCORA_INSERCAO not in conteudo:
        print(f"[ERRO] Ancora nao encontrada: {ANCORA_INSERCAO!r}")
        return 3

    # Busca a linha inteira que comeca com # ======== antes da ancora
    linhas = conteudo.split("\n")
    idx_ancora = None
    for i, linha in enumerate(linhas):
        if ANCORA_INSERCAO in linha:
            idx_ancora = i
            break

    # Volta pra linha anterior de "=" separadora
    idx_inicio_bloco = idx_ancora
    while idx_inicio_bloco > 0 and not linhas[idx_inicio_bloco - 1].startswith("# ===="):
        idx_inicio_bloco -= 1
    idx_inicio_bloco -= 1  # inclui a linha de "===="

    # Inserta as novas rotas antes da linha de separacao
    linhas_novas = (
        linhas[:idx_inicio_bloco]
        + NOVAS_ROTAS.split("\n")
        + linhas[idx_inicio_bloco:]
    )
    conteudo_novo = "\n".join(linhas_novas)

    MAIN.write_text(conteudo_novo, encoding="utf-8")
    tam_depois = len(conteudo_novo)

    print(f"  [2] Bloco de rotas inserido ({len(NOVAS_ROTAS)} chars)")
    print()
    print("=" * 72)
    print(f"  [OK] main.py patched com sucesso.")
    print(f"  Tamanho antes:  {tam_antes:>6} bytes")
    print(f"  Tamanho depois: {tam_depois:>6} bytes ({tam_depois - tam_antes:+d})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())