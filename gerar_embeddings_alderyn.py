"""
Gera embeddings dos fatos canônicos  (Alderyn / Caminho B)
==========================================================

Pega cada fato em world_facts que tem fact_text mas ainda não tem embedding,
gera um vetor 768-dim e grava em world_facts.embedding. Isso acende a 4ª via
da busca (l_vec) na buscar_fatos_memoria — a busca semântica.

O MODELO e a normalização vivem num lugar só: narrador/memoria/embedding.py.
Este script e o fluxo de turno (query_vec) importam DO MESMO modulo — é a trava
nº 1: indexar e consultar TEM que sair do mesmo modelo/normalização, senão a
busca vetorial vira ruído sem dar erro.

Requisitos:
  pip install sentence-transformers psycopg
  export ALDERYN_DSN="postgresql://usuario:senha@host/banco"
  # rode da raiz do repo (para 'narrador' ser importável).

Idempotente: só toca fato sem embedding. Pode rodar de novo que continua de
onde parou. Na primeira execução o modelo (~1 GB) baixa do HuggingFace.
"""

import os

from narrador.memoria.embedding import MODELO, embed_lote

LOTE = 64  # fatos por rodada de encode + update


def main() -> None:
    dsn = os.environ.get("ALDERYN_DSN")
    if not dsn:
        raise SystemExit("Defina ALDERYN_DSN com a string de conexão do Postgres.")

    import psycopg

    print(f"Modelo de embedding: {MODELO}")

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fact_id, fact_text
                FROM world_facts
                WHERE fact_text IS NOT NULL AND fact_text <> '' AND embedding IS NULL
                ORDER BY fact_id
                """
            )
            linhas = cur.fetchall()

        total = len(linhas)
        print(f"Fatos sem embedding: {total}")
        if total == 0:
            print("Nada a fazer — tudo já tem embedding.")
            return

        feitos = 0
        for i in range(0, total, LOTE):
            lote = linhas[i : i + LOTE]
            ids = [r[0] for r in lote]
            textos = [r[1] for r in lote]

            vetores = embed_lote(textos)  # ja vem como strings pgvector '[...]'

            with conn.cursor() as cur:
                for fid, vec in zip(ids, vetores):
                    cur.execute(
                        "UPDATE world_facts SET embedding = %s::vector WHERE fact_id = %s",
                        (vec, fid),
                    )
            conn.commit()
            feitos += len(lote)
            print(f"  {feitos}/{total}")

        # verificação
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*) FILTER (WHERE embedding IS NULL)
                FROM world_facts
                WHERE fact_text IS NOT NULL AND fact_text <> ''
                """
            )
            restantes = cur.fetchone()[0]
        print(f"Concluído. Fatos com texto ainda sem embedding: {restantes}")


if __name__ == "__main__":
    main()
