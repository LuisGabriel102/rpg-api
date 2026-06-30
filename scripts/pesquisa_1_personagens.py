"""
Pesquisa 1 da Catedral - Schema completo de Personagens (PC).

Extrai do banco Neon Alderyn TODO o schema relacionado a Personagem (Protagonista
jogavel). Reusa a conexao do db.py que ja existe no projeto.

As 8 perguntas que o script faz pro banco:
  1. Quais tabelas existem que falam de personagem? (padroes: personagens, personagem_*, character_*)
  2. Quais colunas tem cada uma?
  3. Quais constraints (PK, FK, UNIQUE, CHECK) cada uma tem?
  4. Quais indices cada uma tem? (incluindo pgvector, ltree, gin_trgm)
  5. Quem mais aponta pra essas tabelas via FK? (referencias reversas)
  5b. Quais tabelas tem coluna 'personagem_id'? (ecossistema completo)
  6. Quais funcoes/RPCs do Postgres mexem com personagem? (nome OU corpo)
  7. Estatisticas: row count, tamanho em disco, triggers, views dependentes.

Saida:
  pesquisa_1_personagens.json - tudo serializado pra Claude processar depois.

Como rodar:
  python pesquisa_1_personagens.py
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


# ====================================================================
# CONSTANTES
# ====================================================================

OUTPUT_FILE = "pesquisa_1_personagens.json"

# Regex pra validar nomes de tabela antes de SQL dinamico (evita injection)
SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def validar_nome_tabela(nome: str) -> str:
    """Garante que o nome da tabela so contem caracteres seguros."""
    if not SAFE_NAME.match(nome):
        raise ValueError(f"Nome de tabela inseguro: {nome!r}")
    return nome


# ====================================================================
# PERGUNTA 1 - Descobrir as tabelas
# ====================================================================

async def pergunta_1_descobrir_tabelas(conn) -> list[str]:
    """
    Lista todas as tabelas do schema public que falam de personagem.

    Padroes buscados:
      - personagens (tabela mae)
      - personagem_* (sub-tabelas, ex: personagem_atributos)
      - character_* (variantes em ingles, ex: character_legacy)
    """
    sql = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
          AND (
            table_name = 'personagens'
            OR table_name LIKE 'personagem_%'
            OR table_name LIKE 'character_%'
          )
        ORDER BY
          CASE WHEN table_name = 'personagens' THEN 0 ELSE 1 END,
          table_name
    """)
    result = await conn.execute(sql)
    return [row[0] for row in result.fetchall()]


# ====================================================================
# PERGUNTA 2 - Colunas de cada tabela
# ====================================================================

async def pergunta_2_colunas(conn, tabela: str) -> list[dict]:
    """
    Retorna todas as colunas da tabela com tipo, nullable, default e
    comentario (se existir).
    """
    sql = text("""
        SELECT
            c.column_name,
            c.data_type,
            c.udt_name,
            c.is_nullable,
            c.column_default,
            c.ordinal_position,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            pgd.description AS comentario
        FROM information_schema.columns c
        LEFT JOIN pg_catalog.pg_statio_all_tables st
            ON st.schemaname = c.table_schema AND st.relname = c.table_name
        LEFT JOIN pg_catalog.pg_description pgd
            ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
        WHERE c.table_schema = 'public'
          AND c.table_name = :tabela
        ORDER BY c.ordinal_position
    """)
    result = await conn.execute(sql, {"tabela": tabela})
    return [
        {
            "nome": row[0],
            "tipo_sql": row[1],
            "tipo_postgres": row[2],
            "nullable": row[3] == "YES",
            "default": row[4],
            "posicao": row[5],
            "max_length": row[6],
            "precisao_numerica": row[7],
            "escala_numerica": row[8],
            "comentario": row[9],
        }
        for row in result.fetchall()
    ]


# ====================================================================
# PERGUNTA 3 - Constraints (PK, FK, UNIQUE, CHECK)
# ====================================================================

