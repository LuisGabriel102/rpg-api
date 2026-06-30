"""
fix_bugs_consolidado.py - Consolidacao dos 3 bugs reais (pesquisas P1-P7).

Bugs corrigidos:
  1. registrar_level_up:        'hp_max' (coluna inexistente) -> 'hp_maximo'
  2. evoluir_habilidade_astral: 'habilidade_categoria + 1'     -> '4 - habilidade_categoria'
  3. ref_habilidades_estrela:   popula tem_preco=TRUE p/ nomes com [TEM PRECO]

Uso:
    python fix_bugs_consolidado.py           # DRY-RUN (ROLLBACK no final)
    python fix_bugs_consolidado.py apply     # COMMIT real

Idempotente: pode ser rodado varias vezes sem efeito cumulativo.
Seguro: tudo dentro de uma transacao unica. Se der erro, rollback automatico.
"""
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


MODO = "apply" if len(sys.argv) > 1 and sys.argv[1].lower() == "apply" else "dry_run"


# ====================================================================
# FIX 1 — registrar_level_up (hp_max -> hp_maximo)
# Reproducao literal do codigo original com UMA linha alterada + 1 comentario.
# ====================================================================

FIX_1_REGISTRAR_LEVEL_UP = r"""
CREATE OR REPLACE FUNCTION public.registrar_level_up(
    p_personagem_id integer,
    p_nivel_novo integer,
    p_sessao_id integer DEFAULT NULL::integer,
    p_hp_ganho integer DEFAULT NULL::integer,
    p_mp_ganho integer DEFAULT NULL::integer,
    p_habilidade_nova text DEFAULT NULL::text,
    p_talento_id integer DEFAULT NULL::integer,
    p_melhoria_atrib jsonb DEFAULT NULL::jsonb,
    p_narrativa text DEFAULT NULL::text,
    p_data_harptos text DEFAULT NULL::text
)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $func$
DECLARE
    v_nivel_atual INTEGER;
BEGIN
    SELECT nivel INTO v_nivel_atual FROM personagens WHERE id = p_personagem_id;
    IF NOT FOUND THEN
        RETURN jsonb_build_object('sucesso', false, 'erro', 'Personagem nao encontrado');
    END IF;

    IF p_nivel_novo <= v_nivel_atual THEN
        RETURN jsonb_build_object('sucesso', false, 'erro',
            'Nivel novo (' || p_nivel_novo || ') deve ser maior que nivel atual (' || v_nivel_atual || ')');
    END IF;

    -- Registrar no log
    INSERT INTO personagem_nivel_log (
        personagem_id, sessao_id, nivel_anterior, nivel_novo,
        hp_ganho, mp_ganho, habilidade_nova, talento_ganho_id,
        melhoria_atributo, narrativa_contexto, data_harptos
    ) VALUES (
        p_personagem_id, p_sessao_id, v_nivel_atual, p_nivel_novo,
        p_hp_ganho, p_mp_ganho, p_habilidade_nova, p_talento_id,
        p_melhoria_atrib, p_narrativa, p_data_harptos
    );

    -- Atualizar nivel no personagem
    UPDATE personagens SET nivel = p_nivel_novo WHERE id = p_personagem_id;

    -- Atualizar HP max se informado
    -- FIX P7 Catedral: era 'hp_max' (coluna inexistente), agora 'hp_maximo'
    IF p_hp_ganho IS NOT NULL THEN
        UPDATE personagens SET hp_maximo = hp_maximo + p_hp_ganho WHERE id = p_personagem_id;
    END IF;

    RETURN jsonb_build_object(
        'sucesso',          true,
        'nivel_anterior',   v_nivel_atual,
        'nivel_novo',       p_nivel_novo,
        'hp_ganho',         p_hp_ganho,
        'mp_ganho',         p_mp_ganho,
        'habilidade_nova',  p_habilidade_nova,
        'mensagem',         'Nivel ' || p_nivel_novo || ' alcancado!'
            || CASE WHEN p_narrativa IS NOT NULL THEN ' — ' || p_narrativa ELSE '' END
    );
END;
$func$
"""


# ====================================================================
# FIX 2 — evoluir_habilidade_astral (categoria+1 -> 4-categoria)
# Reproducao literal + UMA linha alterada + comentario atualizado.
# ====================================================================

