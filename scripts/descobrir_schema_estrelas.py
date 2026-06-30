"""
descobrir_schema_estrelas.py - Le o schema real das 2 tabelas de estrelas
direto do Neon pra eu poder escrever as classes SQLModel com precisao.

Mostra:
  1. Colunas (nome, tipo, nullable, default)
  2. Constraints (PK, CHECK, UNIQUE, FK)
  3. Indices
  4. Contagem de linhas
  5. Amostra: 3 linhas de cada tabela
"""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


TABELAS = ["ref_estrelas_nascimento", "ref_habilidades_estrela"]


async def mostrar_colunas(conn, tabela: str) -> None:
    print(f"\n  --- COLUNAS ---")
    sql = text("""
        SELECT
            column_name,
            data_type,
            udt_name,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :tab
        ORDER BY ordinal_position
    """)
    rows = (await conn.execute(sql, {"tab": tabela})).fetchall()
    if not rows:
        print(f"  [TABELA NAO EXISTE]")
        return
    for r in rows:
        col, dtype, udt, nullable, default, maxlen, prec, scale = r
        type_str = udt
        if maxlen:
            type_str += f"({maxlen})"
        elif prec:
            type_str += f"({prec},{scale})" if scale else f"({prec})"
        nn = "NOT NULL" if nullable == "NO" else "NULL"
        def_str = f" DEFAULT {default}" if default else ""
        print(f"  {col:35s} {type_str:20s} {nn}{def_str}")


async def mostrar_constraints(conn, tabela: str) -> None:
    print(f"\n  --- CONSTRAINTS ---")
    sql = text("""
        SELECT
            con.conname,
            con.contype,
            pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public' AND rel.relname = :tab
        ORDER BY con.contype, con.conname
    """)
    rows = (await conn.execute(sql, {"tab": tabela})).fetchall()
    if not rows:
        print("  [nenhuma]")
        return
    tipo_map = {"p": "PRIMARY", "c": "CHECK", "u": "UNIQUE", "f": "FOREIGN"}
    for r in rows:
        nome, tipo, definicao = r
        print(f"  [{tipo_map.get(tipo, tipo)}] {nome}")
        print(f"      {definicao}")


async def mostrar_indices(conn, tabela: str) -> None:
    print(f"\n  --- INDICES ---")
    sql = text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = :tab
        ORDER BY indexname
    """)
    rows = (await conn.execute(sql, {"tab": tabela})).fetchall()
    if not rows:
        print("  [nenhum]")
        return
    for r in rows:
        print(f"  {r[0]}")
        print(f"      {r[1]}")


async def mostrar_contagem(conn, tabela: str) -> None:
    sql = text(f"SELECT COUNT(*) FROM {tabela}")
    total = (await conn.execute(sql)).scalar()
    print(f"\n  --- CONTAGEM: {total} linhas ---")


async def mostrar_amostra(conn, tabela: str, limite: int = 3) -> None:
    print(f"\n  --- AMOSTRA ({limite} linhas) ---")
    sql = text(f"SELECT * FROM {tabela} ORDER BY id LIMIT {limite}")
    result = await conn.execute(sql)
    cols = result.keys()
    rows = result.fetchall()
    for i, row in enumerate(rows, 1):
        print(f"\n  LINHA {i}:")
        for col, val in zip(cols, row):
            # Trunca valores longos
            val_str = repr(val)
            if len(val_str) > 140:
                val_str = val_str[:137] + "..."
            print(f"    {col:35s} = {val_str}")


async def main() -> None:
    print("=" * 76)
    print("  DESCOBERTA DE SCHEMA - Tabelas de Estrelas do Veu")
    print("=" * 76)

    async with engine.connect() as conn:
        for tabela in TABELAS:
            print(f"\n{'=' * 76}")
            print(f"  TABELA: {tabela}")
            print("=" * 76)
            await mostrar_colunas(conn, tabela)
            await mostrar_constraints(conn, tabela)
            await mostrar_indices(conn, tabela)
            await mostrar_contagem(conn, tabela)
            await mostrar_amostra(conn, tabela, limite=2)

    await engine.dispose()
    print("\n" + "=" * 76)
    print("  FIM")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())