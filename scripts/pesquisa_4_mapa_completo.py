"""
Pesquisa 4 da Catedral - Mapa completo das 157 tabelas do banco.

Diferente das pesquisas 1-3 (focadas em dominios), esta e panoramica.
Captura metadata RESUMIDO de cada tabela pra descobrir o territorio inteiro.

Por tabela coleta:
  - Nome, prefixo (1a parte do nome ate _)
  - Numero de colunas
  - Row count
  - Tem trigger?
  - Tem coluna embedding (pgvector)?
  - Tem coluna path (ltree)?
  - Quantas FKs SAEM (out)
  - Quantas FKs ENTRAM (in)
  - Tamanho em disco

Por RPC: nome + parametros + retorno (sem codigo fonte).

Saida: pesquisa_4_mapa_completo.json (esperado ~100KB)
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


OUTPUT_FILE = "pesquisa_4_mapa_completo.json"
SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def validar(nome: str) -> str:
    if not SAFE_NAME.match(nome):
        raise ValueError(f"Nome inseguro: {nome!r}")
    return nome


# ====================================================================
# QUERIES PRINCIPAIS
# ====================================================================

async def listar_todas_tabelas(conn) -> list[str]:
    sql = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    result = await conn.execute(sql)
    return [row[0] for row in result.fetchall()]


async def listar_todas_views(conn) -> list[str]:
    sql = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'VIEW'
        ORDER BY table_name
    """)
    result = await conn.execute(sql)
    return [row[0] for row in result.fetchall()]


async def metadata_de_tabela(conn, tabela: str) -> dict:
    """
    Captura metadata resumido de UMA tabela.
    Retorna dict com: cols, row_count, has_trigger, has_vector, has_ltree,
    has_trgm_idx, fks_out, fks_in, size_kb.
    """
    nome_seg = validar(tabela)

    # 1. Numero de colunas + flags de embedding/path
    cols_sql = text("""
        SELECT column_name, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :t
        ORDER BY ordinal_position
    """)
    res = await conn.execute(cols_sql, {"t": tabela})
    colunas = [(row[0], row[1]) for row in res.fetchall()]
    n_cols = len(colunas)

    has_vector = any(udt == 'vector' for _, udt in colunas)
    has_ltree = any(udt == 'ltree' for _, udt in colunas)
    has_jsonb = any(udt == 'jsonb' for _, udt in colunas)

    # Lista nomes de coluna pra detectar campos relacionais comuns
    nomes_col = [n for n, _ in colunas]

    # 2. Row count
    try:
        rc = await conn.execute(text(f"SELECT count(*) FROM public.{nome_seg}"))
        row_count = rc.scalar()
    except Exception:
        row_count = None

    # 3. Tem trigger?
    tr_sql = text("""
        SELECT count(*) FROM information_schema.triggers
        WHERE event_object_schema = 'public' AND event_object_table = :t
    """)
    tr = await conn.execute(tr_sql, {"t": tabela})
    n_triggers = tr.scalar()

    # 4. Tem indice trgm? (pra busca fuzzy)
    idx_sql = text("""
        SELECT count(*) FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = :t
          AND indexdef ILIKE '%gin_trgm%'
    """)
    ix = await conn.execute(idx_sql, {"t": tabela})
    has_trgm_idx = ix.scalar() > 0

    # 5. FKs SAINDO (constraints da tabela do tipo f)
    fks_out_sql = text("""
        SELECT count(*) FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public' AND rel.relname = :t AND con.contype = 'f'
    """)
    fo = await conn.execute(fks_out_sql, {"t": tabela})
    fks_out = fo.scalar()

    # 6. FKs ENTRANDO (quantas tabelas apontam pra ca)
    fks_in_sql = text("""
        SELECT count(*) FROM pg_constraint con
        WHERE con.contype = 'f' AND con.confrelid = (
            SELECT oid FROM pg_class
            WHERE relname = :t
              AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname='public')
        )
    """)
    fi = await conn.execute(fks_in_sql, {"t": tabela})
    fks_in = fi.scalar()

    # 7. Tamanho em disco (KB)
    sz_sql = text("""
        SELECT pg_total_relation_size(c.oid) FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = :t
    """)
    sz = await conn.execute(sz_sql, {"t": tabela})
    sz_bytes = sz.scalar() or 0
    size_kb = round(sz_bytes / 1024, 1)

    # 8. Detecta colunas relacionais comuns (pra ecossistema rapido)
    rel_cols = [n for n in nomes_col if n.endswith('_id') and n not in ('id',)]

    return {
        "n_cols": n_cols,
        "row_count": row_count,
        "n_triggers": n_triggers,
        "has_vector": has_vector,
        "has_ltree": has_ltree,
        "has_jsonb": has_jsonb,
        "has_trgm_idx": has_trgm_idx,
        "fks_out": fks_out,
        "fks_in": fks_in,
        "size_kb": size_kb,
        "fk_columns": rel_cols,
    }


