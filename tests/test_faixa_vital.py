# -*- coding: utf-8 -*-
"""
ADR-008 — _faixa_vital: percentual -> palavra-ancora pro Cronista (vida/mana).

Testa o helper REAL (import direto). Cortes travados:
  vida: >=80 ileso | >=50 ferido | >=25 em sangue | 1..24 por um fio | ==0 caído
  mana: >=80 plena | >=50 desgastada | >=25 rarefeita | 1..24 quase seca | ==0 vazia
Bordas: 'caído'/'vazia' SO em atual==0 exato (1/100 -> por um fio, nunca caído).
Degrada (None) quando atual/maximo None ou maximo<=0.
"""
import pytest

from jogo import _faixa_vital


# ── VIDA (maximo=20, salvo onde indicado) ──────────────────────────────
@pytest.mark.parametrize("atual,maximo,esperado", [
    (20, 20, "ileso"),        # 100%
    (16, 20, "ileso"),        # 80% (borda inferior do ileso)
    (15, 20, "ferido"),       # 75%
    (10, 20, "ferido"),       # 50% (borda inferior do ferido)
    (9,  20, "em sangue"),    # 45%
    (5,  20, "em sangue"),    # 25% (borda inferior)
    (4,  20, "por um fio"),   # 20%
    (1,  20, "por um fio"),   # 5%
    (0,  20, "caído"),        # ==0 exato
    (1,  100, "por um fio"),  # BORDA: 1% NUNCA vira caído
    (0,  100, "caído"),       # ==0 exato
])
def test_faixa_vital_vida(atual, maximo, esperado):
    assert _faixa_vital(atual, maximo, recurso="vida") == esperado


# ── MANA (maximo=20) ───────────────────────────────────────────────────
@pytest.mark.parametrize("atual,maximo,esperado", [
    (20, 20, "plena"),
    (15, 20, "desgastada"),   # 75%
    (9,  20, "rarefeita"),    # 45%
    (4,  20, "quase seca"),   # 20%
    (0,  20, "vazia"),        # ==0 exato
    (1,  100, "quase seca"),  # BORDA: 1% nunca vira vazia
])
def test_faixa_vital_mana(atual, maximo, esperado):
    assert _faixa_vital(atual, maximo, recurso="mana") == esperado


# ── DEGRADACAO -> None (cai pro numero cru no [ESTADO]) ────────────────
@pytest.mark.parametrize("recurso", ["vida", "mana"])
@pytest.mark.parametrize("atual,maximo", [
    (10, None),   # maximo None
    (10, 0),      # maximo 0 (sem divisao por zero)
    (None, 20),   # atual None
])
def test_faixa_vital_degrada(recurso, atual, maximo):
    assert _faixa_vital(atual, maximo, recurso=recurso) is None
