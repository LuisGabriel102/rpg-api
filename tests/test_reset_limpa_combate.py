# -*- coding: utf-8 -*-
"""
Prova que recomecar / selar-sessao LIMPAM o estado de combate (bando + alvo),
pra a trava de persistencia (jogo.py:3217) NAO ressuscitar a luta na cena nova.

Bug original (caca-bugs desta sessao): `inimigo`/`inimigos` faltavam na declaracao
`nonlocal` de ao_recomecar e ao_encerrar -> o assign virava variavel LOCAL e o reset
era no-op na cell do closure -> combate-fantasma persistia apos reset, e (no encerrar)
vazava o bando pra sessao nova.

Determinístico, isolado (zero DB/Opus/browser): dirige os closures REAIS de
_pagina_jogar via harness_combate, lendo o estado pelas cells dos closures.
"""
import asyncio

import jogo
from harness_combate import montar_motor


def _run(coro):
    asyncio.run(coro)


async def _entrar_em_combate(m):
    """Abre combate com um bando de 1 inimigo vivo+ativo; trava o invariante de entrada."""
    await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque")
    assert m.tensao is not None
    assert len(m.inimigos) == 1 and m.inimigos[0]["nome"] == "capanga"


def test_recomecar_limpa_o_bando_e_nao_ressuscita(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=False)
        await _entrar_em_combate(m)
        # recomecar NO MEIO da luta
        await m.ui.handlers["jogar_recomecar"]()
        # o bando e o alvo devem zerar na hora (FALHA no codigo bugado: cell intacta)
        assert m.inimigos == [], "recomecar deve esvaziar o bando"
        assert m.inimigo is None, "recomecar deve limpar o alvo"
        assert m.tensao is None, "recomecar deve zerar a Tensao"
        # turno pacifico seguinte: a trava (3217) NAO pode re-armar combate
        await m.turno("acao: ataque")
        assert m.tensao is None, "sem inimigo vivo, turno pacifico nao pode ter combate"
        assert m.inimigos == [], "o bando deve seguir vazio"
    _run(scenario())


def test_encerrar_limpa_o_bando_sem_vazar_pra_sessao_nova(monkeypatch):
    async def scenario():
        # stub do pipeline de memoria: selar devolve uma sessao nova, sem tocar banco/Haiku
        monkeypatch.setattr(jogo, "_MEMORIA_OK", True)

        async def _fake_encerrar(sessao_id, haiku_fn=None):
            return {"nova_sessao_id": 999, "fatos_enfileirados": 0, "nao_resolvidos": []}

        monkeypatch.setattr(jogo, "encerrar_sessao", _fake_encerrar)

        m = await montar_motor(monkeypatch, com_ficha=False)
        await _entrar_em_combate(m)
        # selar a sessao NO MEIO da luta
        await m.ui.handlers["jogar_encerrar"]()
        # bando/alvo/Tensao zerados -> nao vaza pra sessao nova (FALHA no codigo bugado)
        assert m.inimigos == [], "selar deve esvaziar o bando"
        assert m.inimigo is None, "selar deve limpar o alvo"
        assert m.tensao is None, "selar deve zerar a Tensao"
        # turno pacifico na sessao nova: sem combate-fantasma herdado
        await m.turno("acao: ataque")
        assert m.tensao is None and m.inimigos == [], "a sessao nova nao herda combate"
    _run(scenario())


# ===========================================================================
# LOUSA LIMPA (decisao Gabriel): recomecar/selar zeram TODAS as cells efemeras de
# combate -- feridas_ativas, feridas_ja_usadas, _infeccao_pendente. A unica cicatriz
# duravel que PERMANECE e a divida_viva (corrupcao), que nenhum desses handlers toca.
# ===========================================================================
async def _abrir_ferida_em_combate(m):
    """Combate com 1 inimigo + 1 ferida nomeada -> feridas_ativas e feridas_ja_usadas != []."""
    await m.turno("combate: 1\ninimigo: capanga | comum\nacao: ataque\nferida: corte no braço")
    assert m.tensao is not None
    assert len(m.feridas_ativas) == 1, "a ferida nomeada deveria abrir"
    assert m.feridas_ja_usadas == ["corte no braço"]


def test_recomecar_limpa_feridas_abertas(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=True)
        await _abrir_ferida_em_combate(m)
        # recomecar com a ferida AINDA aberta (meio do combate)
        await m.ui.handlers["jogar_recomecar"]()
        assert m.feridas_ativas == [], "recomecar deve zerar as feridas abertas"
        assert m.feridas_ja_usadas == [], "recomecar deve zerar os nomes ja usados"
        assert m.infeccao_pendente == [], "recomecar deve zerar a infeccao pendente"
    _run(scenario())


def test_recomecar_limpa_infeccao_pendente(monkeypatch):
    async def scenario():
        m = await montar_motor(monkeypatch, com_ficha=True)
        await _abrir_ferida_em_combate(m)
        # mata o capanga -> bando vazio, combate vai terminar
        await m.rolar("sucesso_critico")
        assert m.inimigos == []
        # turno fora de combate: a TRANSICAO converte ferida aberta -> infeccao pendente
        await m.turno("acao: ataque")
        assert len(m.infeccao_pendente) >= 1, "ferida no fim do combate vira infeccao pendente"
        assert m.feridas_ativas == []
        # recomecar deve zerar a infeccao pendente (lousa limpa) + os nomes ja usados
        await m.ui.handlers["jogar_recomecar"]()
        assert m.infeccao_pendente == [], "recomecar deve zerar a infeccao pendente"
        assert m.feridas_ja_usadas == [], "recomecar deve zerar os nomes ja usados"
    _run(scenario())


def test_encerrar_limpa_feridas_e_infeccao(monkeypatch):
    async def scenario():
        monkeypatch.setattr(jogo, "_MEMORIA_OK", True)

        async def _fake_encerrar(sessao_id, haiku_fn=None):
            return {"nova_sessao_id": 999, "fatos_enfileirados": 0, "nao_resolvidos": []}

        monkeypatch.setattr(jogo, "encerrar_sessao", _fake_encerrar)

        m = await montar_motor(monkeypatch, com_ficha=True)
        await _abrir_ferida_em_combate(m)
        # selar a sessao com a ferida aberta no meio da luta
        await m.ui.handlers["jogar_encerrar"]()
        assert m.feridas_ativas == [], "selar deve zerar as feridas abertas"
        assert m.feridas_ja_usadas == [], "selar deve zerar os nomes ja usados"
        assert m.infeccao_pendente == [], "selar deve zerar a infeccao pendente"
    _run(scenario())
