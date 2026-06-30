"""
descobrir_habilidades_estrelas.py - Descoberta pra Etapa 3.

Coleta estatisticas das 1200 habilidades pra decidir estrategia de UI:
  1. Distribuicao (estrela, categoria) - confirma as barras da Etapa 2
  2. Distribuicao tem_preco por estrela
  3. Populacao dos campos opcionais (grau2, grau3, condicao, descricao_preco)
  4. Tamanho das descricoes (min, avg, max)
  5. Amostra de habilidade com evolucao populada
  6. Amostra de habilidade [TEM PRECO] de THESSAR
"""
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlmodel")

from sqlalchemy import text

from db import engine


async def main() -> None:
    print("=" * 76)
    print("  DESCOBERTA DE HABILIDADES - Etapa 3")
    print("=" * 76)

    async with engine.connect() as conn:

        # === 1. Distribuicao (estrela, categoria) ===
        print("\n[1] Distribuicao por estrela e categoria:")
        print(f"    {'estrela':14s} {'cat1':>5s} {'cat2':>5s} {'cat3':>5s} {'total':>6s}")
        sql = text("""
            SELECT e.nome, e.id,
                COUNT(*) FILTER (WHERE h.categoria = 1) AS c1,
                COUNT(*) FILTER (WHERE h.categoria = 2) AS c2,
                COUNT(*) FILTER (WHERE h.categoria = 3) AS c3,
                COUNT(*) AS total
            FROM ref_estrelas_nascimento e
            LEFT JOIN ref_habilidades_estrela h ON h.estrela_id = e.id
            GROUP BY e.id, e.nome
            ORDER BY e.id
        """)
        rows = (await conn.execute(sql)).fetchall()
        for r in rows:
            print(f"    {r[0]:14s} {r[2]:>5d} {r[3]:>5d} {r[4]:>5d} {r[5]:>6d}")

        # === 2. tem_preco por estrela ===
        print("\n[2] tem_preco=TRUE por estrela:")
        sql = text("""
            SELECT e.nome, COUNT(*) AS total_preco
            FROM ref_estrelas_nascimento e
            JOIN ref_habilidades_estrela h ON h.estrela_id = e.id
            WHERE h.tem_preco = TRUE
            GROUP BY e.id, e.nome
            ORDER BY e.id
        """)
        rows = (await conn.execute(sql)).fetchall()
        if not rows:
            print("    [zero habilidades com tem_preco=TRUE em TODAS as estrelas]")
        else:
            total_geral = 0
            for r in rows:
                print(f"    {r[0]:14s} {r[1]:>4d}")
                total_geral += r[1]
            print(f"    {'TOTAL':14s} {total_geral:>4d}")

        # === 3. Populacao dos campos opcionais ===
        print("\n[3] Populacao dos campos opcionais (de 1200 total):")
        sql = text("""
            SELECT
                COUNT(*) FILTER (WHERE evolucao_grau2_descricao IS NOT NULL) AS com_grau2,
                COUNT(*) FILTER (WHERE evolucao_grau3_descricao IS NOT NULL) AS com_grau3,
                COUNT(*) FILTER (WHERE condicao_evolucao IS NOT NULL) AS com_condicao,
                COUNT(*) FILTER (WHERE descricao_preco IS NOT NULL) AS com_desc_preco
            FROM ref_habilidades_estrela
        """)
        r = (await conn.execute(sql)).fetchone()
        print(f"    evolucao_grau2_descricao: {r[0]:>4d}")
        print(f"    evolucao_grau3_descricao: {r[1]:>4d}")
        print(f"    condicao_evolucao:        {r[2]:>4d}")
        print(f"    descricao_preco:          {r[3]:>4d}")

        # === 4. Tamanho das descricoes ===
        print("\n[4] Tamanho de descricao_completa (caracteres):")
        sql = text("""
            SELECT
                MIN(LENGTH(descricao_completa)) AS min_len,
                ROUND(AVG(LENGTH(descricao_completa)))::int AS avg_len,
                MAX(LENGTH(descricao_completa)) AS max_len,
                COUNT(*) FILTER (WHERE LENGTH(descricao_completa) > 500) AS acima_500,
                COUNT(*) FILTER (WHERE LENGTH(descricao_completa) > 1000) AS acima_1000
            FROM ref_habilidades_estrela
        """)
        r = (await conn.execute(sql)).fetchone()
        print(f"    min:            {r[0]:>5d}")
        print(f"    avg:            {r[1]:>5d}")
        print(f"    max:            {r[2]:>5d}")
        print(f"    acima de 500:   {r[3]:>5d}")
        print(f"    acima de 1000:  {r[4]:>5d}")

        # === 5. Amostra de habilidade com evolucao populada ===
        print("\n[5] Amostra: 1 habilidade com evolucao_grau2 populada:")
        sql = text("""
            SELECT h.id, e.nome AS estrela, h.numero_d100, h.nome,
                   h.categoria, h.descricao_completa,
                   h.evolucao_grau2_descricao, h.evolucao_grau3_descricao,
                   h.condicao_evolucao
            FROM ref_habilidades_estrela h
            JOIN ref_estrelas_nascimento e ON e.id = h.estrela_id
            WHERE h.evolucao_grau2_descricao IS NOT NULL
            ORDER BY h.id
            LIMIT 1
        """)
        r = (await conn.execute(sql)).fetchone()
        if r:
            print(f"    id={r[0]}  estrela={r[1]}  d100={r[2]}  cat={r[4]}")
            print(f"    nome: {r[3]}")
            print(f"    descricao:")
            print(f"      {r[5][:300]}")
            if len(r[5]) > 300:
                print(f"      [+ {len(r[5]) - 300} chars]")
            print(f"    grau2:")
            print(f"      {(r[6] or '')[:200]}")
            print(f"    grau3:")
            print(f"      {(r[7] or '')[:200]}")
            print(f"    condicao:")
            print(f"      {(r[8] or '(nula)')[:200]}")
        else:
            print("    [nenhuma]")

        # === 6. Amostra de habilidade [TEM PRECO] de THESSAR ===
        print("\n[6] Amostra: 1 habilidade [TEM PRECO] de THESSAR:")
        sql = text("""
            SELECT h.numero_d100, h.nome, h.categoria,
                   h.descricao_completa, h.descricao_preco
            FROM ref_habilidades_estrela h
            JOIN ref_estrelas_nascimento e ON e.id = h.estrela_id
            WHERE e.nome = 'THESSAR' AND h.tem_preco = TRUE
            ORDER BY h.numero_d100
            LIMIT 1
        """)
        r = (await conn.execute(sql)).fetchone()
        if r:
            print(f"    d100={r[0]}  cat={r[2]}")
            print(f"    nome: {r[1]}")
            print(f"    descricao:")
            print(f"      {r[3][:300]}")
            if len(r[3]) > 300:
                print(f"      [+ {len(r[3]) - 300} chars]")
            print(f"    descricao_preco:")
            print(f"      {r[4] or '(vazia)'}")
        else:
            print("    [nenhuma em THESSAR]")

        # === 7. Amostra: MARKA d100=1 e d100=2 (as mais cosmeticas) ===
        print("\n[7] Amostra: MARKA d100=1 e d100=2 (textura biografica):")
        sql = text("""
            SELECT h.numero_d100, h.nome, h.categoria, h.descricao_completa
            FROM ref_habilidades_estrela h
            JOIN ref_estrelas_nascimento e ON e.id = h.estrela_id
            WHERE e.nome = 'MARKA' AND h.numero_d100 IN (1, 2)
            ORDER BY h.numero_d100
        """)
        rows = (await conn.execute(sql)).fetchall()
        for r in rows:
            print(f"    d100={r[0]}  cat={r[2]}  '{r[1]}'")
            print(f"      {r[3][:200]}")

    await engine.dispose()
    print("\n" + "=" * 76)
    print("  FIM")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())