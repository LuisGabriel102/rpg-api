# -*- coding: utf-8 -*-
"""
CORRUPCAO FATIA 2 — bifurcacao do Julgamento no cap 100 (substitui o STUB da Fatia 1).

A REDE (TDD vermelho->verde): hoje o cap 100 so loga um TODO. A Fatia 2 bifurca, SINCRONA,
no momento de bater 100 (divida_depois>=100):
  - veretheos_comprehendido = TRUE  -> chama disparar_julgamento(pid, sid); a RPC ja grava
    status_narrativo e retorna jsonb; o epilogo_narrativo vira resultado_pendente.
  - veretheos_comprehendido = FALSE -> "Corrompido sem rosto": UPDATE direto
    status_narrativo='colapsado' (valor legal do constraint); resultado_pendente recebe uma linha SECA. NUNCA
    chama disparar_julgamento (a RPC recusa veretheos=false).

CANAL reusado: resultado_pendente (cell do EstadoCombate), escrito pelo bloco de corrupcao
em processar_combate (que tem `estado`), desempacotado pelo narrar -> proximo turno. Sem
canal novo. veretheos lido SEM query extra (estende o SELECT que ja resolve o pid).

Seam: harness montar_motor + _FakeSession/db_log; _JulgSession estende o fake (molde do
_CapSession da Fatia 1) pra forcar divida_depois e devolver veretheos/epilogo conforme o caso.

Tests 1-3 asseram a bifurcacao (FALHAM contra o stub atual). Test 4 e guarda byte-neutra
(abaixo de 100 nao bifurca; ja passa).
"""
import asyncio

import jogo
import db
from harness_combate import montar_motor, char_padrao, _FakeSession, _FakeResult


def _run(coro):
    return asyncio.run(coro)


class _R(_FakeResult):
    """_FakeResult com row (mappings().first()) E/OU scalar() controlaveis."""
    def __init__(self, row=None, scalar_val=None):
        super().__init__(row)
        self._sv = scalar_val
    def scalar(self):
        return self._sv


class _JulgSession(_FakeSession):
    """FakeSession que encena o cap: resolve pid+veretheos+nome, forca divida_depois no
    retorno de registrar_divida, e devolve o jsonb de disparar_julgamento. Tudo o mais
    cai no _FakeSession base (SELECT->char, UPDATE->log)."""
    def __init__(self, char, log, *, veretheos, divida_depois=100, epilogo="O fim veste-se."):
        super().__init__(char, log)
        self._veretheos = veretheos
        self._divida_depois = divida_depois
        self._epilogo = epilogo

    async def execute(self, sql, params=None):
        low = str(sql).lower()
        params = dict(params or {})
        if low.lstrip().startswith("select") and "veretheos_comprehendido" in low:
            self.log.append((low, params))
            return _R(row={"pid": self.char["pid"], "veretheos": self._veretheos, "nome": "Kael"})
        if "registrar_divida" in low:
            self.log.append((low, params))
            return _R(scalar_val={"divida_depois": self._divida_depois, "cap_atingido": True})
        if "disparar_julgamento" in low:
            self.log.append((low, params))
            return _R(scalar_val={"epilogo_narrativo": self._epilogo,
                                  "mensagem_narrador": "msg", "tipo_julgamento": "transcendido"})
        return await super().execute(sql, params)


async def _conjura_cap(monkeypatch, *, veretheos, divida_depois=100, epilogo="O fim veste-se."):
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())
    async def _noop_pressao(sid, valor):
        return None
    monkeypatch.setattr(jogo, "_gravar_pressao", _noop_pressao)
    monkeypatch.setattr(db, "get_session",
                        lambda: _JulgSession(m.char, m.db_log, veretheos=veretheos,
                                             divida_depois=divida_depois, epilogo=epilogo))
    await m.turno("corrupcao: 3 aberrant")
    return m


def _tem(log, agulha):
    return any(agulha in sql for sql, _ in log)


# 1 — veretheos TRUE -> disparar_julgamento chamado (pid/sid); epilogo no resultado_pendente
def test_veretheos_true_dispara_julgamento(monkeypatch):
    m = _run(_conjura_cap(monkeypatch, veretheos=True, epilogo="A luz fria fecha-se sobre ele."))
    log = m.db_log
    assert _tem(log, "disparar_julgamento"), "veretheos=true deveria disparar o Julgamento"
    sql_dj, p_dj = next((sql, p) for sql, p in log if "disparar_julgamento" in sql)
    assert p_dj.get("pid") == m.char["pid"] and "sid" in p_dj
    assert m.resultado_pendente == "A luz fria fecha-se sobre ele."
    # a RPC cuida do status; o motor NAO escreve status de colapso no caminho consciente
    assert not _tem(log, "colapsado")


# 2 — veretheos FALSE -> Corrompido sem rosto: sem julgamento, UPDATE colapsado (valor legal), linha seca
def test_veretheos_false_colapso_sem_rosto(monkeypatch):
    m = _run(_conjura_cap(monkeypatch, veretheos=False))
    log = m.db_log
    assert not _tem(log, "disparar_julgamento"), "veretheos=false NUNCA chama disparar_julgamento"
    assert _tem(log, "status_narrativo = 'colapsado'"), "deveria escrever status_narrativo='colapsado'"
    rp = m.resultado_pendente
    assert rp and "sem rosto" in rp and "Kael" in rp, f"linha seca esperada, veio {rp!r}"


# 3 — dispara UMA vez (sem double)
def test_dispara_uma_vez(monkeypatch):
    m = _run(_conjura_cap(monkeypatch, veretheos=True, epilogo="x"))
    n = sum(1 for sql, _ in m.db_log if "disparar_julgamento" in sql)
    assert n == 1, f"esperava 1 disparo, veio {n}"


# 4 — abaixo de 100 -> nem julgamento nem colapso (guarda byte-neutra; ja passa)
def test_abaixo_de_100_nao_bifurca(monkeypatch):
    m = _run(_conjura_cap(monkeypatch, veretheos=True, divida_depois=50))
    assert not _tem(m.db_log, "disparar_julgamento")
    assert not _tem(m.db_log, "colapsado")
