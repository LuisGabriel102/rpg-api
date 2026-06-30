"""
Pesquisa 7 da Catedral - Estrelas do Veu e habilidades astrais.

Fecha o trio de criacao de personagem (vocacao/caminho/astro). Cataloga as 12
estrelas completas (dump), amostra estrategica das 1200 habilidades por estrela,
e investiga o sistema de evolucao em graus + pagamento de precos.

Saida: pesquisa_7_estrelas_veu.json (estimado 100-180 KB)
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


OUTPUT_FILE = "pesquisa_7_estrelas_veu.json"

SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def validar(nome: str) -> str:
    if not SAFE_NAME.match(nome):
        raise ValueError(f"Nome inseguro: {nome!r}")
    return nome


# ====================================================================
# QUERIES
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
            "posicao": row[0], "nome": row[1], "tipo": row[2],
            "tipo_postgres": row[3], "nullable": row[4] == "YES",
            "default": row[5],
        }
        for row in res.fetchall()
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
    for row in res.fetchall():
        tc = row[1]
        if hasattr(tc, 'decode'):
            tc = tc.decode()
        constraints.append({
            "nome": row[0], "tipo": tc, "definicao": row[2],
        })

    rc = await conn.execute(text(f"SELECT count(*) FROM public.{nome_seg}"))
    row_count = rc.scalar()

    return {
        "n_cols": len(colunas),
        "row_count": row_count,
        "colunas": colunas,
        "constraints": constraints,
    }


async def dump_completo(conn, tabela: str) -> list:
    nome_seg = validar(tabela)
    try:
        sql = text(f"SELECT * FROM public.{nome_seg} ORDER BY id")
        res = await conn.execute(sql)
        return [dict(r) for r in res.mappings().all()]
    except Exception as e:
        return [{"erro": str(e)}]


async def codigo_funcao(conn, nome_funcao: str) -> dict:
    sql = text("""
        SELECT pg_get_functiondef(p.oid),
               pg_get_function_identity_arguments(p.oid),
               pg_get_function_result(p.oid)
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public' AND p.proname = :nome
        LIMIT 1
    """)
    res = await conn.execute(sql, {"nome": nome_funcao})
    row = res.fetchone()
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
    print("PESQUISA 7 - Estrelas do Veu")
    print("=" * 60)
    print()

    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn",
        "objetivo": "Fechar o trio de criacao: mapear 12 estrelas + 1200 habilidades astrais",
        "estrelas": {},
        "habilidades": {},
        "personagem_astro_nascimento_schema": {},
        "agregacoes": {},
        "rpcs": {},
        "rpcs_por_busca": [],
    }

    async with engine.connect() as conn:
        # ============================================================
        # 1. DUMP COMPLETO de ref_estrelas_nascimento (12 linhas)
        # ============================================================
        print("[1/7] Dump completo de ref_estrelas_nascimento (12 linhas)...")
        resultado["estrelas"]["schema"] = await schema_completo(conn, "ref_estrelas_nascimento")
        resultado["estrelas"]["dump"] = await dump_completo(conn, "ref_estrelas_nascimento")
        print(f"      OK: {len(resultado['estrelas']['dump'])} estrelas")
        print()

        # ============================================================
        # 2. SCHEMA de ref_habilidades_estrela
        # ============================================================
        print("[2/7] Schema de ref_habilidades_estrela...")
        resultado["habilidades"]["schema"] = await schema_completo(conn, "ref_habilidades_estrela")
        print(f"      cols={resultado['habilidades']['schema']['n_cols']}  rows={resultado['habilidades']['schema']['row_count']}")
        print()

        # ============================================================
        # 3. AGREGACOES DE ref_habilidades_estrela
        # ============================================================
        print("[3/7] Agregacoes de ref_habilidades_estrela...")

        # 3a. Contagem por estrela (verificar se todas tem 100)
        print("      contagem por estrela (deve ser 100 cada)...")
        sql = text("""
            SELECT e.id, e.nome, e.epiteto, COUNT(h.id) AS total_habs
            FROM ref_estrelas_nascimento e
            LEFT JOIN ref_habilidades_estrela h ON h.estrela_id = e.id
            GROUP BY e.id, e.nome, e.epiteto
            ORDER BY e.id
        """)
        res = await conn.execute(sql)
        resultado["agregacoes"]["contagem_por_estrela"] = [
            {"estrela_id": r[0], "nome": r[1], "epiteto": r[2], "total": r[3]}
            for r in res.fetchall()
        ]
        print(f"      OK")

        # 3b. Contagem por (estrela, categoria)
        print("      contagem por (estrela, categoria)...")
        sql = text("""
            SELECT estrela_id, categoria, COUNT(*) AS total
            FROM ref_habilidades_estrela
            GROUP BY estrela_id, categoria
            ORDER BY estrela_id, categoria
        """)
        res = await conn.execute(sql)
        resultado["agregacoes"]["por_estrela_categoria"] = [
            {"estrela_id": r[0], "categoria": r[1], "total": r[2]}
            for r in res.fetchall()
        ]
        print(f"      OK")

        # 3c. Verificar se numero_d100 vai de 1 a 100 pra cada estrela
        print("      verificar range de numero_d100 por estrela...")
        sql = text("""
            SELECT estrela_id,
                   MIN(numero_d100) AS min_d,
                   MAX(numero_d100) AS max_d,
                   COUNT(DISTINCT numero_d100) AS distinct_d
            FROM ref_habilidades_estrela
            GROUP BY estrela_id
            ORDER BY estrela_id
        """)
        res = await conn.execute(sql)
        resultado["agregacoes"]["range_d100_por_estrela"] = [
            {"estrela_id": r[0], "min_d100": r[1], "max_d100": r[2], "distinct": r[3]}
            for r in res.fetchall()
        ]
        print(f"      OK")

        # 3d. Distribuicao de tem_preco
        print("      distribuicao tem_preco...")
        sql = text("""
            SELECT tem_preco, COUNT(*) AS total
            FROM ref_habilidades_estrela
            GROUP BY tem_preco
        """)
        res = await conn.execute(sql)
        resultado["agregacoes"]["tem_preco_dist"] = [
            {"tem_preco": r[0], "total": r[1]} for r in res.fetchall()
        ]

        # 3e. Quantas habilidades sao 'legendary' (d100=100) realmente existem?
        print("      verificar habilidades d100=100 (lendarias)...")
        sql = text("""
            SELECT estrela_id, COUNT(*)
            FROM ref_habilidades_estrela
            WHERE numero_d100 = 100
            GROUP BY estrela_id
            ORDER BY estrela_id
        """)
        res = await conn.execute(sql)
        resultado["agregacoes"]["d100_100_por_estrela"] = [
            {"estrela_id": r[0], "total": r[1]} for r in res.fetchall()
        ]

        print()

        # ============================================================
        # 4. AMOSTRA ESTRATEGICA DE HABILIDADES
        # ============================================================
        print("[4/7] Amostra estrategica de habilidades...")

        # 4a. As 12 habilidades lendarias completas (d100=100, uma por estrela)
        print("      dump das 12 lendarias (d100=100)...")
        sql = text("""
            SELECT h.*
            FROM ref_habilidades_estrela h
            WHERE h.numero_d100 = 100
            ORDER BY h.estrela_id
        """)
        res = await conn.execute(sql)
        resultado["habilidades"]["lendarias_d100"] = [dict(r) for r in res.mappings().all()]

        # 4b. 2 habilidades categoria 3 aleatorias de cada estrela (amostra rara)
        print("      2 categoria 3 por estrela (24 total)...")
        sql = text("""
            SELECT h.*, e.nome AS estrela_nome
            FROM ref_habilidades_estrela h
            JOIN ref_estrelas_nascimento e ON e.id = h.estrela_id
            WHERE h.categoria = 3
              AND h.numero_d100 != 100
            ORDER BY h.estrela_id, h.numero_d100
        """)
        res = await conn.execute(sql)
        todas = [dict(r) for r in res.mappings().all()]
        # Pega 2 primeiras por estrela
        por_estrela = {}
        for h in todas:
            eid = h['estrela_id']
            if eid not in por_estrela:
                por_estrela[eid] = []
            if len(por_estrela[eid]) < 2:
                por_estrela[eid].append(h)
        amostra_cat3 = []
        for eid in sorted(por_estrela.keys()):
            amostra_cat3.extend(por_estrela[eid])
        resultado["habilidades"]["amostra_categoria_3"] = amostra_cat3

        # 4c. 1 habilidade com tem_preco=true de cada estrela (se existir)
        print("      amostra com precos witcher-grey...")
        sql = text("""
            SELECT DISTINCT ON (h.estrela_id) h.*, e.nome AS estrela_nome
            FROM ref_habilidades_estrela h
            JOIN ref_estrelas_nascimento e ON e.id = h.estrela_id
            WHERE h.tem_preco = TRUE
            ORDER BY h.estrela_id, h.numero_d100
        """)
        res = await conn.execute(sql)
        resultado["habilidades"]["amostra_com_preco"] = [dict(r) for r in res.mappings().all()]

        # 4d. 3 habilidades categoria 1 (comuns) da estrela 1 (MARKA)
        print("      3 categoria 1 de MARKA (comuns)...")
        sql = text("""
            SELECT * FROM ref_habilidades_estrela
            WHERE estrela_id = 1 AND categoria = 1
            ORDER BY numero_d100
            LIMIT 3
        """)
        res = await conn.execute(sql)
        resultado["habilidades"]["amostra_marka_cat1"] = [dict(r) for r in res.mappings().all()]

        print()

        # ============================================================
        # 5. SCHEMA de personagem_astro_nascimento (revisar)
        # ============================================================
        print("[5/7] Schema de personagem_astro_nascimento...")
        resultado["personagem_astro_nascimento_schema"] = await schema_completo(
            conn, "personagem_astro_nascimento"
        )
        print()

        # ============================================================
        # 6. RPCs DO DOMINIO
        # ============================================================
        print("[6/7] RPCs do dominio astro...")
        RPCS_ALVO = [
            "definir_astro_nascimento",
            "definir_astro_nascimento_sorteado",
            "definir_astro_npc",
            "evoluir_habilidade_astral",
            "conceder_grau5_maestria",
            "registrar_habilidade_innata",
            "registrar_habilidade_bonus",
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
                print(" NAO EXISTE")
        print(f"      Encontradas: {existentes}/{len(RPCS_ALVO)}")
        print()

        # ============================================================
        # 7. BUSCA POR PADROES
        # ============================================================
        print("[7/7] Busca por padroes adicionais...")
        padroes = ["estrela", "astro", "astral", "sombra", "veu", "grau", "legado"]
        for pad in padroes:
            sql = text(f"""
                SELECT proname FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'public'
                  AND p.prolang = (SELECT oid FROM pg_language WHERE lanname='plpgsql')
                  AND proname ILIKE '%{pad}%'
                ORDER BY proname
            """)
            res = await conn.execute(sql)
            funcs = [r[0] for r in res.fetchall()]
            resultado["rpcs_por_busca"].append({"padrao": pad, "funcoes": funcs})
            if funcs:
                print(f"      {pad}: {len(funcs)} funcoes")
        print()

    # Salva
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

    import os
    tam_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("=" * 60)
    print(f"OK Arquivo salvo: {OUTPUT_FILE}")
    print(f"   Tamanho: {tam_kb:.1f} KB")
    print(f"   Estrelas: {len(resultado['estrelas']['dump'])}")
    print(f"   Lendarias: {len(resultado['habilidades']['lendarias_d100'])}")
    print(f"   Amostra cat 3: {len(resultado['habilidades']['amostra_categoria_3'])}")
    print(f"   Amostra precos: {len(resultado['habilidades']['amostra_com_preco'])}")
    print(f"   RPCs OK: {existentes}/{len(RPCS_ALVO)}")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())