# -*- coding: utf-8 -*-
"""
PROVA B (P3) — cache-first protege dinheiro + teto de seguranca.

Sem gastar credito: o R2 e o fal sao MOCKADOS (injetados). Provamos:
  - CACHE HIT -> usa a URL do R2 e NAO chama o fal (zero custo).
  - CACHE MISS -> chama o fal UMA vez, sobe no R2 sob a key estavel, devolve a URL.
  - TETO DE SEGURANCA -> apos N geracoes novas na sessao, para de gerar (None), nunca em loop.

Mecanica do mock: gravura.obter_gravura faz `from r2_storage import ...` LAZY e chama
gravura._gerar_fal_bytes. Substituimos o modulo r2_storage em sys.modules e a funcao
_gerar_fal_bytes -> nenhuma credencial, nenhuma chamada de rede.
"""
import asyncio
import sys
import types

import gravura


def _fake_r2(monkeypatch, *, existe, registrar_upload=None):
    """Instala um r2_storage falso. `existe(key)->bool` controla o cache hit/miss."""
    mod = types.ModuleType("r2_storage")

    async def gravura_existe(key):
        return existe(key)

    def url_gravura(key):
        return "https://imagens.luisgabriel.uk/" + key

    async def upload_gravura(key, file_bytes):
        if registrar_upload is not None:
            registrar_upload(key, file_bytes)
        return url_gravura(key)

    mod.gravura_existe = gravura_existe
    mod.url_gravura = url_gravura
    mod.upload_gravura = upload_gravura
    monkeypatch.setitem(sys.modules, "r2_storage", mod)
    return mod


def test_cache_hit_nao_chama_o_fal(monkeypatch):
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})
    _fake_r2(monkeypatch, existe=lambda key: True)   # ja existe -> hit

    chamou_fal = {"sim": False}

    async def fal_proibido(prompt):
        chamou_fal["sim"] = True
        raise AssertionError("fal NAO devia ser chamado em cache hit")

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_proibido)

    url = asyncio.run(gravura.obter_gravura("a taverna a luz de velas", sessao_id=42))

    assert chamou_fal["sim"] is False
    assert url == "https://imagens.luisgabriel.uk/" + gravura.chave_gravura("a taverna a luz de velas")


def test_cache_miss_gera_uma_vez_e_sobe(monkeypatch):
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})
    subiu = {}

    def registrar(key, b):
        subiu["key"] = key
        subiu["bytes"] = b

    _fake_r2(monkeypatch, existe=lambda key: False, registrar_upload=registrar)   # nao existe -> miss

    gerou = {"n": 0}

    async def fal_ok(prompt):
        gerou["n"] += 1
        assert "alderyn_grimdark" in prompt   # trigger entra no prompt
        return b"WEBPBYTES"

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_ok)

    url = asyncio.run(gravura.obter_gravura("o porto sob neblina", sessao_id=7))

    assert gerou["n"] == 1
    assert subiu["key"] == gravura.chave_gravura("o porto sob neblina")
    assert subiu["bytes"] == b"WEBPBYTES"
    assert url.endswith(gravura.chave_gravura("o porto sob neblina"))


def test_teto_de_seguranca_para_de_gerar(monkeypatch):
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})
    _fake_r2(monkeypatch, existe=lambda key: False)   # sempre miss -> forca geracao

    gerou = {"n": 0}

    async def fal_conta(prompt):
        gerou["n"] += 1
        return b"x"

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_conta)

    teto = gravura.TETO_GERACOES_POR_SESSAO
    sid = 99
    # cada descricao distinta = key distinta = uma geracao nova; ate o teto: todas geram
    for i in range(teto):
        u = asyncio.run(gravura.obter_gravura(f"cena numero {i}", sessao_id=sid))
        assert u is not None
    # a proxima estoura o teto -> None, e o fal NAO e chamado de novo
    u_extra = asyncio.run(gravura.obter_gravura("cena que estoura", sessao_id=sid))
    assert u_extra is None
    assert gerou["n"] == teto   # nunca passou do teto


def test_descricao_vazia_nao_gera(monkeypatch):
    monkeypatch.setattr(gravura, "_geracoes_por_sessao", {})

    async def fal_proibido(prompt):
        raise AssertionError("descricao vazia NAO devia gerar")

    monkeypatch.setattr(gravura, "_gerar_fal_bytes", fal_proibido)
    # nem chega a tocar o r2; mas instala um falso por seguranca
    _fake_r2(monkeypatch, existe=lambda key: False)

    assert asyncio.run(gravura.obter_gravura("   ", sessao_id=1)) is None
