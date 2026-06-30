"""
Pesquisa 14 da Catedral - Magia e familias magicas.

O maior catalogo restante: 2231 magias em 42 familias. Estrategia de amostragem
em 3 camadas: schemas completos + agregacoes massivas + amostras estrategicas.

Saida: pesquisa_14_magia.json (estimado 250-450 KB)
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


OUTPUT_FILE = "pesquisa_14_magia.json"
SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def validar(nome: str) -> str:
    if not SAFE_NAME.match(nome):
        raise ValueError(f"Nome inseguro: {nome!r}")
    return nome


# ====================================================================
# QUERIES HELPERS
# ====================================================================

async def schema_completo(conn, tabela: str) -> dict:
    nome_seg = validar(tabela)
    cols_sql = text("""
        SELECT ordinal_position, column_name, data_type, udt_name,
               is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :t
        ORDER BY ordinal_position
    """)
    res = await conn.execute(cols_sql, {"t": tabela})
    colunas = [
        {
            "posicao": r[0], "nome": r[1], "tipo": r[2],
            "tipo_postgres": r[3], "nullable": r[4] == "YES",
            "default": r[5],
        }
        for r in res.fetchall()
    ]

    cons_sql = text("""
        SELECT con.conname, con.contype, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public' AND rel.relname = :t
        ORDER BY con.contype, con.conname
    """)
    res = await conn.execute(cons_sql, {"t": tabela})
    constraints = []
    for r in res.fetchall():
        tc = r[1]
        if hasattr(tc, "decode"):
            tc = tc.decode()
        constraints.append({"nome": r[0], "tipo": tc, "definicao": r[2]})

    rc = await conn.execute(text(f"SELECT count(*) FROM public.{nome_seg}"))
    row_count = rc.scalar()

    return {
        "n_cols": len(colunas),
        "row_count": row_count,
        "colunas": colunas,
        "constraints": constraints,
    }


async def tabela_existe(conn, tabela: str) -> bool:
    nome_seg = validar(tabela)
    sql = text("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema='public' AND table_name=:t
    """)
    row = (await conn.execute(sql, {"t": tabela})).fetchone()
    return row is not None


async def distribuicao(conn, tabela: str, coluna: str) -> dict:
    nome_seg = validar(tabela)
    col_seg = validar(coluna)
    try:
        sql = text(f"""
            SELECT {col_seg} AS valor, COUNT(*) AS total
            FROM public.{nome_seg}
            WHERE {col_seg} IS NOT NULL
            GROUP BY {col_seg}
            ORDER BY total DESC, {col_seg}
        """)
        res = await conn.execute(sql)
        return {str(r[0]): r[1] for r in res.fetchall()}
    except Exception as e:
        return {"erro": str(e)}


async def codigo_funcao(conn, nome_funcao: str) -> dict:
    sql = text("""
        SELECT pg_get_functiondef(p.oid),
               pg_get_function_identity_arguments(p.oid),
               pg_get_function_result(p.oid)
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname='public' AND p.proname=:nome
        LIMIT 1
    """)
    row = (await conn.execute(sql, {"nome": nome_funcao})).fetchone()
    if row:
        return {
            "existe": True,
            "parametros": row[1],
            "retorno": row[2],
            "codigo_fonte": row[0],
        }
    return {"existe": False}


# ====================================================================
# ORQUESTRADOR
# ====================================================================