async def pergunta_3_constraints(conn, tabela: str) -> list[dict]:
    """
    Lista todas as constraints da tabela com sua definicao SQL completa.

    Tipos de constraint que aparecem aqui:
      p = PRIMARY KEY
      f = FOREIGN KEY
      u = UNIQUE
      c = CHECK
    """
    sql = text("""
        SELECT
            con.conname,
            con.contype,
            pg_get_constraintdef(con.oid, true) AS definicao
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
          AND rel.relname = :tabela
        ORDER BY con.contype, con.conname
    """)
    result = await conn.execute(sql, {"tabela": tabela})
    tipos_legivel = {
        "p": "PRIMARY KEY",
        "f": "FOREIGN KEY",
        "u": "UNIQUE",
        "c": "CHECK",
        "x": "EXCLUSION",
    }
    return [
        {
            "nome": row[0],
            "tipo_codigo": row[1],
            "tipo_legivel": tipos_legivel.get(row[1], row[1]),
            "definicao": row[2],
        }
        for row in result.fetchall()
    ]


# ====================================================================
# PERGUNTA 4 - Indices
# ====================================================================

async def pergunta_4_indices(conn, tabela: str) -> list[dict]:
    """Lista todos os indices da tabela com a definicao SQL completa."""
    sql = text("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = :tabela
        ORDER BY indexname
    """)
    result = await conn.execute(sql, {"tabela": tabela})
    indices = []
    for row in result.fetchall():
        idef = row[1]
        is_vector = "vector" in idef.lower() or "hnsw" in idef.lower() or "ivfflat" in idef.lower()
        is_trgm = "gin_trgm" in idef.lower() or "trgm_ops" in idef.lower()
        is_ltree = "ltree" in idef.lower() or "gist" in idef.lower() and "tree" in idef.lower()
        indices.append({
            "nome": row[0],
            "definicao": idef,
            "tipo_especial": (
                "pgvector" if is_vector else
                "pg_trgm" if is_trgm else
                "ltree" if is_ltree else
                None
            ),
        })
    return indices


# ====================================================================
# PERGUNTA 5 - Referencias reversas (quem aponta pra ca via FK)
# ====================================================================

async def pergunta_5_referencias_reversas(conn, tabela: str) -> list[dict]:
    """Lista todas as tabelas que tem FK apontando pra esta tabela."""
    sql = text("""
        SELECT
            (con.conrelid::regclass)::text AS tabela_origem,
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
        {
            "tabela_origem": row[0],
            "constraint_nome": row[1],
            "definicao": row[2],
        }
        for row in result.fetchall()
    ]


# ====================================================================
# PERGUNTA 5B - Tabelas que tem coluna 'personagem_id' (ecossistema)
# ====================================================================

async def pergunta_5b_ecossistema_personagem_id(conn) -> list[dict]:
    """
    Lista TODAS as tabelas do banco que tem alguma coluna chamada
    'personagem_id'. Captura tabelas que pertencem ao ecossistema
    do protagonista mesmo sem ter 'personagem' no nome.
    """
    sql = text("""
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name IN ('personagem_id', 'personagens_id', 'protagonista_id', 'pc_id', 'character_id')
        ORDER BY table_name, column_name
    """)
    result = await conn.execute(sql)
    return [
        {
            "tabela": row[0],
            "coluna": row[1],
            "tipo": row[2],
            "nullable": row[3] == "YES",
        }
        for row in result.fetchall()
    ]


# ====================================================================
# PERGUNTA 6 - Funcoes/RPCs relacionadas a personagem
# ====================================================================

async def pergunta_6_funcoes(conn) -> list[dict]:
    """
    Lista todas as funcoes do schema public cujo nome OU corpo
    mencione personagem/character/protagonista.
    """
    sql = text("""
        SELECT
            p.proname,
            pg_get_function_identity_arguments(p.oid) AS parametros,
            pg_get_function_result(p.oid) AS retorno,
            pg_get_functiondef(p.oid) AS codigo_fonte,
            l.lanname AS linguagem
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_language l ON l.oid = p.prolang
        WHERE n.nspname = 'public'
          AND p.prokind = 'f'
          AND (
              p.proname ILIKE '%personagem%'
              OR p.proname ILIKE '%character%'
              OR p.proname ILIKE '%protagonista%'
              OR p.proname ILIKE '%criar_pc%'
              OR p.proname ILIKE '%level_up%'
              OR p.proname ILIKE '%anima%'
              OR p.proname ILIKE '%maestria%'
          )
        ORDER BY p.proname
    """)
    result = await conn.execute(sql)
    return [
        {
            "nome": row[0],
            "parametros": row[1],
            "retorno": row[2],
            "linguagem": row[4],
            "codigo_fonte": row[3],
        }
        for row in result.fetchall()
    ]


