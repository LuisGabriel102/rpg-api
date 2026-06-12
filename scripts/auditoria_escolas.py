"""
auditoria_escolas.py - Fase 1 do fix do Bug #4.

Busca referencias hardcoded as 8 escolas de magia em:
  1. Codigo de funcoes plpgsql (pg_proc)
  2. CHECK constraints (pg_constraint)
  3. DEFAULT values de colunas (information_schema)
  4. Views (pg_views)
  5. Indices parciais (pg_indexes)

Aviso: 'Necromancia' eh ambigua - tambem eh nome de uma das 42 familias.
Hits pra essa string vao ser marcados como AMBIGUOS.
"""

import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


ESCOLAS = [
    "Abjuracao",
    "Conjuracao",
    "Divinacao",
    "Adivinhacao",
    "Encantamento",
    "Evocacao",
    "Ilusao",
    "Necromancia",
    "Transmutacao",
]

# Essa eh ambigua: tambem eh uma familia magica
AMBIGUAS = {"Necromancia"}


async def buscar_em_funcoes(conn, escola: str) -> list:
    """Busca em codigo de funcoes plpgsql. Retorna lista de (nome_func, linha_num, linha)."""
    sql = text("""
        SELECT p.proname, pg_get_functiondef(p.oid)
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND p.prolang = (SELECT oid FROM pg_language WHERE lanname='plpgsql')
          AND pg_get_functiondef(p.oid) ILIKE :padrao
    """)
    rows = (await conn.execute(sql, {"padrao": f"%{escola}%"})).fetchall()

    matches = []
    for r in rows:
        nome_func = r[0]
        codigo = r[1]
        for num, linha in enumerate(codigo.split("\n"), 1):
            # Procura a escola EM STRING LITERAL (entre aspas simples)
            padroes = [
                f"'{escola}'",
                f"''{escola}''",  # escapado dentro de funcao
                f"= '{escola}'",
                f"={escola}",
            ]
            if any(p in linha for p in padroes):
                matches.append({
                    "funcao": nome_func,
                    "linha_num": num,
                    "linha": linha.strip()[:180],
                })
    return matches


async def buscar_em_constraints(conn, escola: str) -> list:
    sql = text("""
        SELECT con.conname, rel.relname AS tabela, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
          AND pg_get_constraintdef(con.oid) ILIKE :padrao
    """)
    rows = (await conn.execute(sql, {"padrao": f"%{escola}%"})).fetchall()
    return [
        {"nome": r[0], "tabela": r[1], "definicao": r[2][:200]}
        for r in rows
    ]


async def buscar_em_defaults(conn, escola: str) -> list:
    sql = text("""
        SELECT table_name, column_name, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_default IS NOT NULL
          AND column_default ILIKE :padrao
    """)
    rows = (await conn.execute(sql, {"padrao": f"%{escola}%"})).fetchall()
    return [
        {"tabela": r[0], "coluna": r[1], "default": r[2]}
        for r in rows
    ]


async def buscar_em_views(conn, escola: str) -> list:
    sql = text("""
        SELECT viewname, definition
        FROM pg_views
        WHERE schemaname = 'public'
          AND definition ILIKE :padrao
    """)
    rows = (await conn.execute(sql, {"padrao": f"%{escola}%"})).fetchall()
    return [
        {"view": r[0], "trecho": r[1][:200]}
        for r in rows
    ]


async def buscar_em_indices(conn, escola: str) -> list:
    sql = text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexdef ILIKE :padrao
    """)
    rows = (await conn.execute(sql, {"padrao": f"%{escola}%"})).fetchall()
    return [
        {"nome": r[0], "definicao": r[1][:200]}
        for r in rows
    ]


async def main() -> None:
    print("=" * 72)
    print("  AUDITORIA DE DEPENDENCIAS - Bug #4 (Escolas de Magia)")
    print("=" * 72)

    total_geral = {
        "funcoes": 0,
        "constraints": 0,
        "defaults": 0,
        "views": 0,
        "indices": 0,
    }

    async with engine.connect() as conn:
        for escola in ESCOLAS:
            marker = " [AMBIGUA - tambem eh familia]" if escola in AMBIGUAS else ""
            print(f"\n--- {escola}{marker} ---")

            funcs = await buscar_em_funcoes(conn, escola)
            consts = await buscar_em_constraints(conn, escola)
            defs = await buscar_em_defaults(conn, escola)
            views = await buscar_em_views(conn, escola)
            idxs = await buscar_em_indices(conn, escola)

            total_hits = len(funcs) + len(consts) + len(defs) + len(views) + len(idxs)

            if total_hits == 0:
                print("  [zero hits]")
                continue

            total_geral["funcoes"] += len(funcs)
            total_geral["constraints"] += len(consts)
            total_geral["defaults"] += len(defs)
            total_geral["views"] += len(views)
            total_geral["indices"] += len(idxs)

            if funcs:
                print(f"  FUNCOES ({len(funcs)}):")
                for m in funcs[:10]:  # max 10 por escola pra nao explodir
                    print(f"    [{m['funcao']}:{m['linha_num']}]  {m['linha']}")
                if len(funcs) > 10:
                    print(f"    ... + {len(funcs) - 10} mais")

            if consts:
                print(f"  CONSTRAINTS ({len(consts)}):")
                for c in consts:
                    print(f"    {c['tabela']}.{c['nome']}: {c['definicao']}")

            if defs:
                print(f"  DEFAULTS ({len(defs)}):")
                for d in defs:
                    print(f"    {d['tabela']}.{d['coluna']} = {d['default']}")

            if views:
                print(f"  VIEWS ({len(views)}):")
                for v in views:
                    print(f"    {v['view']}")

            if idxs:
                print(f"  INDICES ({len(idxs)}):")
                for i in idxs:
                    print(f"    {i['nome']}: {i['definicao']}")

    print()
    print("=" * 72)
    print("  SUMARIO")
    print("=" * 72)
    print(f"  Hits em FUNCOES:     {total_geral['funcoes']}")
    print(f"  Hits em CONSTRAINTS: {total_geral['constraints']}")
    print(f"  Hits em DEFAULTS:    {total_geral['defaults']}")
    print(f"  Hits em VIEWS:       {total_geral['views']}")
    print(f"  Hits em INDICES:     {total_geral['indices']}")
    soma = sum(total_geral.values())
    print(f"  TOTAL:               {soma}")
    print()
    print("  Lembrete: hits em 'Necromancia' sao ambiguos (tambem eh familia).")
    print("  Os hits reais que importam sao das outras 8 strings.")
    print("=" * 72)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())