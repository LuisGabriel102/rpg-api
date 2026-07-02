# -*- coding: utf-8 -*-
"""
Central de Admin — Aba NPCs (Onda 1): testes PUROS, sem banco/UI/R2.

Cobre os helpers testaveis de pages/admin_npcs.py:
  - _validar_upload: gate de tipo/tamanho ANTES do R2
  - _dot_status: bolinha verde (tem imagem-mae) / vermelha (sem retrato)
  - _r2_key_da_url: key R2 = ultimo segmento da URL publica

A transacao definir_como_mae NAO tem teste puro (decisao Gabriel): a seguranca
dela vem do indice unico parcial no banco + post-check em codigo + o teste vivo
com a Elara. Import do modulo nao exige credencial R2 (import lazy no handler).
"""
from pages.admin_npcs import (
    _MAX_UPLOAD_MB,
    _dot_status,
    _r2_key_da_url,
    _validar_upload,
)


# ── _validar_upload ─────────────────────────────────────────────────────────

def test_upload_jpeg_png_webp_passam():
    for ct in ("image/jpeg", "image/png", "image/webp"):
        assert _validar_upload(ct, 1024) is None


def test_upload_content_type_maiusculo_passa():
    # navegadores variam a caixa; o gate normaliza
    assert _validar_upload("IMAGE/JPEG", 1024) is None


def test_upload_tipo_errado_rejeita():
    assert _validar_upload("image/gif", 1024) is not None
    assert _validar_upload("application/pdf", 1024) is not None
    assert _validar_upload("application/octet-stream", 1024) is not None


def test_upload_sem_content_type_rejeita():
    assert _validar_upload(None, 1024) is not None
    assert _validar_upload("", 1024) is not None


def test_upload_vazio_rejeita():
    assert _validar_upload("image/png", 0) is not None


def test_upload_acima_do_teto_rejeita():
    teto = _MAX_UPLOAD_MB * 1024 * 1024
    assert _validar_upload("image/png", teto) is None          # exatamente no teto: passa
    assert _validar_upload("image/png", teto + 1) is not None  # 1 byte acima: rejeita


# ── _dot_status ─────────────────────────────────────────────────────────────

def test_dot_verde_quando_tem_mae():
    cor, rotulo = _dot_status(True)
    assert cor == "#22c55e"
    assert "imagem-mãe" in rotulo


def test_dot_vermelho_quando_sem_retrato():
    cor, rotulo = _dot_status(False)
    assert cor == "#ef4444"
    assert "sem retrato" in rotulo


# ── _r2_key_da_url ──────────────────────────────────────────────────────────

def test_r2_key_e_o_ultimo_segmento():
    assert _r2_key_da_url(
        "https://imagens.luisgabriel.uk/npc_41_2026-07-01_20-00-00-123_a1b2c3.webp"
    ) == "npc_41_2026-07-01_20-00-00-123_a1b2c3.webp"


def test_r2_key_url_vazia_nao_quebra():
    assert _r2_key_da_url("") == ""
    assert _r2_key_da_url(None) == ""