async def listar_todas_funcoes(conn) -> list[dict]:
    """Todas as funcoes do schema public, sem codigo fonte."""
    sql = text("""
        SELECT p.proname,
               pg_get_function_identity_arguments(p.oid) AS parametros,
               pg_get_function_result(p.oid) AS retorno,
               l.lanname AS linguagem,
               p.prokind AS kind
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_language l ON l.oid = p.prolang
        WHERE n.nspname = 'public'
        ORDER BY p.proname
    """)
    result = await conn.execute(sql)
    return [
        {
            "nome": row[0],
            "parametros": row[1],
            "retorno": row[2],
            "linguagem": row[3],
            "kind": row[4] if isinstance(row[4], str) else (row[4].decode() if hasattr(row[4], 'decode') else str(row[4])),
        }
        for row in result.fetchall()
    ]


async def listar_extensoes(conn) -> list[str]:
    sql = text("SELECT extname FROM pg_extension ORDER BY extname")
    result = await conn.execute(sql)
    return [row[0] for row in result.fetchall()]


# ====================================================================
# ORQUESTRADOR
# ====================================================================

async def main() -> None:
    print("=" * 60)
    print("PESQUISA 4 - Mapa completo das 157 tabelas")
    print("=" * 60)
    print()

    async with engine.connect() as conn:
        print("[1/5] Listando extensoes do Postgres...")
        exts = await listar_extensoes(conn)
        print(f"      Encontradas: {len(exts)}")
        for e in exts:
            print(f"      - {e}")
        print()

        print("[2/5] Listando todas as tabelas e views...")
        tabelas = await listar_todas_tabelas(conn)
        views = await listar_todas_views(conn)
        print(f"      Tabelas (BASE TABLE): {len(tabelas)}")
        print(f"      Views:                {len(views)}")
        print()

        print("[3/5] Coletando metadata de cada tabela (pode demorar)...")
        dados_tabelas: dict = {}
        for i, tabela in enumerate(tabelas, start=1):
            if i % 20 == 0:
                print(f"      ... {i}/{len(tabelas)}")
            try:
                dados_tabelas[tabela] = await metadata_de_tabela(conn, tabela)
            except Exception as e:
                print(f"      ERRO em {tabela}: {e}")
                dados_tabelas[tabela] = {"erro": str(e)}
        print(f"      Concluido: {len(dados_tabelas)}/{len(tabelas)}")
        print()

        print("[4/5] Listando todas as funcoes/RPCs do banco...")
        funcoes = await listar_todas_funcoes(conn)
        # Separa user vs trigger vs aggregate
        user_funcs = [f for f in funcoes if f['kind'] == 'f']
        triggers = [f for f in funcoes if f['kind'] == 't' or 'trigger' in f['retorno']]
        print(f"      Total: {len(funcoes)}")
        print(f"      User functions: {len(user_funcs)}")
        print()

    # Calcula agrupamentos por prefixo
    print("[5/5] Calculando agrupamentos por prefixo...")
    from collections import Counter
    prefixos = Counter()
    for nome in tabelas:
        # prefixo = primeira palavra antes de _
        if '_' in nome:
            pref = nome.split('_')[0]
        else:
            pref = nome
        prefixos[pref] += 1
    
    top_prefixos = prefixos.most_common(20)
    print(f"      Top prefixos:")
    for p, q in top_prefixos[:10]:
        print(f"        {p}_*: {q} tabelas")
    print()

    # Tabelas com pgvector / ltree
    com_vector = [t for t, m in dados_tabelas.items() if m.get('has_vector')]
    com_ltree = [t for t, m in dados_tabelas.items() if m.get('has_ltree')]
    com_trgm = [t for t, m in dados_tabelas.items() if m.get('has_trgm_idx')]
    com_trigger = [t for t, m in dados_tabelas.items() if m.get('n_triggers', 0) > 0]
    print(f"      Tabelas com pgvector: {len(com_vector)}")
    print(f"      Tabelas com ltree:    {len(com_ltree)}")
    print(f"      Tabelas com trgm idx: {len(com_trgm)}")
    print(f"      Tabelas com trigger:  {len(com_trigger)}")
    print()

    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn (ep-calm-shadow-any1pg3i)",
        "extensoes_postgres": exts,
        "total_tabelas": len(tabelas),
        "total_views": len(views),
        "views": views,
        "tabelas": dados_tabelas,
        "prefixos_count": dict(prefixos),
        "tabelas_com_pgvector": com_vector,
        "tabelas_com_ltree": com_ltree,
        "tabelas_com_trgm_idx": com_trgm,
        "tabelas_com_trigger": com_trigger,
        "total_funcoes": len(funcoes),
        "funcoes": funcoes,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

    import os
    tam_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("=" * 60)
    print(f"OK Arquivo salvo: {OUTPUT_FILE}")
    print(f"   Tamanho: {tam_kb:.1f} KB")
    print(f"   Tabelas: {len(tabelas)}")
    print(f"   Views:   {len(views)}")
    print(f"   Funcoes: {len(funcoes)}")
    print(f"   Extensoes: {len(exts)}")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())