# -*- coding: utf-8 -*-
"""
FASE 2 (Degrau 2.8) — ARCO COMPLETO de combate via harness (FakeSession + MODO_MOCK).

Os 62 testes (46 puro + 16 fluxo) cobrem PECAS do motor; este arquivo cobre o ARCO:
uma briga do inicio (spawn) ao fim (desfecho + combate fechado), turno a turno.
Determinístico, isolado: zero DB real, zero Opus/Haiku, zero browser.

Mesma disciplina dos 16: o `inimigo:` so e emitido no turno do SPAWN; turnos seguintes
nao re-emitem (o bando persiste em memoria; a trava segura o combate enquanto vivo).

Cobre os 3 desfechos como arco:
  1) VENCER: dano turno a turno -> HP do inimigo zera -> sai -> combate fecha -> trava do fim.
  2) FUGA  : combate aberto por ataque -> turno seguinte foge -> escapa -> combate fecha.
             (o desfecho fuga-fecha tambem aparece, 1-turno, em test_fuga_gradiente; aqui
              o valor extra e o lead-in multi-turno + a trava pos-escape.)
  3) RECUO : UNICO inimigo recua -> sai -> combate fecha (o teste de fluxo deixa 1 vivo).
"""
import asyncio

from harness_combate import montar_motor


def _run(coro):
    asyncio.run(coro)


# ===========================================================================
# ARCO 1 — VENCER: chip turno a turno ate a morte, combate fecha, trava do fim.
# comum hp 6; dano sucesso = 4 -> dois golpes certeiros (6 -> 2 -> morto).
# ===========================================================================
def test_arco_vencer_ate_fechar(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=True)

        # turno 1: abre combate, spawna o capanga (hp do tier), arma o golpe.
        await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
        assert m.tensao is not None, "combate iniciou: tensao acende"
        assert len(m.inimigos) == 1 and m.inimigos[0]["nome"] == "capanga"
        assert m.inimigos[0]["hp"] == 6, "HP nasce do tier (comum=6)"
        assert m.inimigo is m.inimigos[0], "alvo = o unico inimigo vivo"

        # rola sucesso: 4 de dano NO ALVO certo -> hp 6 -> 2.
        await m.rolar("sucesso")
        assert len(m.inimigos) == 1, "ainda vivo apos o primeiro golpe"
        assert m.inimigos[0]["hp"] == 2, "dano caiu no alvo (6 - 4 = 2)"

        # turno 2: VESTE o resultado (nao re-arma, guard _vestindo). Sem re-emitir
        # o inimigo: a trava segura o combate (capanga vivo+ativo).
        await m.turno("acao: ataque")
        assert m.tensao is not None, "trava: combate segue com inimigo vivo"
        assert m.teste_pendente is None, "turno de vestir nao re-arma"

        # turno 3: re-arma o golpe (ja nao esta vestindo).
        await m.turno("acao: ataque")
        assert m.teste_pendente is not None, "novo golpe armado"

        # rola sucesso de novo: hp 2 - 4 -> morre (clamp 0).
        await m.rolar("sucesso")
        assert m.inimigos == [], "HP zerou: inimigo sai do bando"
        assert "caiu" in (m.resultado_pendente or ""), "tag [X caiu] emitida"

        # turno 4: sem inimigo vivo e sem combate:1 -> combate FECHA (veste o 'caiu').
        await m.turno("acao: ataque")
        assert m.tensao is None, "ultimo inimigo caiu -> combate fecha"
        assert m.inimigos == [] and m.inimigo is None

        # turno 5 — TRAVA DO FIM (lado oposto): atacar combate encerrado e inerte.
        await m.turno("acao: ataque")
        assert m.tensao is None, "combate fechado permanece fechado"
        assert m.inimigos == [] and m.teste_pendente is None
        assert not m.armou_dado(), "sem inimigo: nao arma, nao reabre"

    _run(scenario())


# ===========================================================================
# ARCO 2 — FUGA: combate aberto por ataque, turno seguinte foge e ESCAPA,
# combate fecha; depois a trava do fim segura (atacar o fim e inerte).
# (sobrepoe parcialmente test_fuga_gradiente[sucesso]; valor extra = multi-turno
#  + trava pos-escape.)
# ===========================================================================
def test_arco_fuga_escapa_e_fecha(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=True)

        # turno 1: combate aberto por um ATAQUE (estabelece a briga).
        await m.turno("combate: 1\ninimigo: bruto | bravo\nacao: ataque")
        assert m.tensao is not None, "combate iniciou"
        assert len(m.inimigos) == 1 and m.inimigos[0]["nome"] == "bruto"

        # turno 2: o jogador decide FUGIR (sem re-emitir o inimigo; tier vem da memoria).
        await m.turno("acao: fugir")
        assert m.teste_pendente is not None, "fuga arma um teste"
        assert m.teste_pendente["intencao"] == "fugir"

        # rola sucesso: escapa limpo -> bando vazio, combate fecha.
        await m.rolar("sucesso")
        assert m.inimigos == [], "escape: bando esvazia"
        assert m.tensao is None, "escape fecha o combate"

        # TRAVA DO FIM: combate encerrado pela fuga -> atacar e inerte.
        await m.turno("acao: ataque")
        assert m.tensao is None and m.inimigos == []
        assert m.teste_pendente is None and not m.armou_dado()

    _run(scenario())


# ===========================================================================
# ARCO 3 — RECUO que FECHA: o UNICO inimigo recua -> sai -> combate fecha.
# (test_recuo_remove_e_remira usa 2 inimigos e sobra 1 vivo; aqui fecha de vez.)
# ===========================================================================
def test_arco_recuo_unico_fecha(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=False)

        # turno 1: abre combate com UM inimigo.
        await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
        assert m.tensao is not None, "combate iniciou"
        assert len(m.inimigos) == 1 and m.inimigo["nome"] == "capanga"

        # turno 2: esse unico inimigo RECUA -> sai do bando, sem alvo restante.
        await m.turno("combate: 1\ninimigo_recuou: capanga\nacao: ataque")
        assert m.inimigos == [], "unico inimigo recuou: bando vazio"
        assert m.inimigo is None, "sem alvo apos o recuo do unico inimigo"

        # turno 3: sem inimigo e sem combate:1 -> combate FECHA.
        await m.turno("acao: ataque")
        assert m.tensao is None, "sem inimigo vivo -> combate fecha"
        assert m.inimigos == []

        # TRAVA DO FIM: atacar o combate encerrado NAO arma novo golpe (o gate do arme,
        # jogo.py:3354, exige inimigo vivo). teste_pendente NAO e checado aqui: o golpe
        # armado no turno 1 nunca foi rolado e so um 'rolar' o consome -> fica vivo ate la,
        # artefato ortogonal ao fechamento, nao parte dele. O fechamento e tensao+bando+alvo.
        await m.turno("acao: ataque")
        assert m.tensao is None and m.inimigos == [] and m.inimigo is None
        assert not m.armou_dado(), "sem inimigo vivo: o ataque nao arma novo dado"

    _run(scenario())
