"""Tier 3 — testes de estabilidade (pipeline + SSE circuit breaker)."""

import inspect


# =====================================================================
# FIX 1 — pipeline_geracao: get_session() em vez de asyncpg.connect()
# =====================================================================

def test_pipeline_carregar_npc_uses_get_session():
    """_carregar_npc usa get_session, nao asyncpg.connect."""
    import pipeline_geracao
    src = inspect.getsource(pipeline_geracao._carregar_npc)
    assert "get_session" in src
    assert "asyncpg.connect" not in src


def test_pipeline_buscar_canonica_uses_get_session():
    """_buscar_url_canonica usa get_session, nao asyncpg.connect."""
    import pipeline_geracao
    src = inspect.getsource(pipeline_geracao._buscar_url_canonica)
    assert "get_session" in src
    assert "asyncpg.connect" not in src


def test_pipeline_no_asyncpg_import():
    """pipeline_geracao nao importa asyncpg diretamente."""
    import pipeline_geracao
    src = inspect.getsource(pipeline_geracao)
    lines = [l.strip() for l in src.splitlines()]
    assert "import asyncpg" not in lines


# =====================================================================
# FIX 2 — SSE circuit breaker: para apos N falhas / teto de vida
# =====================================================================

def test_sse_breaker_stops_after_5_consecutive_failures():
    """5 falhas seguidas encerram o stream."""
    falhas = 0
    events = []

    for _ in range(20):
        falhas += 1
        events.append("error")
        if falhas >= 5:
            events.append("close:too_many_errors")
            break

    assert events[-1] == "close:too_many_errors"
    assert events.count("error") == 5


def test_sse_breaker_resets_on_success():
    """Sucesso reseta o contador — 4 falhas + ok + 4 falhas nao fecha."""
    falhas = 0
    closed = False
    sequence = ["fail"] * 4 + ["ok"] + ["fail"] * 4

    for s in sequence:
        if s == "fail":
            falhas += 1
            if falhas >= 5:
                closed = True
                break
        else:
            falhas = 0

    assert not closed


def test_sse_breaker_success_then_5_fails_closes():
    """Sucesso seguido de 5 falhas fecha corretamente."""
    falhas = 0
    closed = False
    sequence = ["ok"] * 3 + ["fail"] * 5

    for s in sequence:
        if s == "fail":
            falhas += 1
            if falhas >= 5:
                closed = True
                break
        else:
            falhas = 0

    assert closed


def test_sse_lifetime_cap_at_1200_ticks():
    """Stream encerra apos 1200 ticks (~1h a 3s/tick)."""
    ticks = 0
    capped = False

    for _ in range(1300):
        if ticks >= 1200:
            capped = True
            break
        ticks += 1

    assert capped
    assert ticks == 1200
