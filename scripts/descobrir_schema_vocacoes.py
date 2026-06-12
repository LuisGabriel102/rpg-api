"""
descobrir_schema_vocacoes.py - Etapa 0 de vocacoes.

Descobre quais tabelas existem no dominio vocacoes, le schemas completos,
conta linhas, e mostra amostras pra Claude poder planejar as proximas etapas.
"""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


async def listar_tabelas(conn) -> list[str]:
    """Encontra todas as tabelas relevantes do dominio vocacoes."""
    sql = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND (
              table_name LIKE 'ref_vocac%'
              OR table_name LIKE 'ref_caminh%'
              OR table_name LIKE 'ref_pilar%'
              OR table_name LIKE 'ref_habilidades_classe%'
          )
        ORDER BY table_name
    """)
    rows = (await conn.execute(sql)).fetchall()
    return [r[0] for r in rows]


async def mostrar_colunas(conn, tabela: str) -> None:
    print(f"\n  --- COLUNAS ---")
    sql = text("""
        SELECT column_name, udt_name, is_nullable, column_default,
               character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :tab
        ORDER BY ordinal_position
    """)
    rows = (await conn.execute(sql, {"tab": tabela})).fetchall()
    for r in rows:
        col, udt, nullable, default, maxlen = r
        tipo = f"{udt}({maxlen})" if maxlen else udt
        nn = "NOT NULL" if nullable == "NO" else "NULL"
        def_str = f" DEFAULT {default[:30]}" if default else ""
        print(f"  {col:32s} {tipo:18s} {nn}{def_str}")


async def mostrar_constraints(conn, tabela: str) -> None:
    print(f"\n  --- CONSTRAINTS ---")
    sql = text("""
        SELECT con.conname, con.contype, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public' AND rel.relname = :tab
        ORDER BY con.contype
    """)
    rows = (await conn.execute(sql, {"tab": tabela})).fetchall()
    tipo_map = {"p": "PK", "c": "CHECK", "u": "UNIQUE", "f": "FK"}
    for r in rows:
        nome, tipo, definicao = r
        # pg retorna b'c' na v2 em alguns drivers, tratamos ambos
        key = tipo if isinstance(tipo, str) else tipo.decode()
        label = tipo_map.get(key, key)
        print(f"  [{label}] {definicao[:120]}")


async def mostrar_contagem_e_amostra(conn, tabela: str, limite: int = 2) -> None:
    total = (await conn.execute(text(f"SELECT COUNT(*) FROM {tabela}"))).scalar()
    print(f"\n  --- CONTAGEM: {total} linhas ---")

    if total == 0:
        return

    print(f"\n  --- AMOSTRA ({limite} linhas) ---")
    sql = text(f"SELECT * FROM {tabela} LIMIT {limite}")
    result = await conn.execute(sql)
    cols = list(result.keys())
    for i, row in enumerate(result.fetchall(), 1):
        print(f"\n  LINHA {i}:")
        for col, val in zip(cols, row):
            val_str = repr(val)
            if len(val_str) > 120:
                val_str = val_str[:117] + "..."
            print(f"    {col:32s} = {val_str}")


async def main() -> None:
    print("=" * 76)
    print("  DESCOBERTA DE SCHEMA - Dominio Vocacoes (Etapa 0)")
    print("=" * 76)

    async with engine.connect() as conn:
        tabelas = await listar_tabelas(conn)
        print(f"\n  Tabelas encontradas ({len(tabelas)}):")
        for t in tabelas:
            print(f"    - {t}")

        for t in tabelas:
            print(f"\n{'=' * 76}")
            print(f"  TABELA: {t}")
            print("=" * 76)
            await mostrar_colunas(conn, t)
            await mostrar_constraints(conn, t)
            await mostrar_contagem_e_amostra(conn, t, limite=2)

    await engine.dispose()
    print("\n" + "=" * 76)
    print("  FIM")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())