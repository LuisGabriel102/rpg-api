# -*- coding: utf-8 -*-
"""
FATIA 1 itens (2o corte) — bonus_dano no dano CAUSADO ao inimigo.

Duas redes:
  A) bonus_dano_equipado: SOMA CRUA do bonus_dano dos itens equipados (db fakeado, sem Neon,
     sem id 8). Espelho de bonus_ataque_equipado; filtro de tipo e SOMA sao DB-side -> o fake
     controla o scalar(); 'string ignorada' e verificado ESTRUTURALMENTE (guard na query).
  B) _aplicar_bonus_dano: amortecimento min(3, bruto//2) + GATE (so soma se base>0). Pura.
"""
import asyncio

import jogo
import db


def _run(coro):
    return asyncio.run(coro)


# ─────────────────────────── A) bonus_dano_equipado ───────────────────────────
class _FakeResult:
    def __init__(self, val):
        self._val = val
    def scalar(self):
        return self._val


class _FakeSession:
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


def test_sem_equipado_zero(monkeypatch):
    _patch(monkeypatch, 0)
    assert _run(jogo.bonus_dano_equipado(3)) == 0


def test_um_item_mais_2(monkeypatch):
    _patch(monkeypatch, 2)
    assert _run(jogo.bonus_dano_equipado(3)) == 2


def test_dois_itens_soma_crua_4(monkeypatch):
    # +1 e +3 -> SUM no SQL -> 4 (SOMA CRUA, sem amortecer; amortizacao e do helper)
    _patch(monkeypatch, 4)
    assert _run(jogo.bonus_dano_equipado(3)) == 4


def test_string_ignorada_guard_no_sql(monkeypatch):
    log = _patch(monkeypatch, 0)
    _run(jogo.bonus_dano_equipado(3))
    assert any("jsonb_typeof" in s and "'number'" in s and "bonus_dano" in s for s in log), \
        "a query deve filtrar bonus_dano por tipo NUMBER (ignora os string)"


def test_erro_query_retorna_zero(monkeypatch):
    def _boom():
        raise RuntimeError("db down (teste)")
    monkeypatch.setattr(db, "get_session", _boom)
    assert _run(jogo.bonus_dano_equipado(3)) == 0


# ─────────────────────── B) _aplicar_bonus_dano (puro) ────────────────────────
import pytest


# amortecimento min(3, bruto//2) com base que JA fere (base=10): tabela +1->0 ... +6+->3
@pytest.mark.parametrize("bruto,efetivo", [
    (0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (10, 3),  # 10 -> teto +3
])
def test_amortecimento(bruto, efetivo):
    base = 10
    assert jogo._aplicar_bonus_dano(base, bruto) == base + efetivo


# GATE: faixa que zera (base<=0) NAO recebe bonus, qualquer bruto
@pytest.mark.parametrize("bruto", [0, 2, 6, 100])
def test_gate_faixa_zero_nao_soma(bruto):
    assert jogo._aplicar_bonus_dano(0, bruto) == 0
