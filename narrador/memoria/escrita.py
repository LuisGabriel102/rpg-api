"""
Escrita / canon do narrador — adapter ASYNC (driver SQLAlchemy/asyncpg da Oficina).
====================================================================================

Mesma lógica do `resolver_fatos_alderyn` (psycopg síncrono), portada pro
`db.get_session()` async. Comportamento idêntico:

  parse_haiku_output -> processar_fatos_haiku (resolve nomes->uuid, valida
  predicates, chama enfileirar_fatos_sessao) -> commit_canon -> gravar_recap.

O que não resolve (entidade não cadastrada/ambígua, predicate inválido) NÃO entra
no banco — vai pra `nao_resolvidos`. O mundo não cria entidade sozinho.

Reusa o vocabulário fechado e o parser do módulo puro (sem duplicar):
`resolver_fatos_alderyn.PREDICATES_VALIDOS` e `.parse_haiku_output`.
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import text

from db import get_session
from resolver_fatos_alderyn import PREDICATES_VALIDOS, parse_haiku_output  # noqa: F401

# re-exporta parse_haiku_output pra quem importar deste módulo (conveniência)
__all__ = ["parse_haiku_output", "processar_fatos_haiku", "commit_canon", "gravar_recap"]


_SQL_NOME_EXATO = text("SELECT id FROM entities WHERE lower(name) = lower(:n)")
_SQL_SLUG = text("SELECT id FROM entities WHERE slug IS NOT NULL AND lower(slug) = lower(:n)")
_SQL_ALIAS = text(
    "SELECT id FROM entities WHERE metadata ? 'aliases' AND EXISTS ("
    " SELECT 1 FROM jsonb_array_elements_text(metadata->'aliases') a"
    " WHERE lower(a) = lower(:n))"
)
_SQL_PARCIAL = text("SELECT id FROM entities WHERE name ILIKE :pat")

_SQL_ENFILEIRAR = text("SELECT enfileirar_fatos_sessao(CAST(:t AS jsonb))")
_SQL_COMMIT_CANON = text(
    "SELECT * FROM canon_validation.commit_canon(CAST(:ids AS bigint[]), :force)"
)
_SQL_GRAVAR_RECAP = text("SELECT gravar_recap_sessao(:sid, CAST(:r AS jsonb))")


async def _resolver_nome(session, nome: str) -> Optional[str]:
    """name exato -> slug -> alias -> parcial. >1 match em qualquer camada => None."""
    nome = (nome or "").strip()
    if not nome:
        return None

    rows = (await session.execute(_SQL_NOME_EXATO, {"n": nome})).all()
    if len(rows) == 1:
        return str(rows[0][0])
    if len(rows) > 1:
        return None  # ambíguo no nome — não arrisca

    rows = (await session.execute(_SQL_SLUG, {"n": nome})).all()
    if len(rows) == 1:
        return str(rows[0][0])

    rows = (await session.execute(_SQL_ALIAS, {"n": nome})).all()
    if len(rows) == 1:
        return str(rows[0][0])

    rows = (await session.execute(_SQL_PARCIAL, {"pat": f"%{nome}%"})).all()
    if len(rows) == 1:
        return str(rows[0][0])

    return None


async def processar_fatos_haiku(haiku_json: dict) -> dict:
    """
    Resolve nomes, valida predicates, monta triples e enfileira como provisional.

    Devolve {"enfileirados": {inseridos, pulados, ids_inseridos}, "nao_resolvidos": [...]}.
    """
    triples = []
    nao_resolvidos = []

    async with get_session() as session:
        for f in haiku_json.get("fatos", []):
            predicate = f.get("predicate")
            if predicate not in PREDICATES_VALIDOS:
                nao_resolvidos.append(
                    {"motivo": f"predicate fora do vocabulario: {predicate!r}", "fato": f}
                )
                continue

            subj = await _resolver_nome(session, f.get("subject", ""))
            if subj is None:
                nao_resolvidos.append({"motivo": "subject nao cadastrado/ambiguo", "fato": f})
                continue

            obj_id, obj_text = None, None
            if f.get("object_tipo") == "entidade":
                obj_id = await _resolver_nome(session, f.get("object", ""))
                if obj_id is None:
                    nao_resolvidos.append(
                        {"motivo": "object (entidade) nao cadastrado/ambiguo", "fato": f}
                    )
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
            res = await session.execute(_SQL_ENFILEIRAR, {"t": json.dumps(triples)})
            resultado = res.scalar()
            await session.commit()

    return {"enfileirados": resultado, "nao_resolvidos": nao_resolvidos}


async def commit_canon(fact_ids, force: bool = False) -> list[dict]:
    """Promove os fatos provisional (>=0.6 canonical, <0.6 pending_review; force=true força)."""
    if not fact_ids:
        return []
    ids_literal = "{" + ",".join(str(int(i)) for i in fact_ids) + "}"
    async with get_session() as session:
        res = await session.execute(_SQL_COMMIT_CANON, {"ids": ids_literal, "force": force})
        linhas = res.all()
        await session.commit()
    return [dict(r._mapping) for r in linhas]


async def gravar_recap(sessao_id: int, recap: dict) -> str:
    """Grava/atualiza o recap da sessão (UPSERT). recap precisa de resumo_curto."""
    async with get_session() as session:
        res = await session.execute(
            _SQL_GRAVAR_RECAP, {"sid": sessao_id, "r": json.dumps(recap)}
        )
        uid = res.scalar()
        await session.commit()
    return str(uid)
