"""
Pesquisa 6 da Catedral - Vocacoes e Caminhos.

Primeira pesquisa focada em um dominio Alderyn-native puro. 126 vocacoes,
88 caminhos, 320 habilidades por classe/nivel. Catalogo em PT-BR, curado.

Estrategia diferente: como os catalogos sao pequenos o bastante, DUMP COMPLETO
de ref_vocacoes (126) e ref_caminhos (88). Pra ref_habilidades_classe_nivel
(320), faz agregacoes + amostra.

Saida: pesquisa_6_vocacoes.json (estimado 200-400 KB)
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


OUTPUT_FILE = "pesquisa_6_vocacoes.json"

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
    """Puxa TODAS as linhas (pra catalogos pequenos)."""
    nome_seg = validar(tabela)
    try:
        sql = text(f"SELECT * FROM public.{nome_seg} ORDER BY id")
        res = await conn.execute(sql)
        return [dict(r) for r in res.mappings().all()]
    except Exception as e:
        return [{"erro": str(e)}]


async def amostra_dados(conn, tabela: str, n: int = 10) -> list:
    nome_seg = validar(tabela)
    try:
        sql = text(f"SELECT * FROM public.{nome_seg} ORDER BY id LIMIT {n}")
        res = await conn.execute(sql)
        return [dict(r) for r in res.mappings().all()]
    except Exception as e:
        return [{"erro": str(e)}]


async def distribuicao(conn, tabela: str, coluna: str) -> dict:
    """Conta valores unicos de uma coluna (COUNT GROUP BY)."""
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
        return {str(row[0]): row[1] for row in res.fetchall()}
    except Exception as e:
        return {"erro": str(e)}


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


async def busca_funcoes(conn, padroes: list) -> list:
    where = " OR ".join([f"proname ILIKE '%{p}%'" for p in padroes])
    sql = text(f"""
        SELECT proname FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND p.prolang = (SELECT oid FROM pg_language WHERE lanname='plpgsql')
          AND ({where})
        ORDER BY proname
    """)
    res = await conn.execute(sql)
    return [row[0] for row in res.fetchall()]


# ====================================================================
# ORQUESTRADOR
# ====================================================================

async def main() -> None:
    print("=" * 60)
    print("PESQUISA 6 - Vocacoes e Caminhos")
    print("=" * 60)
    print()

    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn",
        "objetivo": "Mapear sistema de progressao de classes (vocacoes, caminhos, habilidades por nivel)",
        "catalogos": {},
        "instancias": {},
        "agregacoes": {},
        "rpcs": {},
        "rpcs_por_busca": [],
    }

    async with engine.connect() as conn:
        # 1. DUMP COMPLETO DE ref_vocacoes (126 linhas)
        print("[1/7] Dump completo de ref_vocacoes (126 linhas)...")
        resultado["catalogos"]["ref_vocacoes"] = {
            "schema": await schema_completo(conn, "ref_vocacoes"),
            "dump_completo": await dump_completo(conn, "ref_vocacoes"),
        }
        print(f"      OK: {len(resultado['catalogos']['ref_vocacoes']['dump_completo'])} linhas")
        print()

        # 2. DUMP COMPLETO DE ref_caminhos (88 linhas)
        print("[2/7] Dump completo de ref_caminhos (88 linhas)...")
        resultado["catalogos"]["ref_caminhos"] = {
            "schema": await schema_completo(conn, "ref_caminhos"),
            "dump_completo": await dump_completo(conn, "ref_caminhos"),
        }
        print(f"      OK: {len(resultado['catalogos']['ref_caminhos']['dump_completo'])} linhas")
        print()

        # 3. ref_habilidades_classe_nivel (320 linhas) - schema + amostra + agregacoes
        print("[3/7] ref_habilidades_classe_nivel (schema + 15 amostras + agregacoes)...")
        resultado["catalogos"]["ref_habilidades_classe_nivel"] = {
            "schema": await schema_completo(conn, "ref_habilidades_classe_nivel"),
            "amostra": await amostra_dados(conn, "ref_habilidades_classe_nivel", 15),
        }
        print()

        # 4. AGREGACOES ESTRATEGICAS
        print("[4/7] Agregacoes estrategicas...")

        # Distribuicao de 'pilar' em vocacoes
        print("      pilares (ref_vocacoes.pilar)...")
        resultado["agregacoes"]["vocacoes_por_pilar"] = await distribuicao(
            conn, "ref_vocacoes", "pilar"
        )

        # Distribuicao de 'tipo' em vocacoes
        print("      tipos (ref_vocacoes.tipo)...")
        resultado["agregacoes"]["vocacoes_por_tipo"] = await distribuicao(
            conn, "ref_vocacoes", "tipo"
        )

        # Distribuicao de 'disponivel_escolha'
        print("      disponibilidade (ref_vocacoes.disponivel_escolha)...")
        resultado["agregacoes"]["vocacoes_disponiveis"] = await distribuicao(
            conn, "ref_vocacoes", "disponivel_escolha"
        )

        # Caminhos agrupados por vocacao_id
        print("      caminhos por vocacao_id...")
        sql = text("""
            SELECT c.vocacao_id, v.nome AS vocacao_nome, COUNT(c.id) AS num_caminhos
            FROM ref_caminhos c
            LEFT JOIN ref_vocacoes v ON v.id = c.vocacao_id
            GROUP BY c.vocacao_id, v.nome
            ORDER BY num_caminhos DESC, vocacao_nome
        """)
        res = await conn.execute(sql)
        resultado["agregacoes"]["caminhos_por_vocacao"] = [
            {"vocacao_id": row[0], "vocacao_nome": row[1], "num_caminhos": row[2]}
            for row in res.fetchall()
        ]

        # Habilidades por classe+nivel
        print("      habilidades por classe (nome/id)...")
        sql = text("""
            SELECT vocacao_id, COUNT(*) AS num_habs,
                   MIN(nivel) AS min_nivel, MAX(nivel) AS max_nivel
            FROM ref_habilidades_classe_nivel
            GROUP BY vocacao_id
            ORDER BY num_habs DESC
            LIMIT 30
        """)
        try:
            res = await conn.execute(sql)
            resultado["agregacoes"]["habilidades_por_vocacao_id"] = [
                {"vocacao_id": row[0], "total": row[1], "min_nivel": row[2], "max_nivel": row[3]}
                for row in res.fetchall()
            ]
        except Exception as e:
            resultado["agregacoes"]["habilidades_por_vocacao_id"] = {"erro": str(e)}

        # Distribuicao por nivel
        print("      habilidades por nivel (1-20)...")
        try:
            sql = text("""
                SELECT nivel, COUNT(*) AS total
                FROM ref_habilidades_classe_nivel
                GROUP BY nivel
                ORDER BY nivel
            """)
            res = await conn.execute(sql)
            resultado["agregacoes"]["habilidades_por_nivel"] = {
                row[0]: row[1] for row in res.fetchall()
            }
        except Exception as e:
            resultado["agregacoes"]["habilidades_por_nivel"] = {"erro": str(e)}

        print()

        # 5. INSTANCIAS personagem_habilidades_classe
        print("[5/7] Schema de personagem_habilidades_classe...")
        resultado["instancias"]["personagem_habilidades_classe"] = {
            "schema": await schema_completo(conn, "personagem_habilidades_classe"),
        }
        print()

        # 6. RPCs ALVO do dominio
        print("[6/7] RPCs do dominio progressao...")
        RPCS_ALVO = [
            "aprender_habilidade",
            "conceder_habilidades_nivel",
            "conceder_habilidades_com_recursos",
            "get_habilidades_nivel",
            "get_habilidades_aprendiveis_disponiveis",
            "get_ficha_classe_completa",
            "get_vocacoes_compativeis",
            "levelUp",
            "escalar_recursos_level_up",
            "registrar_level_up",
            "conceder_grau5_maestria",
            "verificar_pre_requisitos_habilidade",
            "listar_maestrias_personagem",
            "sincronizar_habilidades_innatas",
            "registrar_habilidade_innata",
            "registrar_habilidade_bonus",
            "get_arvore_habilidade",
            "desbloquear_tecnica",
            "get_tecnicas_disponiveis",
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

        # 7. Busca adicional por padrao
        print("[7/7] Busca adicional por padroes...")
        padroes = ["habilidade", "classe", "nivel", "maestria", "tecnica", "recurso", "pilar"]
        for pad in padroes:
            funcs = await busca_funcoes(conn, [pad])
            resultado["rpcs_por_busca"].append({"padrao": pad, "funcoes": funcs})
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
    print(f"   Vocacoes dumpadas: {len(resultado['catalogos']['ref_vocacoes']['dump_completo'])}")
    print(f"   Caminhos dumpados: {len(resultado['catalogos']['ref_caminhos']['dump_completo'])}")
    print(f"   RPCs OK: {existentes}/{len(RPCS_ALVO)}")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())