"""
Pesquisa 3 da Catedral - Schema completo de NPCs (com foco em Ancora).

Desafio especial: NPCs nao tem prefixo unico como personagem_* ou companion_*.
Buscamos em 3 padroes:
  - npcs (tabela mae)
  - npc_* (subtabelas e ecossistema)
  - ancora_*, anchor_* (possiveis tabelas especificas de Camada 3)

Saida: pesquisa_3_npcs.json
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


OUTPUT_FILE = "pesquisa_3_npcs.json"
SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def validar_nome_tabela(nome: str) -> str:
    if not SAFE_NAME.match(nome):
        raise ValueError(f"Nome de tabela inseguro: {nome!r}")
    return nome


# ====================================================================
# PERGUNTA 1 - Descobrir tabelas de NPCs
# ====================================================================

async def pergunta_1_descobrir_tabelas(conn) -> list[str]:
    """
    Padroes:
      - npcs (tabela mae)
      - npc_* (subtabelas)
      - ancora_*, anchor_* (Camada 3 especifica)
      - location_npcs (ja conhecida)
    """
    sql = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
          AND (
            table_name = 'npcs'
            OR table_name LIKE 'npc_%'
            OR table_name LIKE '%_npcs'
            OR table_name LIKE 'ancora_%'
            OR table_name LIKE 'anchor_%'
          )
        ORDER BY
          CASE WHEN table_name = 'npcs' THEN 0 ELSE 1 END,
          table_name
    """)
    result = await conn.execute(sql)
    return [row[0] for row in result.fetchall()]


# ====================================================================
# PERGUNTAS 2-7 (copiadas da Pesquisa 2, funcionam identicas)
# ====================================================================

async def pergunta_2_colunas(conn, tabela: str) -> list[dict]:
    sql = text("""
        SELECT
            c.column_name, c.data_type, c.udt_name, c.is_nullable,
            c.column_default, c.ordinal_position, c.character_maximum_length,
            c.numeric_precision, c.numeric_scale, pgd.description AS comentario
        FROM information_schema.columns c
        LEFT JOIN pg_catalog.pg_statio_all_tables st
            ON st.schemaname = c.table_schema AND st.relname = c.table_name
        LEFT JOIN pg_catalog.pg_description pgd
            ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
        WHERE c.table_schema = 'public' AND c.table_name = :tabela
        ORDER BY c.ordinal_position
    """)
    result = await conn.execute(sql, {"tabela": tabela})
    return [
        {
            "nome": row[0], "tipo_sql": row[1], "tipo_postgres": row[2],
            "nullable": row[3] == "YES", "default": row[4], "posicao": row[5],
            "max_length": row[6], "precisao_numerica": row[7],
            "escala_numerica": row[8], "comentario": row[9],
        }
        for row in result.fetchall()
    ]


async def pergunta_3_constraints(conn, tabela: str) -> list[dict]:
    sql = text("""
        SELECT con.conname, con.contype, pg_get_constraintdef(con.oid, true) AS definicao
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public' AND rel.relname = :tabela
        ORDER BY con.contype, con.conname
    """)
    result = await conn.execute(sql, {"tabela": tabela})
    tipos_legivel = {"p": "PRIMARY KEY", "f": "FOREIGN KEY", "u": "UNIQUE", "c": "CHECK", "x": "EXCLUSION"}
    out = []
    for row in result.fetchall():
        tc = row[1] if isinstance(row[1], str) else row[1].decode() if hasattr(row[1], 'decode') else str(row[1])
        out.append({
            "nome": row[0],
            "tipo_codigo": tc,
            "tipo_legivel": tipos_legivel.get(tc, tc),
            "definicao": row[2],
        })
    return out


