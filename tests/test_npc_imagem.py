# -*- coding: utf-8 -*-
"""
Migracao de storage (Bloco 1): rota GET /npc-imagem/{imagem_id}.

Testes puros, sem banco:
  - _media_type: mime gravado -> usa; NULL/vazio -> image/webp
  - nivel de acesso: a UNICA mudanca de auth do bloco e "/npc-imagem/" na
    whitelist (leitura publica, mesmo nivel do dominio R2 — o <img> do jogo
    nao manda senha). Nenhuma outra rota muda de nivel.

O caminho 200-com-bytes e exercitado ao vivo so no Bloco 2/3 (hoje nenhuma
linha tem imagem_bytes; a rota nasce respondendo 404 pra tudo, por design).
"""
import auth
from server import _media_type


# ── _media_type ─────────────────────────────────────────────────────────────

def test_media_type_usa_mime_gravado():
    assert _media_type("image/png") == "image/png"
    assert _media_type("image/jpeg") == "image/jpeg"
    assert _media_type("image/webp") == "image/webp"


def test_media_type_null_ou_vazio_cai_no_webp():
    assert _media_type(None) == "image/webp"
    assert _media_type("") == "image/webp"
    assert _media_type("   ") == "image/webp"


# ── whitelist de auth ───────────────────────────────────────────────────────

def test_npc_imagem_e_leitura_publica():
    assert auth._is_public("/npc-imagem/41") is True
    assert auth._is_public("/npc-imagem/999999") is True


def test_nenhuma_outra_rota_mudou_de_nivel():
    # protegidas continuam protegidas
    assert auth._is_public("/oficina") is False
    assert auth._is_public("/oficina/admin/npcs") is False
    assert auth._is_public("/oraculo") is False
    # sem a barra final o prefixo nao casa (a rota real sempre tem /{id})
    assert auth._is_public("/npc-imagem") is False
    # publicas de antes continuam publicas
    assert auth._is_public("/health") is True
    assert auth._is_public("/api/v1/qualquer") is True
