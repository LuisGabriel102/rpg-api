# -*- coding: utf-8 -*-
"""
url_imagem_oficial (modelo fase+cena, fallback a+b desenho b): testes sem banco.

Mecanica do mock: a funcao faz `from db import get_session` LAZY — instalamos
um modulo db falso em sys.modules (mesmo truque do test_gravura_cache) cuja
sessao devolve respostas roteirizadas e grava cada SQL executado.

O que se prova aqui (a ordenacao REAL do CASE e provada na auditoria viva):
  - pedido com momento vai na query dos degraus 1-3 (filtro degrau <= 3,
    desenho b) e usa a url achada;
  - query vazia -> degrau 4 = ponteiro (npcs.imagem_url);
  - fase=None e cena=None -> ponteiro DIRETO (equivalencia com url_imagem_mae,
    sem deixar o slot vazio de legado casar "exato");
  - erro no banco -> degrada (None no pior caso), NUNCA levanta — o contrato
    de gravura.py.
"""
import asyncio
import sys
import types
from contextlib import asynccontextmanager

import gravura


class _ResultadoFalso:
    def __init__(self, valor):
        self._valor = valor

    def scalar(self):
        return self._valor


class _SessaoFalsa:
    """Devolve as respostas na ordem; sem resposta na fila -> RuntimeError
    (vira o caso 'banco quebrou' do teste de degradacao)."""

    def __init__(self, respostas):
        self._fila = list(respostas)
        self.sqls = []

    async def execute(self, sql, params=None):
        self.sqls.append((str(sql), params))
        if not self._fila:
            raise RuntimeError("banco quebrou (roteiro)")
        return _ResultadoFalso(self._fila.pop(0))


def _instalar_db(monkeypatch, respostas):
    sessao = _SessaoFalsa(respostas)
    mod = types.ModuleType("db")

    @asynccontextmanager
    async def get_session():
        yield sessao

    mod.get_session = get_session
    monkeypatch.setitem(sys.modules, "db", mod)
    return sessao


def test_oficial_com_momento_usa_a_query_de_degraus(monkeypatch):
    sessao = _instalar_db(monkeypatch, ["/npc-imagem/53"])
    url = asyncio.run(gravura.url_imagem_oficial(46, "adulta", "combate"))
    assert url == "/npc-imagem/53"
    sql, params = sessao.sqls[0]
    assert "degrau <= 3" in sql          # desenho (b): oficial aleatoria NAO ganha
    assert "status = 'canonica'" in sql
    assert params == {"nid": 46, "fase": "adulta", "cena": "combate"}
    assert len(sessao.sqls) == 1         # achou no degrau 1-3: ponteiro nem e lido


def test_oficial_query_vazia_cai_no_ponteiro(monkeypatch):
    # degraus 1-3 vazios -> degrau 4 = npcs.imagem_url (via url_imagem_mae)
    sessao = _instalar_db(monkeypatch, [None, "/npc-imagem/48"])
    url = asyncio.run(gravura.url_imagem_oficial(46, "adulta", "combate"))
    assert url == "/npc-imagem/48"
    assert "FROM npcs" in sessao.sqls[1][0]


def test_oficial_sem_momento_vai_direto_no_ponteiro(monkeypatch):
    # equivalencia: (None, None) nem monta a query de degraus
    sessao = _instalar_db(monkeypatch, ["/npc-imagem/49"])
    url = asyncio.run(gravura.url_imagem_oficial(41))
    assert url == "/npc-imagem/49"
    assert len(sessao.sqls) == 1
    assert "FROM npcs" in sessao.sqls[0][0]


def test_oficial_npc_falsy_e_none(monkeypatch):
    _instalar_db(monkeypatch, [])
    assert asyncio.run(gravura.url_imagem_oficial(None, "adulta", "normal")) is None
    assert asyncio.run(gravura.url_imagem_oficial(0)) is None


def test_oficial_erro_de_banco_degrada_sem_levantar(monkeypatch):
    # fila vazia: TODA query explode (degraus E ponteiro) -> None, sem excecao
    _instalar_db(monkeypatch, [])
    url = asyncio.run(gravura.url_imagem_oficial(46, "adulta", "combate"))
    assert url is None