async def pergunta_4_indices(conn, tabela: str) -> list[dict]:
    sql = text("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = :tabela
        ORDER BY indexname
    """)
    result = await conn.execute(sql, {"tabela": tabela})
    indices = []
    for row in result.fetchall():
        idef = row[1]
        is_vector = "vector" in idef.lower() or "hnsw" in idef.lower() or "ivfflat" in idef.lower()
        is_trgm = "gin_trgm" in idef.lower() or "trgm_ops" in idef.lower()
        is_ltree = "ltree" in idef.lower()
        indices.append({
            "nome": row[0],
            "definicao": idef,
            "tipo_especial": (
                "pgvector" if is_vector else
                "pg_trgm" if is_trgm else
                "ltree" if is_ltree else None
            ),
        })
    return indices


async def pergunta_5_referencias_reversas(conn, tabela: str) -> list[dict]:
    sql = text("""
        SELECT (con.conrelid::regclass)::text AS tabela_origem,
               con.conname,
               pg_get_constraintdef(con.oid, true) AS definicao
        FROM pg_constraint con
        WHERE con.contype = 'f'
          AND con.confrelid = (
              SELECT oid FROM pg_class
              WHERE relname = :tabela
                AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname='public')
          )
        ORDER BY tabela_origem, con.conname
    """)
    result = await conn.execute(sql, {"tabela": tabela})
    return [
        {"tabela_origem": row[0], "constraint_nome": row[1], "definicao": row[2]}
        for row in result.fetchall()
    ]


async def pergunta_5b_ecossistema(conn) -> list[dict]:
    """Tabelas com coluna npc_id (ecossistema de NPCs)."""
    sql = text("""
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name IN (
              'npc_id', 'npcs_id', 'ancora_id', 'anchor_id',
              'npc_relacionado_id', 'afeta_npc_id'
          )
        ORDER BY table_name, column_name
    """)
    result = await conn.execute(sql)
    return [
        {
            "tabela": row[0], "coluna": row[1],
            "tipo": row[2], "nullable": row[3] == "YES",
        }
        for row in result.fetchall()
    ]


async def pergunta_6_funcoes(conn) -> list[dict]:
    """Funcoes relacionadas a NPCs."""
    sql = text("""
        SELECT p.proname,
               pg_get_function_identity_arguments(p.oid) AS parametros,
               pg_get_function_result(p.oid) AS retorno,
               pg_get_functiondef(p.oid) AS codigo_fonte,
               l.lanname AS linguagem
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_language l ON l.oid = p.prolang
        WHERE n.nspname = 'public' AND p.prokind = 'f'
          AND (
              p.proname ILIKE '%npc%'
              OR p.proname ILIKE '%ancora%'
              OR p.proname ILIKE '%anchor%'
              OR p.proname ILIKE '%figurante%'
              OR p.proname ILIKE '%recorrente%'
              OR p.proname ILIKE '%memoria%'
              OR p.proname ILIKE '%dialogo%'
              OR p.proname ILIKE '%interacao%'
          )
        ORDER BY p.proname
    """)
    result = await conn.execute(sql)
    return [
        {
            "nome": row[0], "parametros": row[1], "retorno": row[2],
            "linguagem": row[4], "codigo_fonte": row[3],
        }
        for row in result.fetchall()
    ]


async def pergunta_7_estatisticas(conn, tabela: str) -> dict:
    nome_seguro = validar_nome_tabela(tabela)
    rc = await conn.execute(text(f"SELECT count(*) FROM public.{nome_seguro}"))
    row_count = rc.scalar()

    sz = await conn.execute(text("""
        SELECT pg_total_relation_size(c.oid), pg_relation_size(c.oid), pg_indexes_size(c.oid)
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = :tabela
    """), {"tabela": tabela})
    sz_row = sz.fetchone()
    tamanho = {
        "total_bytes": sz_row[0] if sz_row else 0,
        "tabela_bytes": sz_row[1] if sz_row else 0,
        "indices_bytes": sz_row[2] if sz_row else 0,
    } if sz_row else {}

    tr = await conn.execute(text("""
        SELECT trigger_name, event_manipulation, action_timing, action_statement
        FROM information_schema.triggers
        WHERE event_object_schema = 'public' AND event_object_table = :tabela
        ORDER BY trigger_name
    """), {"tabela": tabela})
    triggers = [
        {"nome": row[0], "evento": row[1], "timing": row[2], "acao": row[3]}
        for row in tr.fetchall()
    ]

    vr = await conn.execute(text("""
        SELECT DISTINCT v.viewname FROM pg_views v
        WHERE v.schemaname = 'public' AND v.definition ILIKE '%' || :tabela || '%'
        ORDER BY v.viewname
    """), {"tabela": tabela})
    views = [row[0] for row in vr.fetchall()]

    return {
        "row_count": row_count, "tamanho": tamanho,
        "triggers": triggers, "views_dependentes": views,
    }


# ====================================================================
# ORQUESTRADOR
# ====================================================================

async def main() -> None:
    print("=" * 60)
    print("PESQUISA 3 - Schema completo de NPCs")
    print("=" * 60)
    print()

    async with engine.connect() as conn:
        print("[1/8] Descobrindo tabelas (npcs, npc_*, *_npcs, ancora_*, anchor_*)...")
        tabelas = await pergunta_1_descobrir_tabelas(conn)
        print(f"      Encontradas: {len(tabelas)} tabelas")
        for t in tabelas:
            print(f"      - {t}")
        print()

        dados_tabelas: dict = {}
        for i, tabela in enumerate(tabelas, start=1):
            print(f"[2-7] Processando tabela {i}/{len(tabelas)}: {tabela}...")
            try:
                dados_tabelas[tabela] = {
                    "colunas": await pergunta_2_colunas(conn, tabela),
                    "constraints": await pergunta_3_constraints(conn, tabela),
                    "indices": await pergunta_4_indices(conn, tabela),
                    "referenciada_por": await pergunta_5_referencias_reversas(conn, tabela),
                    "estatisticas": await pergunta_7_estatisticas(conn, tabela),
                }
            except Exception as e:
                print(f"      ERRO em {tabela}: {e}")
                dados_tabelas[tabela] = {"erro": str(e)}
        print()

        print("[5B/8] Listando tabelas com coluna npc_id/ancora_id (ecossistema)...")
        ecossistema = await pergunta_5b_ecossistema(conn)
        print(f"       Encontradas: {len(ecossistema)} colunas em outras tabelas")
        print()

        print("[6/8] Procurando funcoes/RPCs relacionadas a NPCs...")
        funcoes = await pergunta_6_funcoes(conn)
        print(f"      Encontradas: {len(funcoes)} funcoes")
        for f in funcoes[:15]:
            print(f"      - {f['nome']}({f['parametros'][:60]})")
        if len(funcoes) > 15:
            print(f"      ... e mais {len(funcoes) - 15}")
        print()

    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn (ep-calm-shadow-any1pg3i)",
        "padroes_buscados": ["npcs", "npc_%", "%_npcs", "ancora_%", "anchor_%"],
        "total_tabelas_encontradas": len(tabelas),
        "tabelas": dados_tabelas,
        "ecossistema_npc_id": ecossistema,
        "funcoes_relacionadas": funcoes,
        "total_funcoes_encontradas": len(funcoes),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

    import os
    tamanho_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("=" * 60)
    print(f"OK Arquivo salvo: {OUTPUT_FILE}")
    print(f"   Tamanho: {tamanho_kb:.1f} KB")
    print(f"   Tabelas: {len(tabelas)}")
    print(f"   Funcoes: {len(funcoes)}")
    print(f"   Ecossistema: {len(ecossistema)} colunas em outras tabelas")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())