"""
Pesquisa 5 da Catedral - Modo Origem (workflow de criacao de personagem).

Diferente das pesquisas 1-4 (focadas em schemas), esta tambem extrai DADOS REAIS
dos catalogos populados pra entender o formato do conteudo.

Tabelas-alvo (14): 8 catalogos ref_* + 6 instancias personagem_*.
RPCs-alvo: todas que orquestram criacao de personagem.

Saida: pesquisa_5_modo_origem.json (estimado 150-300 KB)
"""

import asyncio
import json
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


OUTPUT_FILE = "pesquisa_5_modo_origem.json"

# Tabelas envolvidas no Modo Origem
CATALOGOS_REF = [
    "ref_racas",
    "ref_subracas",
    "ref_backgrounds",
    "ref_vocacoes",
    "ref_caminhos",
    "ref_eventos_vida",
    "ref_estrelas_nascimento",
    "ref_habilidades_estrela",
]

INSTANCIAS_PERSONAGEM = [
    "personagem_raca",
    "personagem_background",
    "personagem_classe",
    "personagem_astro_nascimento",
    "personagem_eventos_vida",
    "personagem_tradicoes",
]

# Quantas linhas de amostra puxar de cada catalogo
AMOSTRA_SIZE = 5

# RPCs do Modo Origem (lista de candidatas - se nao existir, ignora)
RPCS_ALVO = [
    "registrar_raca_personagem",
    "registrar_background_personagem",
    "registrar_escolha_vocacao",
    "registrar_escolha_evento",
    "definir_astro_nascimento",
    "definir_astro_nascimento_sorteado",
    "registrar_tradicao_personagem",
    "conceder_habilidades_nivel",
    "conceder_habilidades_com_recursos",
    "get_vocacoes_compativeis",
    "get_evento_vida",
    "criar_personagem_via_origem",  # provavelmente nao existe
    "registrar_marco_vida",
]

SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def validar(nome: str) -> str:
    if not SAFE_NAME.match(nome):
        raise ValueError(f"Nome inseguro: {nome!r}")
    return nome


# ====================================================================
# QUERIES
# ====================================================================

async def schema_completo(conn, tabela: str) -> dict:
    """Pega colunas + constraints + FKs de uma tabela."""
    nome_seg = validar(tabela)

    cols_sql = text("""
        SELECT
            ordinal_position,
            column_name,
            data_type,
            udt_name,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :t
        ORDER BY ordinal_position
    """)
    res = await conn.execute(cols_sql, {"t": tabela})
    colunas = []
    for row in res.fetchall():
        colunas.append({
            "posicao": row[0],
            "nome": row[1],
            "tipo": row[2],
            "tipo_postgres": row[3],
            "nullable": row[4] == "YES",
            "default": row[5],
            "max_length": row[6],
        })

    # Constraints
    cons_sql = text("""
        SELECT con.conname, con.contype, pg_get_constraintdef(con.oid) AS definicao
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
            "nome": row[0],
            "tipo": tc,
            "definicao": row[2],
        })

    # Row count
    rc = await conn.execute(text(f"SELECT count(*) FROM public.{nome_seg}"))
    row_count = rc.scalar()

    return {
        "n_cols": len(colunas),
        "row_count": row_count,
        "colunas": colunas,
        "constraints": constraints,
    }


async def amostra_dados(conn, tabela: str, n: int = AMOSTRA_SIZE) -> list:
    """Puxa N linhas de amostra (ORDER BY id LIMIT N)."""
    nome_seg = validar(tabela)
    try:
        # Tenta detectar se tem 'id'
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


async def listar_nomes_catalogo(conn, tabela: str, coluna_nome: str = "nome", limite: int = 30) -> list:
    """Lista os primeiros N nomes de um catalogo (vocabulario)."""
    nome_seg = validar(tabela)
    col_seg = validar(coluna_nome)
    try:
        # Verifica se a coluna existe
        check = await conn.execute(text(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='public' AND table_name='{nome_seg}' AND column_name='{col_seg}'
        """))
        if not check.scalar():
            return []
        sql = text(f"SELECT {col_seg} FROM public.{nome_seg} ORDER BY {col_seg} LIMIT {limite}")
        res = await conn.execute(sql)
        return [row[0] for row in res.fetchall()]
    except Exception as e:
        return [f"ERRO: {e}"]


async def codigo_funcao(conn, nome_funcao: str) -> dict:
    """Pega codigo fonte de uma RPC. Retorna dict com erro se nao existir."""
    sql = text("""
        SELECT
            pg_get_functiondef(p.oid) AS codigo,
            pg_get_function_identity_arguments(p.oid) AS parametros,
            pg_get_function_result(p.oid) AS retorno
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


async def fks_que_apontam_pra(conn, tabela: str) -> list:
    """Lista todas as FKs que apontam pra esta tabela (quem depende dela)."""
    sql = text("""
        SELECT
            cls.relname AS tabela_origem,
            att.attname AS coluna_origem,
            con.conname
        FROM pg_constraint con
        JOIN pg_class cls ON cls.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
        JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = ANY(con.conkey)
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
        {"tabela_origem": row[0], "coluna_origem": row[1], "constraint": row[2]}
        for row in res.fetchall()
    ]