# ====================================================================
# PERGUNTA 7 - Estatisticas (row count, tamanho, triggers, views)
# ====================================================================

async def pergunta_7_estatisticas(conn, tabela: str) -> dict:
    """Coleta estatisticas e metadados sobre a tabela."""
    nome_seguro = validar_nome_tabela(tabela)

    # Row count (SQL dinamico, mas nome ja validado)
    row_count_sql = text(f"SELECT count(*) FROM public.{nome_seguro}")
    rc = await conn.execute(row_count_sql)
    row_count = rc.scalar()

    # Tamanho em disco
    size_sql = text("""
        SELECT
            pg_total_relation_size(c.oid) AS total_bytes,
            pg_relation_size(c.oid) AS table_bytes,
            pg_indexes_size(c.oid) AS indexes_bytes
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = :tabela
    """)
    sz = await conn.execute(size_sql, {"tabela": tabela})
    sz_row = sz.fetchone()
    tamanho = {
        "total_bytes": sz_row[0] if sz_row else 0,
        "tabela_bytes": sz_row[1] if sz_row else 0,
        "indices_bytes": sz_row[2] if sz_row else 0,
    } if sz_row else {}

    # Triggers
    trigger_sql = text("""
        SELECT trigger_name, event_manipulation, action_timing, action_statement
        FROM information_schema.triggers
        WHERE event_object_schema = 'public' AND event_object_table = :tabela
        ORDER BY trigger_name
    """)
    tr = await conn.execute(trigger_sql, {"tabela": tabela})
    triggers = [
        {
            "nome": row[0],
            "evento": row[1],
            "timing": row[2],
            "acao": row[3],
        }
        for row in tr.fetchall()
    ]

    # Views que dependem
    view_sql = text("""
        SELECT DISTINCT v.viewname
        FROM pg_views v
        WHERE v.schemaname = 'public'
          AND v.definition ILIKE '%' || :tabela || '%'
        ORDER BY v.viewname
    """)
    vr = await conn.execute(view_sql, {"tabela": tabela})
    views = [row[0] for row in vr.fetchall()]

    return {
        "row_count": row_count,
        "tamanho": tamanho,
        "triggers": triggers,
        "views_dependentes": views,
    }


# ====================================================================
# ORQUESTRADOR PRINCIPAL
# ====================================================================

async def main() -> None:
    print("=" * 60)
    print("PESQUISA 1 - Schema completo de Personagens")
    print("=" * 60)
    print()

    async with engine.connect() as conn:
        # â”€â”€â”€ Pergunta 1 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print("[1/8] Descobrindo tabelas (personagens, personagem_*, character_*)...")
        tabelas = await pergunta_1_descobrir_tabelas(conn)
        print(f"      Encontradas: {len(tabelas)} tabelas")
        for t in tabelas:
            print(f"      - {t}")
        print()

        # â”€â”€â”€ Perguntas 2-5 + 7 (por tabela) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€â”€ Pergunta 5B â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print("[5B/8] Listando tabelas com coluna 'personagem_id' (ecossistema)...")
        ecossistema = await pergunta_5b_ecossistema_personagem_id(conn)
        print(f"       Encontradas: {len(ecossistema)} colunas em outras tabelas")
        print()

        # â”€â”€â”€ Pergunta 6 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print("[6/8] Procurando funcoes/RPCs relacionadas a personagem...")
        funcoes = await pergunta_6_funcoes(conn)
        print(f"      Encontradas: {len(funcoes)} funcoes")
        for f in funcoes[:10]:
            print(f"      - {f['nome']}({f['parametros']})")
        if len(funcoes) > 10:
            print(f"      ... e mais {len(funcoes) - 10}")
        print()

    # â”€â”€â”€ Serializa em JSON â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn (ep-calm-shadow-any1pg3i)",
        "padroes_buscados": ["personagens", "personagem_%", "character_%"],
        "total_tabelas_encontradas": len(tabelas),
        "tabelas": dados_tabelas,
        "ecossistema_personagem_id": ecossistema,
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