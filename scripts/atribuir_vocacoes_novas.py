"""atribuir_vocacoes_novas.py - Define atributos_primarios das 2 novas vocacoes."""
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text
from db import engine

APPLY = "--apply" in sys.argv


async def main() -> None:
    modo = "APLICANDO" if APPLY else "DRY RUN"
    print("=" * 76)
    print(f"  ATRIBUTOS PRIMARIOS - Ladino Arcano + Devorador de Grimorios - {modo}")
    print("=" * 76)

    async with engine.begin() as conn:
        # Estado antes
        print("\n[1] Estado ANTES:")
        result = await conn.execute(text("""
            SELECT id, nome_ptbr, atributos_primarios
            FROM ref_vocacoes
            WHERE id IN (99, 128)
            ORDER BY id
        """))
        for row in result:
            print(f"    [{row[0]:3d}] {row[1]:30s} atribs={row[2]}")

        # UPDATE id 99 -> DEX/INT (Ladino Arcano)
        print("\n[2] UPDATE id 99 (Ladino Arcano) -> DEX/INT")
        await conn.execute(text("""
            UPDATE ref_vocacoes
            SET atributos_primarios = :atribs
            WHERE id = 99
        """), {"atribs": ["DEX", "INT"]})
        print("    OK")

        # UPDATE id 128 -> INT/CON (Devorador de Grimorios)
        print("\n[3] UPDATE id 128 (Devorador de Grimorios) -> INT/CON")
        await conn.execute(text("""
            UPDATE ref_vocacoes
            SET atributos_primarios = :atribs
            WHERE id = 128
        """), {"atribs": ["INT", "CON"]})
        print("    OK")

        # Estado depois
        print("\n[4] Estado DEPOIS:")
        result = await conn.execute(text("""
            SELECT id, nome_ptbr, atributos_primarios
            FROM ref_vocacoes
            WHERE id IN (99, 128)
            ORDER BY id
        """))
        for row in result:
            print(f"    [{row[0]:3d}] {row[1]:30s} atribs={row[2]}")

        if not APPLY:
            print("\n[5] DRY RUN - fazendo ROLLBACK")
            raise Exception("ROLLBACK_DRY_RUN")

    print("\n" + "=" * 76)
    print("  [OK] ATRIBUTOS APLICADOS")
    print("=" * 76)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        if "ROLLBACK_DRY_RUN" in str(e):
            print("\n" + "=" * 76)
            print("  [DRY RUN] Nada foi escrito. Rode com --apply pra aplicar.")
            print("=" * 76)
        else:
            raise