FIX_2_EVOLUIR_HABILIDADE_ASTRAL = r"""
CREATE OR REPLACE FUNCTION public.evoluir_habilidade_astral(
    p_personagem_id integer,
    p_sessao_id integer,
    p_contexto_marco text
)
 RETURNS json
 LANGUAGE plpgsql
AS $func$
DECLARE
    v_astro     personagem_astro_nascimento%ROWTYPE;
    v_hab       ref_habilidades_estrela%ROWTYPE;
    v_grau_novo INTEGER;
    v_desc_nova TEXT;
BEGIN
    SELECT * INTO v_astro FROM personagem_astro_nascimento WHERE personagem_id = p_personagem_id;
    IF NOT FOUND THEN
        RETURN json_build_object('erro', 'Personagem sem estrela definida.');
    END IF;

    SELECT * INTO v_hab FROM ref_habilidades_estrela WHERE id = v_astro.habilidade_id;

    -- Verificar se pode evoluir
    IF v_astro.habilidade_categoria = 3 THEN
        RETURN json_build_object('erro', 'Habilidades de 3ª categoria são estáticas — nunca evoluem.');
    END IF;

    -- FIX P7 Catedral: era 'v_astro.habilidade_categoria + 1' (logica invertida).
    -- Correto: Cat 1 -> grau max 3 (2 evolucoes); Cat 2 -> grau max 2 (1 evolucao).
    -- Isso faz as Evolucoes 2 das 12 habilidades lendarias serem alcancaveis.
    IF v_astro.grau_atual >= 4 - v_astro.habilidade_categoria THEN
        RETURN json_build_object('erro', 'Habilidade já atingiu sua evolução máxima.');
    END IF;

    -- Calcular novo grau e descrição
    v_grau_novo := v_astro.grau_atual + 1;
    v_desc_nova := CASE v_grau_novo
        WHEN 2 THEN v_hab.evolucao_grau2_descricao
        WHEN 3 THEN v_hab.evolucao_grau3_descricao
    END;

    IF v_desc_nova IS NULL THEN
        RETURN json_build_object('erro', 'Descrição de evolução não encontrada. Verifique os dados da habilidade.');
    END IF;

    -- Atualizar grau
    UPDATE personagem_astro_nascimento
    SET grau_atual = v_grau_novo
    WHERE personagem_id = p_personagem_id;

    -- Atualizar world_facts com nova forma
    UPDATE world_facts
    SET conteudo = v_desc_nova,
        titulo   = 'Estrela evoluída (Grau ' || v_grau_novo || '): ' || v_hab.nome
    WHERE personagem_id = p_personagem_id
      AND tipo = 'habilidade_astro'
      AND ativo = TRUE;

    INSERT INTO log_dados (sessao_id, personagem_id, tipo_evento, descricao, dados_json)
    VALUES (p_sessao_id, p_personagem_id, 'astro_evolucao',
        'Habilidade astral evoluída para grau ' || v_grau_novo || ': ' || v_hab.nome,
        json_build_object('grau_anterior', v_astro.grau_atual, 'grau_novo', v_grau_novo,
            'contexto_marco', p_contexto_marco));

    RETURN json_build_object(
        'sucesso',          TRUE,
        'habilidade_nome',  v_hab.nome,
        'grau_anterior',    v_astro.grau_atual,
        'grau_novo',        v_grau_novo,
        'nova_descricao',   v_desc_nova
    );
END;
$func$
"""


# ====================================================================
# FIX 3 — ref_habilidades_estrela: sincronizar tem_preco com a marcacao
# ====================================================================

FIX_3_TEM_PRECO = """
UPDATE ref_habilidades_estrela
SET tem_preco = TRUE
WHERE nome ILIKE '%[TEM PRECO]%'
  AND tem_preco = FALSE
"""


# ====================================================================
# VERIFICACOES
# ====================================================================

