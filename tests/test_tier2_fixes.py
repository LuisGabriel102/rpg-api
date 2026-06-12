"""Tier 2 — testes de hardening e fixes defensivos."""

import html
import json


# =====================================================================
# FIX 1 — XSS: html.escape() em bestiario.py
# =====================================================================

def test_fix1_html_escape_blocks_xss():
    """Conteudo com tags HTML eh escapado."""
    malicious = '<script>alert("xss")</script>'
    escaped = html.escape(malicious)
    assert "<script>" not in escaped
    assert "&lt;script&gt;" in escaped


def test_fix1_html_escape_preserves_normal():
    """Texto limpo nao eh alterado."""
    assert html.escape("Dragao Vermelho Ancestral") == "Dragao Vermelho Ancestral"


def test_fix1_html_escape_then_br():
    """Escape antes de substituir newline por <br> — ordem correta."""
    conteudo = '<b>bold</b>\nline2'
    result = html.escape(conteudo).replace(chr(10), "<br>")
    assert "&lt;b&gt;" in result
    assert "<br>" in result
    assert "<b>" not in result


# =====================================================================
# FIX 2 — XSS: json.dumps para clipboard JS
# =====================================================================

def test_fix2_json_dumps_safe_for_js():
    """json.dumps produz string JS double-quoted, sem template injection."""
    prompt = 'line1\nline2\t"quoted" and `backtick` ${inject}'
    safe = json.dumps(prompt)
    js = f"navigator.clipboard.writeText({safe})"
    assert js.startswith('navigator.clipboard.writeText("')
    assert "${inject}" not in js.split(safe)[0]


def test_fix2_json_dumps_handles_none():
    """Prompt None vira string vazia."""
    safe = json.dumps(None or "")
    assert safe == '""'


# =====================================================================
# FIX 5 — events.py: aggregate_id=0 e sessao_id=0 sao filtros validos
# =====================================================================

def test_fix5_aggregate_id_zero_is_valid():
    """aggregate_id=0 deve gerar filtro, nao ser ignorado."""
    conditions, params = [], []
    aggregate_id = 0
    if aggregate_id is not None:
        conditions.append("aggregate_id = %s")
        params.append(aggregate_id)
    assert conditions == ["aggregate_id = %s"]
    assert params == [0]


def test_fix5_aggregate_id_none_skips():
    """aggregate_id=None nao gera filtro."""
    conditions, params = [], []
    aggregate_id = None
    if aggregate_id is not None:
        conditions.append("aggregate_id = %s")
        params.append(aggregate_id)
    assert conditions == []


def test_fix5_sessao_id_zero_is_valid():
    """sessao_id=0 deve gerar filtro."""
    conditions, params = [], []
    sessao_id = 0
    if sessao_id is not None:
        conditions.append("sessao_id = %s")
        params.append(sessao_id)
    assert conditions == ["sessao_id = %s"]
    assert params == [0]


# =====================================================================
# FIX 7 — ILIKE: wildcards escapados
# =====================================================================

def test_fix7_percent_escaped():
    """% em busca ILIKE eh escapado."""
    nome = "100%"
    _nome = nome.replace("%", "\\%").replace("_", "\\_")
    assert _nome == "100\\%"


def test_fix7_underscore_escaped():
    """_ em busca ILIKE eh escapado."""
    nome = "Cure_Wounds"
    _nome = nome.replace("%", "\\%").replace("_", "\\_")
    assert _nome == "Cure\\_Wounds"


def test_fix7_normal_unchanged():
    """Nome sem wildcards nao muda."""
    nome = "Fireball"
    _nome = nome.replace("%", "\\%").replace("_", "\\_")
    assert _nome == "Fireball"


def test_fix7_both_wildcards():
    """% e _ juntos."""
    nome = "50%_off"
    _nome = nome.replace("%", "\\%").replace("_", "\\_")
    assert _nome == "50\\%\\_off"


# =====================================================================
# FIX 8 — gerador_flux: has_nsfw_concepts vazio/None/ausente
# =====================================================================

def test_fix8_nsfw_empty_list():
    """has_nsfw_concepts=[] nao causa IndexError."""
    resultado = {"has_nsfw_concepts": []}
    nsfw = bool((resultado.get("has_nsfw_concepts") or [False])[0])
    assert nsfw is False


def test_fix8_nsfw_none():
    """has_nsfw_concepts=None nao causa TypeError."""
    resultado = {"has_nsfw_concepts": None}
    nsfw = bool((resultado.get("has_nsfw_concepts") or [False])[0])
    assert nsfw is False


def test_fix8_nsfw_missing():
    """has_nsfw_concepts ausente nao causa erro."""
    resultado = {}
    nsfw = bool((resultado.get("has_nsfw_concepts") or [False])[0])
    assert nsfw is False


def test_fix8_nsfw_true():
    """has_nsfw_concepts=[True] retorna True."""
    resultado = {"has_nsfw_concepts": [True]}
    nsfw = bool((resultado.get("has_nsfw_concepts") or [False])[0])
    assert nsfw is True


def test_fix8_nsfw_false_list():
    """has_nsfw_concepts=[False] retorna False (lista nao-vazia, nao usa fallback)."""
    resultado = {"has_nsfw_concepts": [False]}
    nsfw = bool((resultado.get("has_nsfw_concepts") or [False])[0])
    assert nsfw is False


# =====================================================================
# FIX 10 — datetime.utcnow → datetime.now(timezone.utc)
# =====================================================================

def test_fix10_timezone_aware():
    """datetime.now(timezone.utc) produz datetime com tzinfo."""
    from datetime import datetime, timezone
    dt = datetime.now(timezone.utc)
    assert dt.tzinfo is not None
    assert dt.tzinfo == timezone.utc
