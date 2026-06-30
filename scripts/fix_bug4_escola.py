"""
fix_bug4_escola.py - Fix do Bug #4 descoberto na Pesquisa 14.

Consolida as 2 magias marcadas com escola='Adivinhacao' em escola='Divinacao'
(a grafia majoritaria, 184 magias). Opcao A escolhida apos auditoria confirmar
zero dependencias hardcoded no banco e no codigo local.

Backlog: a alderynizacao das escolas (adicionar acentos: Transmutacao ->
Transmutacao, Ilusao -> Ilusao, etc.) fica pra fazer junto com a alderynizacao
massiva das 1500+ magias durante a construcao da Catedral.

Uso:
    python fix_bug4_escola.py           # DRY-RUN (ROLLBACK no final)
    python fix_bug4_escola.py apply     # COMMIT real
"""
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


MODO = "apply" if len(sys.argv) > 1 and sys.argv[1].lower() == "apply" else "dry_run"


FIX_SQL = """
UPDATE magias
SET escola = 'Divinacao'
WHERE escola = 'Adivinhacao'
"""


async def ver_estado(conn, label: str) -> None:
    print(f"\n--- {label} ---")
    sql = text("""
        SELECT escola, COUNT(*) AS total
        FROM magias
        WHERE escola IN ('Divinacao', 'Adivinhacao')
        GROUP BY escola
        ORDER BY escola
    """)
    rows = (await conn.execute(sql)).fetchall()
    if not rows:
        print("  [nenhuma magia com Divinacao ou Adivinhacao]")
        return
    for r in rows:
        print(f"  {r[0]:<15s} {r[1]}")


async def listar_afetadas(conn) -> None:
    sql = text("""
        SELECT id, nome, familia_magica, nivel_original
        FROM magias
        WHERE escola = 'Adivinhacao'
        ORDER BY id
    """)
    rows = (await conn.execute(sql)).fetchall()
    if rows:
        print(f"\n  Magias que serao consolidadas ({len(rows)}):")
        for r in rows:
            print(f"    id={r[0]:5d}  [{r[2]:<20s} N{r[3]}]  {r[1]}")
    else:
        print("\n  Nenhuma magia precisando fix.")


async def main() -> None:
    print("=" * 72)
    print(f"  FIX BUG #4 - Escola Adivinhacao -> Divinacao  |  Modo: {MODO.upper()}")
    print("=" * 72)

    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            await ver_estado(conn, "ESTADO ANTES")
            await listar_afetadas(conn)

            print("\n[APLICANDO FIX]")
            result = await conn.execute(text(FIX_SQL))
            print(f"  OK ({result.rowcount} linhas atualizadas)")

            await ver_estado(conn, "ESTADO DEPOIS (dentro da transacao)")

            print()
            if MODO == "apply":
                await trans.commit()
                print("=" * 72)
                print("  [APPLY] COMMITADO. Bug #4 fechado.")
                print("=" * 72)
            else:
                await trans.rollback()
                print("=" * 72)
                print("  [DRY-RUN] ROLLBACK. Nada foi aplicado.")
                print("  Para aplicar de verdade:")
                print("    python fix_bug4_escola.py apply")
                print("=" * 72)
        except Exception as e:
            await trans.rollback()
            print(f"\n[ERRO] Rollback automatico: {e}")
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())