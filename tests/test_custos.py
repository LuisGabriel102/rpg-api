# -*- coding: utf-8 -*-
"""
PROVA (Tarefa 8) — contador de gasto REAL da sessao.

Sem gastar credito: o usage e SINTETICO e a gravura e MOCKADA (r2/fal injetados).
Provamos:
  - custo do texto bate com a conta a mao (precos Opus 4.8: in 5 / out 25 / cw 6.25 / cr 0.50/1M).
  - cache write e cache read entram na conta.
  - LEITURA DEFENSIVA: usage None/torto -> 0.0 (nunca levanta excecao -> turno nunca quebra).
  - gravura NOVA soma 0.035 (on_custo chamado 1x); cache HIT soma 0 (on_custo NAO chamado).
  - cambio fixo R$ 5.40.
"""
import asyncio
import sys
import types

import pytest

import custos
import gravura


class _UsageObj:
    """Imita o objeto usage do Anthropic (atributos), inclusive campos ausentes."""
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


# ---------------------------------------------------------------- math do texto

def test_custo_texto_bate_com_conta_a_mao():
    # in=5000, out=800, cache_read=20000 (sintetico do enunciado)
    # = (5000*5 + 800*25 + 0*6.25 + 20000*0.5) / 1e6 = 55000/1e6 = 0.055
    u = _UsageObj(input_tokens=5000, output_tokens=800,
                  cache_creation_input_tokens=0, cache_read_input_tokens=20000)
    assert custos.custo_texto_usd(u) == pytest.approx(0.055)


def test_cache_write_entra_na_conta():
    # cw=8000 -> 8000 * 6.25 / 1e6 = 0.05
    u = _UsageObj(input_tokens=0, output_tokens=0,
                  cache_creation_input_tokens=8000, cache_read_input_tokens=0)
    assert custos.custo_texto_usd(u) == pytest.approx(0.05)


def test_custo_texto_aceita_dict_acumulado():
    # o motor pode somar o usage de varias chamadas num dict com as mesmas chaves
    d = {"input_tokens": 1000, "output_tokens": 1000,
         "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    # 1000*5 + 1000*25 = 30000 /1e6 = 0.03
    assert custos.custo_texto_usd(d) == pytest.approx(0.03)


def test_soma_de_dois_turnos():
    a = custos.custo_texto_usd(_UsageObj(input_tokens=5000, output_tokens=800,
                                         cache_read_input_tokens=20000))
    b = custos.custo_texto_usd(_UsageObj(input_tokens=1000, output_tokens=1000))
    assert (a + b) == pytest.approx(0.055 + 0.03)


# ---------------------------------------------------------------- defensivo

def test_usage_none_zero():
    assert custos.custo_texto_usd(None) == 0.0


def test_usage_vazio_zero():
    assert custos.custo_texto_usd({}) == 0.0
    assert custos.custo_texto_usd(_UsageObj()) == 0.0


def test_usage_torto_nao_levanta_e_da_zero():
    # valores nao-numericos / negativos -> ignorados, sem excecao (turno nunca quebra)
    u = _UsageObj(input_tokens="muitos", output_tokens=None,
                  cache_read_input_tokens=-5)
    assert custos.custo_texto_usd(u) == 0.0
    # objeto totalmente estranho tambem nao quebra
    assert custos.custo_texto_usd(object()) == 0.0


# ---------------------------------------------------------------- cambio

def test_cambio_fixo():
    assert custos.BRL_POR_USD == 5.40
    assert custos.usd_para_brl(0.055) == pytest.approx(0.055 * 5.40)
    assert custos.usd_para_brl("torto") == 0.0


# ---------------------------------------------------------------- gravura

def test_preco_da_gravura():
    assert custos.USD_POR_GRAVURA == 0.035


def _fake_r2(monkeypatch, *, existe):
    mod = types.ModuleType("r2_storage")

    async def gravura_existe(key):
        return existe(key)

    def url_gravura(key):
        return "https://imagens.luisgabriel.uk/" + key

    async def upload_gravura(key, file_bytes):
        return url_gravura(key)

    mod.gravura_existe = gravura_existe
    mod.url_gravura = url_gravura
    mod.upload_gravura = upload_gravura
    monkeypatch.setitem(sys.modules, "r2_storage", mod)
    return mod


def test_gravura_nova_chama_on_custo_uma_vez(monkeypatch):
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})
    _fake_r2(monkeypatch, existe=lambda key: False)   # miss -> gera

    async def fal_ok(prompt):
        return b"WEBP"

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_ok)

    chamadas = {"n": 0}
    url = asyncio.run(gravura.obter_gravura(
        "um rosto severo a luz de vela", sessao_id=7,
        on_custo=lambda: chamadas.__setitem__("n", chamadas["n"] + 1)))

    assert url is not None
    assert chamadas["n"] == 1   # gravura nova -> soma 1x (0.035 no chamador)


def test_cache_hit_nao_chama_on_custo(monkeypatch):
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})
    _fake_r2(monkeypatch, existe=lambda key: True)   # hit -> nao gera

    async def fal_proibido(prompt):
        raise AssertionError("nao devia gerar em cache hit")

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_proibido)

    chamadas = {"n": 0}
    url = asyncio.run(gravura.obter_gravura(
        "a mesma taverna ja vista", sessao_id=7,
        on_custo=lambda: chamadas.__setitem__("n", chamadas["n"] + 1)))

    assert url is not None
    assert chamadas["n"] == 0   # cache hit -> custo 0


def test_teto_nao_chama_on_custo(monkeypatch):
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})
    _fake_r2(monkeypatch, existe=lambda key: False)

    async def fal_ok(prompt):
        return b"x"

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_ok)

    sid = 5
    teto = gravura.TETO_GERACOES_POR_SESSAO
    for i in range(teto):
        asyncio.run(gravura.obter_gravura(f"cena {i}", sessao_id=sid))
    chamadas = {"n": 0}
    u = asyncio.run(gravura.obter_gravura(
        "estoura o teto", sessao_id=sid,
        on_custo=lambda: chamadas.__setitem__("n", chamadas["n"] + 1)))
    assert u is None
    assert chamadas["n"] == 0   # estourou o teto -> nao gerou -> nao somou


def test_on_custo_que_explode_nao_quebra_a_gravura(monkeypatch):
    # se o callback levantar, a imagem ainda nasce (a cena nunca quebra pela contabilidade)
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})
    _fake_r2(monkeypatch, existe=lambda key: False)

    async def fal_ok(prompt):
        return b"WEBP"

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_ok)

    def on_custo_quebrado():
        raise RuntimeError("contabilidade falhou")

    url = asyncio.run(gravura.obter_gravura(
        "um vulto no limiar", sessao_id=3, on_custo=on_custo_quebrado))
    assert url is not None   # apesar do callback explodir