async def main() -> None:
    print("=" * 60)
    print("PESQUISA 14 - Magia (2231 magias, 42 familias)")
    print("=" * 60)
    print()

    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn",
        "objetivo": "Mapear o maior catalogo restante: 2231 magias em 42 familias magicas",
        "tabelas": {},
        "agregacoes": {},
        "amostras": {},
        "rpcs": {},
        "rpcs_por_busca": [],
    }

    async with engine.connect() as conn:
        # ============================================================
        # 1. DESCOBERTA DE TABELAS RELEVANTES
        # ============================================================
        print("[1/8] Descobrindo tabelas relacionadas a magia...")
        sql = text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public'
              AND (table_name ILIKE '%magia%'
                   OR table_name ILIKE '%magic%'
                   OR table_name ILIKE '%feiti%'
                   OR table_name ILIKE '%familia%'
                   OR table_name ILIKE '%escola%'
                   OR table_name ILIKE '%slot%'
                   OR table_name ILIKE '%encanta%')
            ORDER BY table_name
        """)
        res = await conn.execute(sql)
        tabelas_relacionadas = [r[0] for r in res.fetchall()]
        resultado["tabelas_descobertas"] = tabelas_relacionadas
        for t in tabelas_relacionadas:
            print(f"      - {t}")
        print()

        # ============================================================
        # 2. SCHEMA COMPLETO DE magias + TABELAS DE SUPORTE
        # ============================================================
        print("[2/8] Schemas completos das tabelas centrais...")
        TABELAS_ALVO = [
            "magias",
            "ref_familias_magicas",
            "ref_escolas_magia",
            "ref_magias",
            "personagem_magias",
            "personagem_familias_magicas",
            "ref_vocacoes_familias_magicas",
            "magias_preparadas",
            "slots_magicos",
        ]
        for t in TABELAS_ALVO:
            if await tabela_existe(conn, t):
                print(f"      {t}...", end="")
                resultado["tabelas"][t] = await schema_completo(conn, t)
                print(f" {resultado['tabelas'][t]['n_cols']} cols, {resultado['tabelas'][t]['row_count']} rows")
            else:
                print(f"      {t}... NAO EXISTE")
        print()

        # ============================================================
        # 3. AGREGACOES DE magias
        # ============================================================
        print("[3/8] Agregacoes massivas de magias...")

        # 3a. Descobrir quais colunas existem antes de agregacoes
        cols_magias = []
        if "magias" in resultado["tabelas"]:
            cols_magias = [c["nome"] for c in resultado["tabelas"]["magias"]["colunas"]]
            print(f"      (magias tem {len(cols_magias)} colunas)")

        # 3b. Distribuicao por familia
        for candidato in ["familia", "familia_magica", "familia_id", "escola", "escola_magia"]:
            if candidato in cols_magias:
                print(f"      distribuicao por {candidato}...")
                dist = await distribuicao(conn, "magias", candidato)
                resultado["agregacoes"][f"por_{candidato}"] = dist
                print(f"         {len(dist)} valores unicos")

        # 3c. Distribuicao por nivel
        for candidato in ["nivel", "circulo", "nivel_minimo", "circulo_magico"]:
            if candidato in cols_magias:
                print(f"      distribuicao por {candidato}...")
                dist = await distribuicao(conn, "magias", candidato)
                resultado["agregacoes"][f"por_{candidato}"] = dist

        # 3d. Distribuicao por tipo
        for candidato in ["tipo", "tipo_magia", "categoria", "classe"]:
            if candidato in cols_magias:
                dist = await distribuicao(conn, "magias", candidato)
                resultado["agregacoes"][f"por_{candidato}"] = dist

        # 3e. Distribuicao por fonte (FR vs Alderyn vs SRD)
        for candidato in ["fonte", "origem", "homebrew", "nativa"]:
            if candidato in cols_magias:
                dist = await distribuicao(conn, "magias", candidato)
                resultado["agregacoes"][f"por_{candidato}"] = dist

        # 3f. Quantas tem custo_mp / hp / slot
        for candidato in ["custo_mp", "consome_hp", "custo_especial", "concentracao", "ritual"]:
            if candidato in cols_magias:
                sql = text(f"""
                    SELECT
                        COUNT(*) FILTER (WHERE {candidato} IS NOT NULL) AS preenchidas,
                        COUNT(*) AS total
                    FROM magias
                """)
                row = (await conn.execute(sql)).fetchone()
                resultado["agregacoes"][f"cobertura_{candidato}"] = {
                    "preenchidas": row[0], "total": row[1]
                }

        print()

        # ============================================================
        # 4. AGREGACAO CRUZADA familia x nivel
        # ============================================================
        print("[4/8] Agregacao cruzada familia x nivel...")

        col_fam = None
        for c in ["familia", "familia_magica", "familia_id"]:
            if c in cols_magias:
                col_fam = c
                break

        col_nivel = None
        for c in ["nivel", "circulo"]:
            if c in cols_magias:
                col_nivel = c
                break

        if col_fam and col_nivel:
            cf = validar(col_fam)
            cn = validar(col_nivel)
            sql = text(f"""
                SELECT {cf} AS familia, {cn} AS nivel, COUNT(*) AS total
                FROM magias
                GROUP BY {cf}, {cn}
                ORDER BY {cf}, {cn}
            """)
            res = await conn.execute(sql)
            resultado["agregacoes"]["familia_x_nivel"] = [
                {"familia": str(r[0]), "nivel": r[1], "total": r[2]}
                for r in res.fetchall()
            ]
            print(f"      OK ({len(resultado['agregacoes']['familia_x_nivel'])} combinacoes)")
        else:
            print(f"      (pulado: familia='{col_fam}' nivel='{col_nivel}')")

        # 4b. Cobertura por familia: total por familia
        if col_fam:
            cf = validar(col_fam)
            sql = text(f"""
                SELECT {cf} AS familia, COUNT(*) AS total,
                       MIN({col_nivel}) AS min_nivel,
                       MAX({col_nivel}) AS max_nivel
                FROM magias
                GROUP BY {cf}
                ORDER BY total DESC
            """) if col_nivel else text(f"""
                SELECT {cf} AS familia, COUNT(*) AS total
                FROM magias
                GROUP BY {cf}
                ORDER BY total DESC
            """)
            res = await conn.execute(sql)
            resultado["agregacoes"]["cobertura_por_familia"] = [
                dict(zip(["familia", "total", "min_nivel", "max_nivel"], r))
                for r in res.fetchall()
            ]
        print()

        # ============================================================
        # 5. AMOSTRAS ESTRATEGICAS
        # ============================================================
        print("[5/8] Amostras estrategicas...")

        # 5a. 3 magias aleatorias de cada familia
        if col_fam:
            cf = validar(col_fam)
            print(f"      3 magias por familia (amostra representativa)...")
            sql = text(f"""
                SELECT DISTINCT ON ({cf}, rn) *
                FROM (
                    SELECT m.*,
                        ROW_NUMBER() OVER (PARTITION BY {cf} ORDER BY id) AS rn
                    FROM magias m
                ) sub
                WHERE rn <= 3
                ORDER BY {cf}, rn
            """)
            try:
                res = await conn.execute(sql)
                resultado["amostras"]["por_familia_3_cada"] = [
                    dict(r) for r in res.mappings().all()
                ]
                print(f"         {len(resultado['amostras']['por_familia_3_cada'])} linhas")
            except Exception as e:
                print(f"         erro: {e}")
                resultado["amostras"]["por_familia_3_cada"] = [{"erro": str(e)}]

        # 5b. Top 5 magias de nivel mais alto (capstones) - uma por familia
        if col_fam and col_nivel:
            cf = validar(col_fam)
            cn = validar(col_nivel)
            print(f"      magias capstone (nivel max) por familia...")
            sql = text(f"""
                SELECT DISTINCT ON ({cf}) *
                FROM magias
                ORDER BY {cf}, {cn} DESC, id
            """)
            try:
                res = await conn.execute(sql)
                resultado["amostras"]["capstones"] = [
                    dict(r) for r in res.mappings().all()
                ]
                print(f"         {len(resultado['amostras']['capstones'])} capstones")
            except Exception as e:
                resultado["amostras"]["capstones"] = [{"erro": str(e)}]

        # 5c. Busca por magias 5e classicas (contaminacao FR)
        print(f"      busca por magias SRD 5e classicas...")
        nomes_srd = [
            "Fireball", "Magic Missile", "Cure Wounds", "Mage Armor",
            "Shield", "Eldritch Blast", "Bola de Fogo", "Misseis Magicos",
            "Curar Ferimentos", "Armadura Arcana"
        ]
        achados_srd = []
        for nome in nomes_srd:
            sql = text("""
                SELECT id, nome FROM magias
                WHERE nome ILIKE :padrao
                LIMIT 3
            """)
            res = await conn.execute(sql, {"padrao": f"%{nome}%"})
            for r in res.fetchall():
                achados_srd.append({"buscado": nome, "id": r[0], "nome": r[1]})
        resultado["amostras"]["srd_5e_hits"] = achados_srd
        print(f"         {len(achados_srd)} hits")

        print()

        # ============================================================
        # 6. RPCs DO DOMINIO MAGIA
        # ============================================================
        print("[6/8] RPCs do dominio magia...")
        RPCS_ALVO = [
            "aprender_magia",
            "lancar_magia",
            "esquecer_magia",
            "preparar_magia",
            "get_magias_disponiveis",
            "get_magias_personagem",
            "get_magias_por_familia",
            "get_magias_por_nivel",
            "get_magias_por_vocacao",
            "calcular_custo_mp",
            "calcular_dano_magia",
            "verificar_pre_requisitos_magia",
            "recuperar_slots_magicos",
            "conceder_magias_iniciais",
            "conceder_magias_nivel",
            "registrar_magia_conhecida",
            "get_familias_magicas_vocacao",
            "registrar_uso_magia",
        ]
        existentes = 0
        for nome in RPCS_ALVO:
            print(f"      {nome}...", end="")
            info = await codigo_funcao(conn, nome)
            resultado["rpcs"][nome] = info
            if info.get("existe"):
                print(" OK")
                existentes += 1
            else:
                print(" NAO")
        print(f"      Encontradas: {existentes}/{len(RPCS_ALVO)}")
        print()

        # ============================================================
        # 7. BUSCA POR PADROES ADICIONAIS
        # ============================================================
        print("[7/8] Busca por padroes adicionais...")
        padroes = ["magia", "feiti", "slot", "familia_mag", "mp", "mana",
                   "ritual", "conjur", "lancar", "preparar"]
        for pad in padroes:
            sql = text(f"""
                SELECT proname FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname='public'
                  AND p.prolang = (SELECT oid FROM pg_language WHERE lanname='plpgsql')
                  AND proname ILIKE '%{pad}%'
                ORDER BY proname
            """)
            res = await conn.execute(sql)
            funcs = [r[0] for r in res.fetchall()]
            if funcs:
                print(f"      {pad}: {len(funcs)}")
                resultado["rpcs_por_busca"].append({"padrao": pad, "funcoes": funcs})
        print()

        # ============================================================
        # 8. DUMPS ESPECIFICOS DE 2 FAMILIAS EXEMPLARES
        # ============================================================
        print("[8/8] Dumps de familias exemplares...")

        if col_fam:
            cf = validar(col_fam)
            # Descobrir top 2 familias por cobertura
            sql = text(f"SELECT {cf}, COUNT(*) FROM magias GROUP BY {cf} ORDER BY COUNT(*) DESC LIMIT 2")
            res = await conn.execute(sql)
            top2 = [r[0] for r in res.fetchall()]

            for fam in top2:
                if fam is None:
                    continue
                print(f"      dump de familia: {fam}")
                sql = text(f"""
                    SELECT * FROM magias WHERE {cf} = :fam ORDER BY id
                """)
                res = await conn.execute(sql, {"fam": fam})
                dump = [dict(r) for r in res.mappings().all()]
                resultado["amostras"][f"dump_familia_{fam}"] = dump
                print(f"         {len(dump)} magias")
        print()

    # Salva
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

    import os
    tam_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("=" * 60)
    print(f"OK Arquivo salvo: {OUTPUT_FILE}")
    print(f"   Tamanho: {tam_kb:.1f} KB")
    print(f"   Tabelas descobertas: {len(resultado.get('tabelas_descobertas', []))}")
    print(f"   Tabelas mapeadas: {len(resultado['tabelas'])}")
    print(f"   RPCs OK: {existentes}/{len(RPCS_ALVO)}")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())