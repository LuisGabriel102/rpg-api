# -*- coding: utf-8 -*-
"""
CORRUPCAO FATIA 1 — somar divida ao conjurar magia escura (caminho de ESCRITA).

A REDE (TDD vermelho->verde): hoje jogo.py NAO chama registrar_divida (divida e
read-only no jogo). Esta obra liga o motor a RPC quando o Opus emite a tag nova
"corrupcao: <peso 1-3> <sabor>" no <estado>. SITE UNICO: cobra no CAST (no parse do
<estado>, dentro do narrar/processar_combate), pros dois modos. delta = peso x 5.
O Julgamento (disparar_julgamento) NAO entra nesta fatia — fica como stub marcado.

A seco: zero Opus, FakeSession em memoria (db_log captura as chamadas), zero browser.
Reusa o harness montar_motor + _FakeSession do test_golden_magia_fora_combate.

Os testes que asseram PRESENCA de chamada (1,2,5,6,7) FALHAM contra o codigo atual
(a feature nao existe). Os que asseram AUSENCIA (3,4) sao guardas de regressao: ja
passam hoje e devem CONTINUAR passando depois (byte-neutro sem tag).
"""
import asyncio

import pytest

import jogo
import db
from harness_combate import montar_motor, char_padrao, _FakeSession, _FakeResult


def _run(coro):
    return asyncio.run(coro)


def _chamadas_divida(db_log):
    """Filtra o db_log do FakeSession para as chamadas a registrar_divida."""
    return [(sql, p) for (sql, p) in db_log if "registrar_divida" in sql]


async def _conjura(monkeypatch, estado, *, com_ficha=True):
    """Um turno: o Cronista dita o <estado> com (ou sem) a tag de corrupcao."""
    m = await montar_motor(monkeypatch, com_ficha=com_ficha, char=char_padrao())
    # higiene (igual aos goldens): silencia o _gravar_pressao best-effort.
    async def _noop_pressao(sid, valor):
        return None
    monkeypatch.setattr(jogo, "_gravar_pressao", _noop_pressao)
    await m.turno(estado)
    return m


# 1 — fora de combate: peso 2 hemomantic -> delta 10, tag hemomantic, tipo 'magia'
def test_corrupcao_fora_combate_hemomantic(monkeypatch):
    m = _run(_conjura(monkeypatch, "corrupcao: 2 hemomantic"))
    chamadas = _chamadas_divida(m.db_log)
    assert len(chamadas) == 1, f"esperava 1 registrar_divida, veio {len(chamadas)}"
    sql, p = chamadas[0]
    assert p["delta"] == 10
    assert p["tag"] == "hemomantic"
    assert "'magia'" in sql, "tipo_evento deve ser 'magia' (literal na RPC)"


# 2 — em combate: cobra no CAST (no parse), nao no roll
def test_corrupcao_em_combate_cobra_no_cast(monkeypatch):
    estado = "combate: 1\ninimigo: Goblin | comum\nvia: magico\ncorrupcao: 1 toxic"
    m = _run(_conjura(monkeypatch, estado))
    chamadas = _chamadas_divida(m.db_log)
    assert len(chamadas) == 1, f"esperava 1 registrar_divida, veio {len(chamadas)}"
    sql, p = chamadas[0]
    assert p["delta"] == 5
    assert p["tag"] == "toxic"


# 3 — sem tag -> ZERO chamadas (guarda de regressao; verde antes e depois)
def test_sem_tag_zero_fora_combate(monkeypatch):
    m = _run(_conjura(monkeypatch, "via: magico"))
    assert _chamadas_divida(m.db_log) == []


def test_sem_tag_zero_em_combate(monkeypatch):
    estado = "combate: 1\ninimigo: Goblin | comum\nvia: magico"
    m = _run(_conjura(monkeypatch, estado))
    assert _chamadas_divida(m.db_log) == []