# ====================================================================
# ORQUESTRADOR
# ====================================================================

async def main() -> None:
    print("=" * 60)
    print("PESQUISA 5 - Modo Origem (workflow cruzado)")
    print("=" * 60)
    print()

    resultado = {
        "extraido_em": datetime.now().isoformat(),
        "banco": "Neon Alderyn",
        "objetivo": "Mapear workflow completo de criacao de personagem via Modo Origem",
        "catalogos": {},
        "instancias_personagem": {},
        "rpcs": {},
        "fks_reversas": {},
        "vocabulario": {},
    }

    async with engine.connect() as conn:
        # 1. CATALOGOS REF_*
        print("[1/5] Catalogos ref_* (8 tabelas)...")
        for t in CATALOGOS_REF:
            print(f"      {t}...")
            resultado["catalogos"][t] = {
                "schema": await schema_completo(conn, t),
                "amostra": await amostra_dados(conn, t, AMOSTRA_SIZE),
            }
            # FKs reversas
            resultado["fks_reversas"][t] = await fks_que_apontam_pra(conn, t)
        print()

        # 2. INSTANCIAS PERSONAGEM_*
        print("[2/5] Instancias personagem_* (6 tabelas)...")
        for t in INSTANCIAS_PERSONAGEM:
            print(f"      {t}...")
            resultado["instancias_personagem"][t] = {
                "schema": await schema_completo(conn, t),
                # Sem amostra - tabelas vazias
            }
        print()

        # 3. RPCs do Modo Origem
        print(f"[3/5] RPCs ({len(RPCS_ALVO)} candidatas)...")
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

        # 4. VOCABULARIO (nomes dos catalogos)
        print("[4/5] Vocabulario dos catalogos...")
        # ref_racas, ref_backgrounds, ref_vocacoes, ref_estrelas_nascimento - todos tem coluna 'nome'
        for t in ["ref_racas", "ref_subracas", "ref_backgrounds",
                  "ref_vocacoes", "ref_caminhos", "ref_estrelas_nascimento"]:
            print(f"      {t}...")
            resultado["vocabulario"][t] = await listar_nomes_catalogo(conn, t, "nome", 50)

        # ref_eventos_vida tem provavelmente coluna 'descricao' ou 'titulo'
        print(f"      ref_eventos_vida (categorias)...")
        # Tenta pegar tipos/categorias unicas
        try:
            sql = text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema='public' AND table_name='ref_eventos_vida'
            """)
            res = await conn.execute(sql)
            cols_eventos = [r[0] for r in res.fetchall()]
            resultado["vocabulario"]["ref_eventos_vida_colunas"] = cols_eventos
        except Exception as e:
            resultado["vocabulario"]["ref_eventos_vida_colunas"] = f"ERRO: {e}"
        print()

        # 5. RPCs adicionais por busca
        print("[5/5] Buscando RPCs adicionais relacionadas a Modo Origem...")
        sql = text("""
            SELECT proname FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.prolang = (SELECT oid FROM pg_language WHERE lanname='plpgsql')
              AND (proname ILIKE '%raca%'
                OR proname ILIKE '%background%'
                OR proname ILIKE '%vocac%'
                OR proname ILIKE '%origem%'
                OR proname ILIKE '%nascimento%'
                OR proname ILIKE '%idioma%'
                OR proname ILIKE '%tradicao%'
                OR proname ILIKE '%marco_vida%'
                OR proname ILIKE '%evento_vida%')
            ORDER BY proname
        """)
        res = await conn.execute(sql)
        relacionadas = [row[0] for row in res.fetchall()]
        resultado["rpcs_relacionadas_busca"] = relacionadas
        print(f"      Encontradas por busca: {len(relacionadas)}")
        for r in relacionadas:
            marca = "ja capturada" if r in RPCS_ALVO and resultado["rpcs"].get(r, {}).get("existe") else "NOVA"
            print(f"        - {r}  [{marca}]")
        print()

    # Salva
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

    import os
    tam_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("=" * 60)
    print(f"OK Arquivo salvo: {OUTPUT_FILE}")
    print(f"   Tamanho: {tam_kb:.1f} KB")
    print(f"   Catalogos:    {len(resultado['catalogos'])}")
    print(f"   Instancias:   {len(resultado['instancias_personagem'])}")
    print(f"   RPCs encontradas: {existentes}/{len(RPCS_ALVO)}")
    print(f"   RPCs por busca:   {len(relacionadas)}")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())