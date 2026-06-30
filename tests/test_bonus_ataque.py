# -*- coding: utf-8 -*-
"""
FATIA 1 itens — bonus_ataque_equipado: soma o bonus de ataque dos itens EQUIPADOS.

Testa a funcao REAL com db.get_session fakeado (faking de banco, sem Neon, sem id 8).
A SOMA e o filtro de tipo (jsonb_typeof='number') sao DB-side -> o fake controla o
scalar() retornado; o caso 'string ignorada' e verificado de forma ESTRUTURAL (o guard
'number' esta na query), ja que jsonb nao roda no mock. Combate nao pode quebrar por item:
erro -> 0.
"""
import asyncio

import jogo
import db


def _run(coro):
    return asyncio.run(coro)


class _FakeResult:
    def __init__(self, val):
        self._val = val
    def scalar(self):
        return self._val


class _FakeSession:
    """Sessao falsa: registra o SQL e devolve um scalar() configuravel."""
    def __init__(self, val, log):
        self._val = val
        self._log = log
    async def __aenter__(self):
        return self
    async def __aexit__(self, *a):
        return False
    async def execute(self, sql, params=None):
        self._log.append(str(sql))
        return _FakeResult(self._val)
    async def commit(self):
        return None


def _patch(monkeypatch, val):
    log = []
    monkeypatch.setattr(db, "get_session", lambda: _FakeSession(val, log))
    return log


# (a) nada equipado -> SQL faz COALESCE(...,0) -> 0
def test_sem_equipado_zero(monkeypatch):
    _patch(monkeypatch, 0)
    assert _run(jogo.bonus_ataque_equipado(3)) == 0


# (b) 1 arma equipada bonus_ataque=2 -> 2
def test_uma_arma_mais_2(monkeypatch):
    _patch(monkeypatch, 2)
    assert _run(jogo.bonus_ataque_equipado(3)) == 2


# (c) 2 itens equipados (+1 e +3) -> SUM no SQL -> 4
def test_dois_itens_soma_4(monkeypatch):
    _patch(monkeypatch, 4)
    assert _run(jogo.bonus_ataque_equipado(3)) == 4


# (d) item com bonus_ataque string -> IGNORADO. Filtro e DB-side (jsonb_typeof); aqui
#     verificamos ESTRUTURALMENTE que o guard 'number' esta na query (exclui os 3 string).
def test_string_ignorada_guard_no_sql(monkeypatch):
    log = _patch(monkeypatch, 0)
    _run(jogo.bonus_ataque_equipado(3))
    assert any("jsonb_typeof" in s and "'number'" in s for s in log), \
        "a query deve filtrar bonus_ataque por tipo NUMBER (ignora os string)"


# (e) erro de query -> 0, NUNCA lanca (combate nao quebra por item)
def test_erro_query_retorna_zero(monkeypatch):
    def _boom():
        raise RuntimeError("db down (teste)")
    monkeypatch.setattr(db, "get_session", _boom)
    assert _run(jogo.bonus_ataque_equipado(3)) == 0