# 4 — peso fora de faixa -> regex nao casa -> ZERO chamadas (guarda)
@pytest.mark.parametrize("estado", ["corrupcao: 4 fey", "corrupcao: 0 fey"])
def test_peso_fora_de_faixa_zero(monkeypatch, estado):
    m = _run(_conjura(monkeypatch, estado))
    assert _chamadas_divida(m.db_log) == []


# 5b — sabor com maiuscula (case-insensitive) -> tag baixada, NAO coagida para generic
def test_sabor_maiusculo_baixa_para_minuscula(monkeypatch):
    m = _run(_conjura(monkeypatch, "corrupcao: 2 Hemomantic"))
    chamadas = _chamadas_divida(m.db_log)
    assert len(chamadas) == 1
    assert chamadas[0][1]["tag"] == "hemomantic"  # nao 'generic', nao 'Hemomantic'


# 5 — sabor invalido -> UMA chamada, tag coagida para generic
def test_sabor_invalido_coage_generic(monkeypatch):
    m = _run(_conjura(monkeypatch, "corrupcao: 2 sombrio"))
    chamadas = _chamadas_divida(m.db_log)
    assert len(chamadas) == 1
    assert chamadas[0][1]["tag"] == "generic"


# 6 — mapa peso -> delta (1->5, 2->10, 3->15)
@pytest.mark.parametrize("peso,delta", [(1, 5), (2, 10), (3, 15)])
def test_peso_para_delta(monkeypatch, peso, delta):
    m = _run(_conjura(monkeypatch, f"corrupcao: {peso} fey"))
    chamadas = _chamadas_divida(m.db_log)
    assert len(chamadas) == 1
    assert chamadas[0][1]["delta"] == delta


# 7 — cap do divida_depois>=100: bifurca (Fatia 2). Sem veretheos -> Corrompido sem rosto,
#     NUNCA disparar_julgamento. (Era o teste do STUB da Fatia 1; o stub foi substituido pela
#     bifurcacao na Fatia 2 — assercao atualizada p/ a verdade nova, sem afrouxar.)
class _CapResult(_FakeResult):
    """_FakeResult cujo scalar() devolve o jsonb da RPC (simula cap atingido)."""
    def __init__(self, row, scalar_val):
        super().__init__(row)
        self._scalar_val = scalar_val
    def scalar(self):
        return self._scalar_val


class _CapSession(_FakeSession):
    """Igual ao FakeSession, mas a chamada registrar_divida devolve divida_depois=100."""
    async def execute(self, sql, params=None):
        low = str(sql).lower()
        if "registrar_divida" in low:
            self.log.append((low, dict(params or {})))
            return _CapResult(None, {"divida_depois": 100, "cap_atingido": True})
        return await super().execute(sql, params)


async def _conjura_cap(monkeypatch):
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())
    async def _noop_pressao(sid, valor):
        return None
    monkeypatch.setattr(jogo, "_gravar_pressao", _noop_pressao)
    monkeypatch.setattr(db, "get_session", lambda: _CapSession(m.char, m.db_log))
    await m.turno("corrupcao: 3 aberrant")
    return m


def test_cap_sem_veretheos_colapsa_sem_disparar_julgamento(monkeypatch, capsys):
    m = _run(_conjura_cap(monkeypatch))
    out = capsys.readouterr().out
    # registrou a divida (delta 15)
    chamadas = _chamadas_divida(m.db_log)
    assert len(chamadas) == 1 and chamadas[0][1]["delta"] == 15
    # cap detectado (divida_depois>=100) + veretheos ausente (=false) -> Corrompido sem rosto
    assert any("status_narrativo = 'colapsado'" in sql for sql, _ in m.db_log), "esperava UPDATE colapsado"
    assert "Corrompido sem rosto" in out, f"esperava log de colapso; stdout={out!r}"
    # NUNCA chama disparar_julgamento no caminho veretheos=false
    assert not any("disparar_julgamento" in sql for sql, _ in m.db_log)
