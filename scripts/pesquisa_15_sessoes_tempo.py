"""
Pesquisa 15 da Catedral - Sessoes e Tempo (segundo hub do banco).

A tabela `sessoes` e referenciada por 66 outras tabelas - quase empatada com
`personagens` (69). Esta pesquisa mapeia o eixo temporal completo do banco:
sessoes, calendario, world_facts, historico, lendas, eventos compartilhados,
registros de alma e estado de campanha.

Saida: pesquisa_15_sessoes_tempo.json (estimado 200-350 KB)
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


OUTPUT_FILE = "pesquisa_15_sessoes_tempo.json"

# === DOMINIO 1: Sessoes ===
TABELAS_SESSAO = [
    "sessoes",
    "sessao_notas",
    "sessao_resumo",
]

# === DOMINIO 2: Tempo / mundo vivo ===
TABELAS_MUNDO_TEMPO = [
    "calendario_campanha",
    "world_facts",
    "historico_mundo",
    "lendas_do_mundo",
    "eventos_compartilhados",
    "registros_de_alma",
    "rpg_events",
]

# === DOMINIO 3: Campanha (contexto) ===
TABELAS_CAMPANHA = [
    "campanhas",
    "campanha_configuracao",
    "campanha_estado_atual",
    "campanha_mapa_revelado",
    "campanha_segredos",
]

TODAS_TABELAS = TABELAS_SESSAO + TABELAS_MUNDO_TEMPO + TABELAS_CAMPANHA

# RPCs candidatas (camelCase intencional - viram do P4)
RPCS_ALVO = [
    "iniciarSessao",
    "encerrarSessao",
    "historicoSessoes",
    "registrar_nota_sessao",
    "registrar_resumo_sessao",
    "get_estado_campanha",
    "atualizar_estado_campanha",
    "avancar_calendario",
    "get_contexto_mundo",
    "get_contexto_enriquecido",
    "revelar_local_mapa",
    "registrar_lenda",
]

SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$", re.IGNORECASE)


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


async def amostra_dados(conn, tabela: str, n: int = 5) -> list:
    nome_seg = validar(tabela)
    try:
        check = await conn.execute(text(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='public' AND table_name='{nome_seg}' AND column_name='id'
            LIMIT 1
        """))
        tem_id = check.scalar() is not None
        order = "ORDER BY id" if tem_id else ""
        sql = text(f"SELECT * FROM public.{nome_seg} {order} LIMIT {n}")
        res = await conn.execute(sql)
        rows = res.mappings().all()
        return [dict(r) for r in rows]
    except Exception as e:
        return [{"erro_amostragem": str(e)}]


async def fks_que_apontam_pra(conn, tabela: str) -> list:
    sql = text("""
        SELECT cls.relname AS tabela_origem,
               att.attname AS coluna_origem,
               con.conname,
               pg_get_constraintdef(con.oid) AS definicao
        FROM pg_constraint con
        JOIN pg_class cls ON cls.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
        JOIN pg_attribute att ON att.attrelid = con.conrelid
                              AND att.attnum = ANY(con.conkey)
        WHERE con.contype = 'f' AND nsp.nspname = 'public'
          AND con.confrelid = (
              SELECT oid FROM pg_class
              WHERE relname = :t
                AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname='public')
          )
        ORDER BY cls.relname, att.attname
    """)
    res = await conn.execute(sql, {"t": tabela})
    return [
        {
            "tabela_origem": row[0],
            "coluna_origem": row[1],
            "constraint": row[2],
            "definicao": row[3],
        }
        for row in res.fetchall()
    ]


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


async def busca_funcoes_por_padrao(conn, padroes: list) -> list:
    """Busca nomes de funcoes plpgsql que casem com algum padrao ILIKE."""
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
    print("PESQUISA 15 - Sessoes e Tempo")
    print("=" * 60)
    print()

    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn",
        "objetivo": "Mapear o eixo temporal completo: sessoes, tempo, mundo vivo, campanha",
        "sessoes": {},
        "mundo_tempo": {},
        "campanha": {},
        "rpcs": {},
        "fks_reversas_sessoes": [],
        "fks_reversas_world_facts": [],
        "fks_reversas_campanhas": [],
        "rpcs_descobertas_por_busca": {},
    }

    async with engine.connect() as conn:
        # 1. SESSOES
        print(f"[1/6] Dominio Sessoes ({len(TABELAS_SESSAO)} tabelas)...")
        for t in TABELAS_SESSAO:
            print(f"      {t}...")
            resultado["sessoes"][t] = {
                "schema": await schema_completo(conn, t),
                "amostra": await amostra_dados(conn, t, 5),
            }
        print()

        # 2. MUNDO/TEMPO
        print(f"[2/6] Dominio Mundo/Tempo ({len(TABELAS_MUNDO_TEMPO)} tabelas)...")
        for t in TABELAS_MUNDO_TEMPO:
            print(f"      {t}...")
            resultado["mundo_tempo"][t] = {
                "schema": await schema_completo(conn, t),
                "amostra": await amostra_dados(conn, t, 5),
            }
        print()

        # 3. CAMPANHA
        print(f"[3/6] Dominio Campanha ({len(TABELAS_CAMPANHA)} tabelas)...")
        for t in TABELAS_CAMPANHA:
            print(f"      {t}...")
            resultado["campanha"][t] = {
                "schema": await schema_completo(conn, t),
                "amostra": await amostra_dados(conn, t, 5),
            }
        print()

        # 4. AS 66 FKs REVERSAS DE SESSOES (mapa do hub)
        print("[4/6] Mapeando 66 FKs que apontam pra sessoes...")
        resultado["fks_reversas_sessoes"] = await fks_que_apontam_pra(conn, "sessoes")
        print(f"      Encontradas: {len(resultado['fks_reversas_sessoes'])}")
        # Tambem world_facts e campanhas pra contexto
        resultado["fks_reversas_world_facts"] = await fks_que_apontam_pra(conn, "world_facts")
        resultado["fks_reversas_campanhas"] = await fks_que_apontam_pra(conn, "campanhas")
        print(f"      world_facts: {len(resultado['fks_reversas_world_facts'])}")
        print(f"      campanhas:   {len(resultado['fks_reversas_campanhas'])}")
        print()

        # 5. RPCs ALVO
        print(f"[5/6] RPCs ({len(RPCS_ALVO)} candidatas)...")
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

        # 6. BUSCA POR PADROES (descobrir funcoes adicionais)
        print("[6/6] Buscando funcoes adicionais por padrao...")
        padroes = ["sessao", "calendario", "tempo", "world", "mundo", "campanha", "lenda", "alma", "fact"]
        for pad in padroes:
            funcs = await busca_funcoes_por_padrao(conn, [pad])
            resultado["rpcs_descobertas_por_busca"][pad] = funcs
        print(f"      Padroes buscados: {len(padroes)}")
        for pad, funcs in resultado["rpcs_descobertas_por_busca"].items():
            if funcs:
                print(f"        {pad}: {len(funcs)} funcoes")
        print()

    # Salva
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

    import os
    tam_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("=" * 60)
    print(f"OK Arquivo salvo: {OUTPUT_FILE}")
    print(f"   Tamanho: {tam_kb:.1f} KB")
    print(f"   Sessoes:    {len(resultado['sessoes'])}")
    print(f"   Mundo/Tempo:{len(resultado['mundo_tempo'])}")
    print(f"   Campanha:   {len(resultado['campanha'])}")
    print(f"   RPCs OK:    {existentes}/{len(RPCS_ALVO)}")
    print(f"   FKs sessoes:{len(resultado['fks_reversas_sessoes'])}")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())