async def ver_estado(conn, label: str) -> None:
    print(f"\n--- {label} ---")

    # FIX 1
    sql = text("""
        SELECT pg_get_functiondef(oid) ILIKE '%hp_max = hp_max +%' AS has_bug,
               pg_get_functiondef(oid) ILIKE '%hp_maximo = hp_maximo +%' AS has_fix
        FROM pg_proc
        WHERE proname = 'registrar_level_up'
          AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname='public')
    """)
    row = (await conn.execute(sql)).fetchone()
    if row:
        bug, fix = row[0], row[1]
        if bug and not fix:
            status = "BUGADO (tem hp_max = hp_max)"
        elif fix and not bug:
            status = "FIXADO (tem hp_maximo = hp_maximo)"
        else:
            status = f"AMBIGUO (bug={bug} fix={fix})"
        print(f"  FIX 1 registrar_level_up:         {status}")
    else:
        print("  FIX 1 registrar_level_up:         FUNCAO NAO ENCONTRADA")

    # FIX 2
    sql = text("""
        SELECT pg_get_functiondef(oid) ILIKE '%habilidade_categoria + 1%' AS has_bug,
               pg_get_functiondef(oid) ILIKE '%4 - v_astro.habilidade_categoria%' AS has_fix
        FROM pg_proc
        WHERE proname = 'evoluir_habilidade_astral'
          AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname='public')
    """)
    row = (await conn.execute(sql)).fetchone()
    if row:
        bug, fix = row[0], row[1]
        if bug and not fix:
            status = "BUGADO (tem 'categoria + 1')"
        elif fix and not bug:
            status = "FIXADO (tem '4 - categoria')"
        else:
            status = f"AMBIGUO (bug={bug} fix={fix})"
        print(f"  FIX 2 evoluir_habilidade_astral:  {status}")
    else:
        print("  FIX 2 evoluir_habilidade_astral:  FUNCAO NAO ENCONTRADA")

    # FIX 3
    sql = text("""
        SELECT
            (SELECT count(*) FROM ref_habilidades_estrela WHERE nome ILIKE '%[TEM PRECO]%') AS com_marca,
            (SELECT count(*) FROM ref_habilidades_estrela WHERE tem_preco = TRUE) AS com_flag,
            (SELECT count(*) FROM ref_habilidades_estrela) AS total
    """)
    row = (await conn.execute(sql)).fetchone()
    if row:
        marca, flag, total = row[0], row[1], row[2]
        if marca == flag and marca > 0:
            status = f"SINCRONIZADO ({marca}/{total} com tem_preco=TRUE)"
        elif marca > flag:
            status = f"DESSINCRONIZADO (marca={marca} nos nomes, flag={flag}, faltam {marca-flag})"
        elif flag > marca:
            status = f"FLAG EXCEDE MARCA (flag={flag}, marca={marca}) - cuidado"
        else:
            status = f"ZERO (marca={marca}, flag={flag}) - nada a fazer"
        print(f"  FIX 3 ref_habilidades_estrela:    {status}")


async def listar_habs_afetadas(conn) -> int:
    sql = text("""
        SELECT h.id, e.nome AS estrela, h.numero_d100, h.nome
        FROM ref_habilidades_estrela h
        JOIN ref_estrelas_nascimento e ON e.id = h.estrela_id
        WHERE h.nome ILIKE '%[TEM PRECO]%'
          AND h.tem_preco = FALSE
        ORDER BY h.estrela_id, h.numero_d100
    """)
    rows = (await conn.execute(sql)).fetchall()
    if rows:
        print(f"\n  Habilidades que serao marcadas com tem_preco=TRUE ({len(rows)}):")
        for r in rows:
            print(f"    id={r[0]:4d}  [{r[1]:<8s} D100={r[2]:3d}]  {r[3]}")
    else:
        print("\n  Nenhuma habilidade com marca [TEM PRECO] precisando fix.")
    return len(rows)


# ====================================================================
# APLICACAO
# ====================================================================

async def aplicar_fixes(conn) -> None:
    print("\n[APLICANDO FIXES]")

    print("  [1/3] registrar_level_up (CREATE OR REPLACE)...")
    await conn.execute(text(FIX_1_REGISTRAR_LEVEL_UP))
    print("        OK")

    print("  [2/3] evoluir_habilidade_astral (CREATE OR REPLACE)...")
    await conn.execute(text(FIX_2_EVOLUIR_HABILIDADE_ASTRAL))
    print("        OK")

    print("  [3/3] ref_habilidades_estrela (UPDATE tem_preco)...")
    result = await conn.execute(text(FIX_3_TEM_PRECO))
    print(f"        OK ({result.rowcount} linhas atualizadas)")


# ====================================================================
# MAIN
# ====================================================================

async def main() -> None:
    print("=" * 72)
    print(f"  CONSOLIDACAO DE BUGS DA CATEDRAL — Modo: {MODO.upper()}")
    print("=" * 72)

    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            # 1. Estado antes
            await ver_estado(conn, "ESTADO ANTES")
            n_afetadas = await listar_habs_afetadas(conn)

            # 2. Aplicar
            await aplicar_fixes(conn)

            # 3. Estado depois
            await ver_estado(conn, "ESTADO DEPOIS (dentro da transacao)")

            # 4. Commit ou rollback
            print()
            if MODO == "apply":
                await trans.commit()
                print("=" * 72)
                print("  [APPLY] COMMITADO. Mudancas persistidas no Neon.")
                print("=" * 72)
            else:
                await trans.rollback()
                print("=" * 72)
                print("  [DRY-RUN] ROLLBACK. Nada foi aplicado no banco.")
                print("  Para aplicar de verdade:")
                print("    python fix_bugs_consolidado.py apply")
                print("=" * 72)
        except Exception as e:
            await trans.rollback()
            print(f"\n[ERRO] Rollback automatico por exception: {e}")
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())