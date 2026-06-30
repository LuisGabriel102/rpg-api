# -*- coding: utf-8 -*-
"""GUARDA DE SERVIDOR em ao_rolar_dado: so resolve com pedido pendente (teste_pendente),
e o pedido e consumido apos resolver -> fecha rolagem NAO solicitada (emit cru de
'rolar_dado') e dano REPETIVEL. A seco: harness montar_motor (FakeUI no-op + MODO_MOCK +
faixa forcada), zero Opus / browser / banco real. NUNCA toca o personagem real (id 8).
"""
import asyncio

import jogo
from harness_combate import montar_motor, char_padrao


def _run(coro):
    return asyncio.run(coro)


def _rolou(m):
    """A rolagem REAL emite window.__resolverDado(...); sem ela, nada rolou."""
    return any("__resolverDado" in c for c in m.ui.js)


async def _motor(monkeypatch):
    m = await montar_motor(monkeypatch, com_ficha=True, char=char_padrao())
    async def _noop_pressao(sid, valor):
        return None
    monkeypatch.setattr(jogo, "_gravar_pressao", _noop_pressao)
    return m


# ---------------------------------------------------------------------------
# A) emit cru SEM pedido pendente -> guarda IGNORA (nao rola, nao da dano, nao grava)
# ---------------------------------------------------------------------------
async def _cru_sem_pedido(monkeypatch):
    m = await _motor(monkeypatch)
    assert m.teste_pendente is None              # fresco: nada pendente
    vitais0 = m.vitais_totais
    n_db0 = len(m.db_log)
    await m.rolar("falha_critica")               # emit cru (a faixa forcada nem e usada)
    return m, vitais0, n_db0


def test_emit_cru_sem_pedido_e_ignorado(monkeypatch):
    m, vitais0, n_db0 = _run(_cru_sem_pedido(monkeypatch))
    assert not _rolou(m)                          # guarda barrou: nenhum __resolverDado
    assert m.vitais_totais == vitais0             # sem dano
    assert m.teste_pendente is None
    assert len(m.db_log) == n_db0                 # nenhuma escrita nova


# ---------------------------------------------------------------------------
# B) combate LEGITIMO ainda resolve (rola + da dano + consome) e NAO e repetivel
# ---------------------------------------------------------------------------
async def _legitimo_e_repeticao(monkeypatch):
    m = await _motor(monkeypatch)
    # combate abre + motor arma o golpe (arme sintetico: atacar inimigo vivo)
    await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
    s = {
        "armou": m.armou_dado(),
        "pendente_antes": m.teste_pendente is not None,
        "tensao": m.tensao is not None,
        "vitais_antes": m.vitais_totais,
    }
    await m.rolar("falha_critica")               # rolagem LEGITIMA -> dano EM VOCE
    s["rolou_legit"] = _rolou(m)
    s["vitais_pos_legit"] = m.vitais_totais
    s["pendente_pos"] = m.teste_pendente
    # NAO-REPETIVEL: 2o emit cru, sem novo pedido -> guarda barra
    await m.rolar("falha_critica")
    s["rolou_2o"] = _rolou(m)
    s["vitais_pos_2o"] = m.vitais_totais
    return s


def test_combate_legitimo_rola_da_dano_consome_e_nao_repete(monkeypatch):
    s = _run(_legitimo_e_repeticao(monkeypatch))
    # arme legitimo aconteceu
    assert s["armou"] and s["pendente_antes"] and s["tensao"]
    # rolagem legitima resolve + da dano (combate NAO regrediu)
    assert s["rolou_legit"]
    assert s["vitais_pos_legit"] < s["vitais_antes"]
    # pedido consumido
    assert s["pendente_pos"] is None
    # 2o emit cru NAO repete o dano
    assert not s["rolou_2o"]
    assert s["vitais_pos_2o"] == s["vitais_pos_legit"]
