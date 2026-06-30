# -*- coding: utf-8 -*-
"""
REDE da montagem do [ESTADO] — exercita o _montar_estado_safe REAL (sem harness, sem
stub da funcao sob teste). A unica injecao e um fake de db.get_session (faking de banco,
nao stub da funcao) -> zero Neon.

Prova o que faltava cobertura: a barra pressao_emocional foi REMOVIDA da producao. Dois
ramos:
  CASO 1 (cheio): fake devolve hp/mp -> bloco traz 'vida:'/'mana:' e NUNCA pressao.
  CASO 2 (degradado): get_session falha -> except engata -> bloco minimo so com o
          cabecalho [ESTADO], sem pressao.

Padrao async: asyncio.run (como o resto da suite; sem pytest-asyncio).
"""
import asyncio

import jogo
import db


def _run(coro):
    return asyncio.run(coro)


class _FakeResult:
    def __init__(self, row):
        self._row = row
    def mappings(self):
        return self
    def first(self):
        return self._row


class _FakeSession:
    """Sessao falsa: toda query devolve a MESMA row. Suficiente pro ramo cheio (pid=None
    pula a 2a query, consultar_divida)."""
    def __init__(self, row):
        self._row = row
    async def __aenter__(self):
        return self
    async def __aexit__(self, *a):
        return False
    async def execute(self, sql, params=None):
        return _FakeResult(self._row)
    async def commit(self):
        return None


def _row_cheia():
    # TODAS as chaves que _SQL_ESTADO devolve (a funcao acessa via row["..."] direto).
    # pid=None -> pula consultar_divida; nome/local/data falsy -> suas linhas somem.
    return {
        "data": None, "pid": None, "nome": None, "classe": None, "nivel": None,
        "hp_atual": 12, "hp_maximo": 20, "status": None,
        "mp_atual": 5, "mp_maximo": 8, "local": None,
        "companheiros": None, "combate": None,
    }


async def _montar_cheio(monkeypatch):
    monkeypatch.setattr(db, "get_session", lambda: _FakeSession(_row_cheia()))
    return await jogo._montar_estado_safe(1, 0)


async def _montar_degradado(monkeypatch):
    def _sem_banco(*a, **k):
        raise RuntimeError("sem banco (teste)")
    monkeypatch.setattr(db, "get_session", _sem_banco)
    return await jogo._montar_estado_safe(1, 0)


# CASO 1 — ramo cheio: vida/mana presentes, pressao ausente (as duas grafias)
def test_estado_cheio_sem_pressao(monkeypatch):
    bloco = _run(_montar_cheio(monkeypatch))
    assert "vida:" in bloco, f"esperava 'vida:'; bloco={bloco!r}"
    assert "mana:" in bloco, f"esperava 'mana:'; bloco={bloco!r}"
    assert "pressão_emocional" not in bloco
    assert "pressao_emocional" not in bloco


# CASO 2 — ramo degradado: bloco minimo, so o cabecalho, sem pressao
def test_estado_degradado_sem_pressao(monkeypatch):
    bloco = _run(_montar_degradado(monkeypatch))
    assert bloco.strip().startswith("[ESTADO]"), f"esperava cabecalho; bloco={bloco!r}"
    assert "pressão_emocional" not in bloco
    assert "pressao_emocional" not in bloco
