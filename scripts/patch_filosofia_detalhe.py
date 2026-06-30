"""patch_filosofia_detalhe.py - Adiciona card de filosofia no detalhe de vocacao."""
from pathlib import Path
import sys

MAIN = Path("main.py")
SENTINELA = "# === Filosofia do pilar ==="

# Substituicao: inserir depois do separator do header, antes do card de Origem
ANCORA_OLD = '''        ui.separator().classes("bg-zinc-700")

        # === Origem (se fundida) ==='''

ANCORA_NEW = '''        ui.separator().classes("bg-zinc-700")

        # === Filosofia do pilar ===
        if data["pilar"] in ("corpo", "sombra", "arcano", "espirito", "engenho"):
            filosofia_data = await _buscar_filosofia_pilar(data["pilar"])
            if filosofia_data:
                with ui.card().classes(
                    "w-full bg-zinc-800 border border-amber-800 p-4"
                ).props("flat"):
                    with ui.row().classes("items-baseline gap-3"):
                        ui.label(filosofia_data["nome"]).classes(
                            "text-sm font-bold text-amber-200 uppercase tracking-wider"
                        )
                        ui.label(filosofia_data["epiteto"]).classes(
                            "text-xs text-zinc-400 italic"
                        )
                    ui.label(filosofia_data["filosofia"]).classes(
                        "text-xs text-zinc-400 italic leading-relaxed mt-2"
                    )

        # === Origem (se fundida) ==='''


def main() -> int:
    c = MAIN.read_text(encoding="utf-8")
    antes = len(c)

    if SENTINELA in c:
        print(f"  [IDEMPOTENTE] Filosofia no detalhe ja aplicado. {antes} bytes.")
        return 0

    if ANCORA_OLD not in c:
        print("[ERRO] Ancora nao encontrada")
        return 1

    c = c.replace(ANCORA_OLD, ANCORA_NEW, 1)
    MAIN.write_text(c, encoding="utf-8")
    depois = len(c)

    print("=" * 72)
    print("  [OK] Card de filosofia adicionado ao detalhe de vocacao.")
    print(f"  Antes: {antes} | Depois: {depois} (+{depois - antes})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())