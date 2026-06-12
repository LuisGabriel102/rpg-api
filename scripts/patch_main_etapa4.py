"""
patch_main_etapa4.py - Etapa 4 do Modulo 5: polish + home.

Tres mudancas em main.py:
  1. Home /oficina: adiciona card clicavel pra /oficina/estrelas
     (vira grid de 2 cards: NPCs + Estrelas)
  2. Acentos corrigidos: "Veu" -> "Véu", "Distribuicao" -> "Distribuição",
     "Medias" -> "Médias", "Lendaria" -> "Lendária"
  3. Altura igual dos cards no grid (h-full + flex flex-col + mt-auto)

Adiciona helper _contar_estrelas_total() para o card da home.

Idempotente via sentinela "Modulo 5.3" no comment do novo helper.
"""
from pathlib import Path
import sys

MAIN = Path("main.py")
SENTINELA = "def _contar_estrelas_total"


# ===========================================================================
# AS 10 SUBSTITUICOES
# ===========================================================================

# --- 1. Adicionar busca de total_estrelas logo apos total_npcs na home ---
REP_1_OLD = """async def pagina_oficina():
    total_npcs = await _contar_npcs_total()
"""
REP_1_NEW = """async def pagina_oficina():
    total_npcs = await _contar_npcs_total()
    total_estrelas = await _contar_estrelas_total()
"""

# --- 2. Substituir card unico dos NPCs por grid de 2 cards ---
REP_2_OLD = """        with ui.card().classes(
            "w-full max-w-2xl bg-zinc-800 border border-zinc-700 p-6 cursor-pointer "
            "hover:border-amber-700 transition-colors"
        ).on("click", lambda: ui.navigate.to("/oficina/npcs")):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-1"):
                    ui.label("NPCs cadastrados").classes(
                        "text-sm uppercase tracking-wider text-zinc-400"
                    )
                    ui.label(str(total_npcs)).classes(
                        "text-6xl font-bold text-amber-200"
                    )
                ui.icon("arrow_forward", size="2rem").classes("text-zinc-500")

            if total_npcs == 0:
                ui.label("O Alderyn ainda nao tem rostos.").classes(
                    "text-zinc-500 italic mt-4"
                )
                ui.label("Clique aqui pra forjar a primeira alma.").classes(
                    "text-zinc-600 text-sm"
                )
            else:
                ui.label(f"{total_npcs} alma(s) caminham pelo mundo.").classes(
                    "text-zinc-400 mt-4"
                )"""

REP_2_NEW = """        # Grid de cards das secoes da Catedral
        with ui.row().classes("w-full gap-4 flex-wrap"):

            # --- Card: NPCs ---
            with ui.card().classes(
                "flex-1 min-w-[280px] bg-zinc-800 border border-zinc-700 p-6 "
                "cursor-pointer hover:border-amber-700 transition-colors"
            ).on("click", lambda: ui.navigate.to("/oficina/npcs")):
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.column().classes("gap-1"):
                        ui.label("NPCs cadastrados").classes(
                            "text-sm uppercase tracking-wider text-zinc-400"
                        )
                        ui.label(str(total_npcs)).classes(
                            "text-6xl font-bold text-amber-200"
                        )
                    ui.icon("person", size="2rem").classes("text-zinc-500")

                if total_npcs == 0:
                    ui.label("O Alderyn ainda não tem rostos.").classes(
                        "text-zinc-500 italic mt-4"
                    )
                    ui.label("Clique aqui pra forjar a primeira alma.").classes(
                        "text-zinc-600 text-sm"
                    )
                else:
                    ui.label(f"{total_npcs} alma(s) caminham pelo mundo.").classes(
                        "text-zinc-400 mt-4"
                    )

            # --- Card: Estrelas do Véu ---
            with ui.card().classes(
                "flex-1 min-w-[280px] bg-zinc-800 border border-zinc-700 p-6 "
                "cursor-pointer hover:border-amber-700 transition-colors"
            ).on("click", lambda: ui.navigate.to("/oficina/estrelas")):
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.column().classes("gap-1"):
                        ui.label("Estrelas do Véu").classes(
                            "text-sm uppercase tracking-wider text-zinc-400"
                        )
                        ui.label(str(total_estrelas)).classes(
                            "text-6xl font-bold text-amber-200"
                        )
                    ui.icon("auto_awesome", size="2rem").classes("text-zinc-500")

                ui.label("Astros sob os quais as almas nascem.").classes(
                    "text-zinc-400 mt-4"
                )
                ui.label(
                    "Clique aqui pra ver os 12 astros, da Forja ao Trono."
                ).classes("text-zinc-600 text-sm")"""

# --- 3. Rodape da home ---
REP_3_OLD = '''"Modulo 4.3 OK. Edicao chega na sub-fase 4.5."'''
REP_3_NEW = '''"Módulo 5.3 OK. Catedral ergue-se: NPCs + Estrelas online."'''

