"""fix_home_travamento.py - Troca 3 awaits sequenciais por asyncio.gather."""
from pathlib import Path
import sys

MAIN = Path("main.py")

OLD = """async def pagina_oficina():
    total_npcs = await _contar_npcs_total()
    total_estrelas = await _contar_estrelas_total()
    total_vocacoes = await _contar_vocacoes_total()
"""

NEW = """async def pagina_oficina():
    try:
        total_npcs, total_estrelas, total_vocacoes = await asyncio.wait_for(
            asyncio.gather(
                _contar_npcs_total(),
                _contar_estrelas_total(),
                _contar_vocacoes_total(),
            ),
            timeout=10.0,
        )
    except Exception as e:
        print(f"[home] erro ao contar: {e}")
        total_npcs = total_estrelas = total_vocacoes = 0
"""


def main() -> int:
    c = MAIN.read_text(encoding="utf-8")

    if "asyncio.wait_for" in c and "total_npcs, total_estrelas, total_vocacoes" in c:
        print("[IDEMPOTENTE] Fix ja aplicado.")
        return 0

    if OLD not in c:
        print("[ERRO] Bloco antigo nao encontrado")
        return 1

    c = c.replace(OLD, NEW, 1)
    MAIN.write_text(c, encoding="utf-8")
    print("=" * 72)
    print("  [OK] Home agora usa asyncio.gather com timeout 10s.")
    print("  Se alguma contagem falhar, mostra 0 em vez de travar.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())