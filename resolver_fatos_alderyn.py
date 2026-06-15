"""
Resolução de fatos do Haiku -> enfileirar_fatos_sessao  (Alderyn / Caminho B)
=============================================================================

Pega o JSON que o Haiku produz (fatos em NOMES), resolve cada nome para o UUID
da entidade, monta o array de triples no formato que enfileirar_fatos_sessao()
aceita, e separa os que não resolveram para curadoria manual.

O Haiku nunca toca UUID. Ele fala em nomes; esta camada traduz.

Driver: exemplo com psycopg (v3) síncrono. A lógica é idêntica em
asyncpg / SQLAlchemy — basta trocar as chamadas de cursor/execute.
"""

import json
from typing import Optional


# --- Vocabulário fechado (defesa: o Haiku não pode inventar predicate) ------
# Tem que bater EXATAMENTE com a lista do prompt do Haiku.
PREDICATES_VALIDOS = {
    # localização
    "reside_em", "na_regiao", "no_continente",
    # relação entre entidades
    "lealdade", "familiar", "rivalidade", "inimizade", "respeito",
    "medo", "mentoria", "divida", "neutro", "aliado_de", "pactuou_com",
    # posse
    "possui",
}


def parse_haiku_output(texto: str) -> dict:
    """
    Limpa e parseia o texto bruto do Haiku.
    Extrai do primeiro '{' ao último '}', então ignora cercas ``` e qualquer
    preâmbulo/posfácio que o modelo tenha deixado escapar.
    Levanta ValueError se não houver JSON parseável.
    """
    t = (texto or "").strip()
    i, j = t.find("{"), t.rfind("}")
    if i == -1 or j == -1 or j < i:
        raise ValueError("Haiku não devolveu um objeto JSON.")
    try:
        return json.loads(t[i:j + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"Haiku não devolveu JSON válido: {e}")


def resolver_nome(conn, nome: str) -> Optional[str]:
    """
    Resolve um nome de entidade para o UUID (str) ou None.
    Camadas, na ordem: name exato -> slug -> alias (metadata) -> parcial.
    Em qualquer camada, mais de um match => ambíguo => None (vai pra curadoria).
    """
    nome = (nome or "").strip()
    if not nome:
        return None

    with conn.cursor() as cur:
        # 1. name exato (case-insensitive)
        cur.execute("SELECT id FROM entities WHERE lower(name) = lower(%s)", (nome,))
        rows = cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])
        if len(rows) > 1:
            return None  # ambíguo no nome — não arrisca

        # 2. slug
        cur.execute(
            "SELECT id FROM entities WHERE slug IS NOT NULL AND lower(slug) = lower(%s)",
            (nome,),
        )
        rows = cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])

        # 3. alias em metadata->'aliases' (array de strings, se você usar)
        cur.execute(
            """SELECT id FROM entities
                WHERE metadata ? 'aliases'
                  AND EXISTS (
                      SELECT 1 FROM jsonb_array_elements_text(metadata->'aliases') a
                      WHERE lower(a) = lower(%s)
                  )""",
            (nome,),
        )
        rows = cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])

        # 4. parcial (só se tudo acima falhou); aceita apenas se houver 1 match
        cur.execute("SELECT id FROM entities WHERE name ILIKE %s", (f"%{nome}%",))
        rows = cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])

    return None


def processar_fatos_haiku(conn, haiku_json: dict) -> dict:
    """
    Recebe o dict do Haiku ({"fatos": [...]}), resolve nomes, valida predicates,
    monta os triples e chama enfileirar_fatos_sessao().

    Devolve:
      {
        "enfileirados":   {inseridos, pulados, ids_inseridos},  # retorno da função
        "nao_resolvidos": [ {motivo, fato}, ... ]               # pra curadoria manual
      }

    Política: o que não resolve (entidade não cadastrada, predicate inválido)
    NÃO entra no banco — vai pra 'nao_resolvidos'. O mundo não cria entidade
    sozinho.
    """
    triples = []
    nao_resolvidos = []

    for f in haiku_json.get("fatos", []):
        predicate = f.get("predicate")

        # defesa: predicate tem que estar no vocabulário fechado
        if predicate not in PREDICATES_VALIDOS:
            nao_resolvidos.append({"motivo": f"predicate fora do vocabulario: {predicate!r}", "fato": f})
            continue

        # resolve o subject
        subj = resolver_nome(conn, f.get("subject", ""))
        if subj is None:
            nao_resolvidos.append({"motivo": "subject nao cadastrado/ambiguo", "fato": f})
            continue

        # resolve o object conforme o tipo
        obj_id, obj_text = None, None
        if f.get("object_tipo") == "entidade":
            obj_id = resolver_nome(conn, f.get("object", ""))
            if obj_id is None:
                nao_resolvidos.append({"motivo": "object (entidade) nao cadastrado/ambiguo", "fato": f})
                continue
        else:
            obj_text = (f.get("object") or "").strip() or None

        triples.append({
            "subject_id": subj,
            "predicate": predicate,
            "object_id": obj_id,
            "object_text": obj_text,
            "reliability": f.get("confianca", 0.9),
            "source_in_universe": f.get("fonte"),
        })

    resultado = {"inseridos": 0, "pulados": [], "ids_inseridos": []}
    if triples:
        with conn.cursor() as cur:
            cur.execute("SELECT enfileirar_fatos_sessao(%s::jsonb)", (json.dumps(triples),))
            resultado = cur.fetchone()[0]  # jsonb -> dict (psycopg adapta)
        conn.commit()

    return {"enfileirados": resultado, "nao_resolvidos": nao_resolvidos}


# --- Exemplo de uso: fim de sessão ------------------------------------------
if __name__ == "__main__":
    # import psycopg
    # conn = psycopg.connect("postgresql://...")

    # 1. o Haiku já rodou e devolveu texto:
    texto_do_haiku = '{ "fatos": [] }'
    haiku_json = parse_haiku_output(texto_do_haiku)

    # 2. resolve nomes e enfileira como provisional
    saida = processar_fatos_haiku(conn, haiku_json)            # noqa: F821
    ids = saida["enfileirados"]["ids_inseridos"]

    # 3. promove só os fatos desta sessão (corte 0.6:
    #    reliability >= 0.6 -> canonical ; < 0.6 -> pending_review)
    if ids:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM canon_validation.commit_canon(%s::bigint[])", (ids,)
            )
            promovidos = cur.fetchall()
        conn.commit()

    # 4. saida["nao_resolvidos"] -> revisar: cadastrar a entidade nova em
    #    'entities' e, se valer, reprocessar o fato.