# --- 4. Subtitulo da tela de estrelas ---
REP_4_OLD = 'ui.label("Estrelas do Veu").classes('
REP_4_NEW = 'ui.label("Estrelas do Véu").classes('

# --- 5. Label "Distribuicao" no card ---
REP_5_OLD = 'ui.label("Distribuicao").classes('
REP_5_NEW = 'ui.label("Distribuição").classes('

# --- 6. Label "Medias" no card ---
REP_6_OLD = """ui.label(f"Medias {e['pct_2']}%").classes("""
REP_6_NEW = """ui.label(f"Médias {e['pct_2']}%").classes("""

# --- 7. Label "Lendaria (d100=100)" no card ---
REP_7_OLD = 'ui.label("Lendaria (d100=100)").classes('
REP_7_NEW = 'ui.label("Lendária (d100=100)").classes('

# --- 8. Altura igual: adicionar h-full flex flex-col no ui.card das estrelas ---
REP_8_OLD = '''    with ui.card().classes(
        "w-full bg-zinc-800 border border-zinc-700 p-5 cursor-pointer "
        "hover:border-amber-700 transition-colors gap-3"
    ).on('''
REP_8_NEW = '''    with ui.card().classes(
        "w-full h-full flex flex-col bg-zinc-800 border border-zinc-700 p-5 "
        "cursor-pointer hover:border-amber-700 transition-colors gap-3"
    ).on('''

# --- 9. mt-auto no separador antes da lendaria (empurra pro rodape) ---
REP_9_OLD = '''        ui.separator().classes("bg-zinc-700")

        # Lendaria (d100=100)'''
REP_9_NEW = '''        ui.separator().classes("bg-zinc-700 mt-auto")

        # Lendária (d100=100)'''

# --- 10. Adicionar helper _contar_estrelas_total() antes do _buscar_estrelas ---
REP_10_OLD = '''async def _buscar_estrelas() -> list[dict]:'''
REP_10_NEW = '''async def _contar_estrelas_total() -> int:  # Modulo 5.3
    """Conta total de estrelas (usado pelo card da home)."""
    async with get_session() as session:
        result = await session.exec(
            select(func.count()).select_from(RefEstrelasNascimento)
        )
        return result.one()


async def _buscar_estrelas() -> list[dict]:'''


REPLACES = [
    (REP_1_OLD, REP_1_NEW, "1. Adicionar total_estrelas na home"),
    (REP_2_OLD, REP_2_NEW, "2. Substituir card unico por grid de 2 cards"),
    (REP_3_OLD, REP_3_NEW, "3. Rodape da home -> Modulo 5.3"),
    (REP_4_OLD, REP_4_NEW, "4. Subtitulo: Veu -> Véu"),
    (REP_5_OLD, REP_5_NEW, "5. Label: Distribuicao -> Distribuição"),
    (REP_6_OLD, REP_6_NEW, "6. Label: Medias -> Médias"),
    (REP_7_OLD, REP_7_NEW, "7. Label: Lendaria -> Lendária"),
    (REP_8_OLD, REP_8_NEW, "8. h-full flex flex-col no card das estrelas"),
    (REP_9_OLD, REP_9_NEW, "9. mt-auto no separador da lendaria"),
    (REP_10_OLD, REP_10_NEW, "10. Adicionar helper _contar_estrelas_total"),
]


def main() -> int:
    if not MAIN.exists():
        print(f"[ERRO] {MAIN} nao encontrado.")
        return 1

    conteudo = MAIN.read_text(encoding="utf-8")
    tam_antes = len(conteudo)

    if SENTINELA in conteudo:
        print("=" * 72)
        print("  [IDEMPOTENTE] Etapa 4 ja aplicada. Nada a fazer.")
        print(f"  Tamanho atual: {tam_antes} bytes")
        print("=" * 72)
        return 0

    # Valida TODAS as substituicoes antes de aplicar qualquer uma
    print("  Validando substituicoes...")
    for i, (old, new, desc) in enumerate(REPLACES, 1):
        count = conteudo.count(old)
        if count == 0:
            print(f"  [ERRO {i}] Nao achou: {desc}")
            print(f"            OLD preview: {old[:80]!r}...")
            return 2
        if count > 1:
            print(f"  [ERRO {i}] Ambiguo ({count}x): {desc}")
            return 3

    # Aplica as substituicoes em ordem
    print()
    print("  Aplicando substituicoes:")
    for old, new, desc in REPLACES:
        conteudo = conteudo.replace(old, new, 1)
        print(f"    [OK] {desc}")

    MAIN.write_text(conteudo, encoding="utf-8")
    tam_depois = len(conteudo)

    print()
    print("=" * 72)
    print(f"  [OK] Etapa 4 aplicada com sucesso.")
    print(f"  Tamanho antes:  {tam_antes:>6} bytes")
    print(f"  Tamanho depois: {tam_depois:>6} bytes ({tam_depois - tam_antes:+d})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())