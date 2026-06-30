# -*- coding: utf-8 -*-
"""
FASE 2 — Caracterizacao do FLUXO de combate REAL (narrar + ao_rolar_dado), via harness.

Caracterizacao = fotografa o comportamento ATUAL. O CODIGO vence; divergencias sao
sinalizadas, nao "corrigidas". Determinístico, isolado (zero DB/Opus/browser).

Casos: trava do fim, recuo, fuga em gradiente, arme sintetico, dano no inimigo +
morte, ordem de prioridade do arme.
"""
import asyncio
import pytest

from harness_combate import montar_motor


def _run(coro):
    asyncio.run(coro)


# ===========================================================================
# 1) TRAVA DO FIM: Cronista solta o combate com inimigo vivo+ativo -> motor MANTEM.
# ===========================================================================
def test_trava_do_fim_mantem_combate(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=False)
        # turno 1: abre combate, spawna o capanga (vivo, ativo)
        await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
        assert m.tensao is not None
        assert len(m.inimigos) == 1 and m.inimigos[0]["nome"] == "capanga"
        # turno 2: Cronista NAO emite combate:1, nao ha recuo, capanga segue vivo+ativo
        await m.turno("acao: ataque")
        assert m.tensao is not None, "trava: combate deve seguir, nao zerar"
        assert len(m.inimigos) == 1 and m.inimigos[0]["nome"].lower() == "capanga"
    _run(scenario())


# ===========================================================================
# 2) RECUO: inimigo_recuou: <nome> -> some do bando; re-mira se era o alvo.
# ===========================================================================
def test_recuo_remove_e_remira(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=False)
        await m.turno(
            "combate: 1\n"
            "inimigo: capanga da esquerda | comum\n"
            "inimigo: capanga da direita | comum\n"
            "acao: ataque"
        )
        assert len(m.inimigos) == 2
        assert m.inimigo["nome"] == "capanga da esquerda"   # alvo = primeiro
        # capanga da esquerda (o alvo atual) recua vivo
        await m.turno("combate: 1\ninimigo_recuou: capanga da esquerda\nacao: ataque")
        assert len(m.inimigos) == 1
        assert m.inimigos[0]["nome"] == "capanga da direita"
        assert m.inimigo is not None and m.inimigo["nome"] == "capanga da direita", \
            "recuo do alvo deve re-mirar no proximo vivo"
    _run(scenario())


# ===========================================================================
# 3) FUGA (gradiente): acao:fugir + faixa forcada -> sucesso/parcial escapa,
#    falha/critica fica e custa. Tier bravo (CD 13, dano x1.5).
# ===========================================================================
@pytest.mark.parametrize("faixa,escapa,custa", [
    ("sucesso_critico", True, False),
    ("sucesso", True, False),
    ("sucesso_parcial", True, True),    # escapa SANGRANDO
    ("falha", False, True),
    ("falha_critica", False, True),
])
def test_fuga_gradiente(monkeypatch, faixa, escapa, custa):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=True)
        await m.turno("combate: 1\ninimigo: bruto | bravo\nacao: fugir")
        assert m.teste_pendente is not None
        assert m.teste_pendente["intencao"] == "fugir"
        assert m.teste_pendente["atributo"] == "destreza"
        assert m.teste_pendente["cd"] == 13   # CD_TIER bravo
        total0 = m.vitais_totais
        await m.rolar(faixa)
        if escapa:
            assert m.inimigos == [] and m.tensao is None, f"{faixa}: deveria escapar"
        else:
            assert len(m.inimigos) == 1 and m.tensao is not None, f"{faixa}: deveria ficar preso"
        if custa:
            assert m.vitais_totais < total0, f"{faixa}: deveria custar vital"
        else:
            assert m.vitais_totais == total0, f"{faixa}: escape limpo, sem custo"
    _run(scenario())


# ===========================================================================
# 4) ARME SINTETICO: acao:ataque + inimigo vivo + Cronista NAO pediu teste +
#    not vestindo -> o MOTOR arma (golpe, forca, CD pelo tier).
# ===========================================================================
def test_arme_sintetico(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=False)
        await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
        assert m.armou_dado(), "deveria armar o dado sozinho"
        tp = m.teste_pendente
        assert tp is not None
        assert tp["intencao"] == "golpe"
        assert tp["atributo"] == "forca"
        assert tp["cd"] == 10   # CD_TIER comum
    _run(scenario())


def test_arme_suprimido_no_turno_que_veste(monkeypatch):
    # caracteriza o guard `not _vestindo`: o turno que VESTE a consequencia nao re-arma.
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=False)
        await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
        assert m.teste_pendente is not None
        await m.rolar("sucesso")                 # gera resultado_pendente, consome o teste
        assert m.teste_pendente is None
        # proximo turno VESTE o resultado -> nao arma de novo
        await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
        assert m.teste_pendente is None, "turno de vestir nao deve re-armar"
        assert not m.armou_dado()
    _run(scenario())


# ===========================================================================
# 5) DANO NO INIMIGO + MORTE: faixa forcada -> hp cai pela tabela; morto sai do
#    bando + tag [X caiu]. Tabela: crit 6 / sucesso 4 / parcial 2 / falha 0.
# ===========================================================================
@pytest.mark.parametrize("faixa,dmg,morre", [
    ("sucesso_critico", 6, True),    # comum hp 6 -> 0
    ("sucesso", 4, False),           # -> hp 2
    ("sucesso_parcial", 2, False),   # -> hp 4
    ("falha", 0, False),             # -> hp 6 (intacto)
])
def test_dano_no_inimigo_e_morte(monkeypatch, faixa, dmg, morre):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=True)
        await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
        assert m.inimigos[0]["hp"] == 6
        await m.rolar(faixa)
        if morre:
            assert m.inimigos == [], f"{faixa}: inimigo deveria cair"
            assert "caiu" in (m.resultado_pendente or ""), "tag [X caiu] deve ser emitida"
        else:
            assert len(m.inimigos) == 1
            assert m.inimigos[0]["hp"] == 6 - dmg
            assert "caiu" not in (m.resultado_pendente or "")
    _run(scenario())


# ===========================================================================
# 6) ORDEM DE PRIORIDADE DO ARME: fuga -> teste explicito do Cronista -> arme.
# ===========================================================================
@pytest.mark.parametrize("estado,intencao_esperada", [
    # acao:fugir + teste_pedido presente -> FUGA vence
    ("combate: 1\ninimigo: x | comum\nacao: fugir\nteste_pedido: pular o muro | destreza | cd 11", "fugir"),
    # acao:ataque + teste_pedido presente -> TESTE EXPLICITO vence
    ("combate: 1\ninimigo: x | comum\nacao: ataque\nteste_pedido: aparar | constituicao | cd 11", "aparar"),
    # acao:ataque + sem teste -> ARME SINTETICO
    ("combate: 1\ninimigo: x | comum\nacao: ataque", "golpe"),
])
def test_prioridade_do_arme(monkeypatch, estado, intencao_esperada):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=False)
        await m.turno(estado)
        assert m.teste_pendente is not None
        assert m.teste_pendente["intencao"] == intencao_esperada
    _run(scenario())
