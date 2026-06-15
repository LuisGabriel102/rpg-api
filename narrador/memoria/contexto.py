"""
Leitura de contexto do narrador — adapter ASYNC (driver SQLAlchemy/asyncpg da Oficina).
=======================================================================================

Mesma lógica do `formatar_contexto_alderyn.carregar_contexto` (psycopg síncrono),
portada pro `db.get_session()` async da Oficina. Comportamento idêntico: chama
montar_contexto_narrador no banco e devolve o markdown pronto pro prompt do Cronista.

A formatação (jsonb -> markdown) é reusada do módulo puro, sem duplicar:
`formatar_contexto_alderyn.formatar_contexto_para_prompt`.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text

from db import get_session
from formatar_contexto_alderyn import formatar_contexto_para_prompt

_SQL_CONTEXTO = text(
    "SELECT montar_contexto_narrador("
    ":sid, :qt, CAST(:qv AS vector), CAST(:fe AS uuid), :rg, :lf, :lt, :lr)"
)


async def carregar_contexto(
    sessao_id: int,
    query_text: Optional[str] = None,
    query_vec: Optional[str] = None,   # embedding da fala como '[...]' pgvector, ou None
    focus_entity: Optional[str] = None,  # uuid (str) da entidade em foco, ou None
    regiao: Optional[str] = None,
    limite_fatos: int = 8,
    limite_turnos: int = 6,
    limite_rumores: int = 5,
) -> str:
    """
    Monta o contexto dos 5 tiers e devolve o markdown. "" se não houver nada.

    query_vec: passe embed_texto(fala) (narrador.memoria.embedding) ou None enquanto
    não quiser busca vetorial — a busca cai pra full-text + trigram + entidade.
    """
    async with get_session() as session:
        result = await session.execute(
            _SQL_CONTEXTO,
            {
                "sid": sessao_id,
                "qt": query_text,
                "qv": query_vec,
                "fe": focus_entity,
                "rg": regiao,
                "lf": limite_fatos,
                "lt": limite_turnos,
                "lr": limite_rumores,
            },
        )
        ctx = result.scalar()
    if not ctx:
        return ""
    return formatar_contexto_para_prompt(ctx)
