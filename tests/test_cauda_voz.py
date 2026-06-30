# -*- coding: utf-8 -*-
"""
FATIA A2.1 — Cauda de voz (anti-repeticao de abertura).

GATE 1: a REDE. Com a cauda DESLIGADA (cauda_voz=False, default), a ultima mensagem
e montada EXATAMENTE como hoje — [ESTADO] -> <contexto> -> fala, sem bloco de cauda.

GATE 3: a cauda LIGADA injeta <cauda_de_voz> ENTRE <contexto> e a fala (fala continua
o ultimo item), com as N=4 aberturas limpas extraidas do historico; degrada em borda
(0 respostas -> so lembrete; 2 -> 2 aberturas); e NUNCA entra no estado.historico.

Dirige a funcao-motor DIRETO (nao via narrar), Opus mockado (MODO_MOCK + dito) e
helpers *_safe stubados. Determinismo total, zero DB/Opus.
"""
import asyncio

import jogo


def _run(coro):
    return asyncio.run(coro)


def _resp(prosa, pressao):
    return f"{prosa}\n\n<estado>\npressao_emocional: {pressao}\n</estado>"


def _patch(monkeypatch, contexto):
    """Stuba Opus(mock)+helpers. Devolve (cap, box): cap['msgs'] guarda cada msgs[-1]
    enviada; box['resp'] dita a resposta do Cronista do proximo turno."""
    cap = {"msgs": []}
    box = {"resp": ""}
    monkeypatch.setattr(jogo, "MODO_MOCK", True)

    def _cron(msgs):
        cap["msgs"].append(msgs[-1]["content"])
        return box["resp"]
    monkeypatch.setattr(jogo, "_cronista_mock", _cron)

    async def _est(sid, pressao, resultado=None):
        return "[ESTADO]"

    async def _ctx(sid, q=None):
        return contexto

    async def _grv(sid, papel, conteudo):
        return None

    monkeypatch.setattr(jogo, "_montar_estado_safe", _est)
    monkeypatch.setattr(jogo, "_carregar_contexto_safe", _ctx)
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _grv)
    return cap, box


async def _um_turno(estado, box, fala, resp, *, cauda_voz):
    box["resp"] = resp
    await jogo.executar_turno_narrado(
        estado, fala, True,
        ui=jogo._UI_TURNO_NOOP, inimigos=(), deve_abortar=lambda: False,
        cauda_voz=cauda_voz,
    )


def _seed(prosas, pressao=3):
    """Historico realista: user(cru) + assistant(prosa+<estado>) por prosa dada."""
    hist = []
    for i, p in enumerate(prosas):
        hist.append({"role": "user", "content": f"acao {i}"})
        hist.append({"role": "assistant", "content": _resp(p, pressao)})
    return hist


# ---------------------------------------------------------------------------
# GATE 1 — cauda DESLIGADA: byte-identico ao de hoje
# ---------------------------------------------------------------------------
CTX = "CTX-FIXO"
ROTEIRO = [
    ("Doran cruza o salao.", "O salao estava vazio.", 2),
    ("Ele forca a porta.", "A madeira cedeu.", 5),
    ("Desce a escada.", "Os degraus afundavam.", 6),
]
ESPERADO_OFF = [
    f"[ESTADO]\n\n<contexto>\n{CTX}\n</contexto>\n\nDoran cruza o salao.",
    f"[ESTADO]\n\n<contexto>\n{CTX}\n</contexto>\n\nEle forca a porta.",
    f"[ESTADO]\n\n<contexto>\n{CTX}\n</contexto>\n\nDesce a escada.",
]


def test_cauda_off_byte_identica(monkeypatch):
    cap, box = _patch(monkeypatch, contexto=CTX)
    estado = jogo.EstadoTurno([], 0, 1, "modelo", None)
    for fala, prosa, pressao in ROTEIRO:
        _run(_um_turno(estado, box, fala, _resp(prosa, pressao), cauda_voz=False))
    assert cap["msgs"] == ESPERADO_OFF
    for m in cap["msgs"]:
        assert "cauda_de_voz" not in m
    for msg in estado.historico:
        assert "cauda_de_voz" not in msg["content"]


# ---------------------------------------------------------------------------
# GATE 3 — cauda LIGADA
# ---------------------------------------------------------------------------
PROSAS_4 = [
    "O ferro rangeu numa nota só, longa, e tudo o mais.",
    "A nave abria-se além de uma porta velha.",
    "A voz saiu baixa e morreu perto.",
    "Da penumbra surgiu uma forma curva.",
]
ABERTURAS_4 = [
    "O ferro rangeu numa nota só, longa, e",
    "A nave abria-se além de uma porta velha.",
    "A voz saiu baixa e morreu perto.",
    "Da penumbra surgiu uma forma curva.",
]


def test_cauda_on_injeta_4_aberturas_na_posicao(monkeypatch):
    cap, box = _patch(monkeypatch, contexto=CTX)
    estado = jogo.EstadoTurno(_seed(PROSAS_4), 3, 1, "modelo", None)
    _run(_um_turno(estado, box, "Entro na sala.", _resp("A porta cedeu.", 4), cauda_voz=True))
    montada = cap["msgs"][-1]
    print("\n=== BLOCO MONTADO (cauda ON, 4 aberturas) ===\n" + montada)

    # bloco presente + 4 aberturas certas
    assert "<cauda_de_voz>" in montada and "</cauda_de_voz>" in montada
    assert "A contenção governa" in montada      # contencao relembrada (ramo com aberturas)
    for a in ABERTURAS_4:
        assert f'- "{a}"' in montada
    assert montada.count('- "') == 4
    # POSICAO: <contexto> antes da cauda, cauda antes da fala, fala por ultimo
    assert montada.index("<contexto>") < montada.index("<cauda_de_voz>")
    assert montada.index("</cauda_de_voz>") < montada.index("Entro na sala.")
    assert montada.endswith("Entro na sala.")
    # a cauda NAO entra no historico guardado
    for m in estado.historico:
        assert "cauda_de_voz" not in m["content"]


def test_cauda_on_zero_respostas_so_lembrete(monkeypatch):
    cap, box = _patch(monkeypatch, contexto="")
    estado = jogo.EstadoTurno([], 0, 1, "modelo", None)
    _run(_um_turno(estado, box, "Faco algo.", _resp("Algo aconteceu.", 1), cauda_voz=True))
    montada = cap["msgs"][-1]
    print("\n=== BLOCO MONTADO (cauda ON, 0 respostas) ===\n" + montada)
    assert "<cauda_de_voz>" in montada
    assert '- "' not in montada                 # sem lista de aberturas
    assert "Varie a entrada" in montada         # lembrete positivo presente
    assert "A contenção governa" in montada      # contencao relembrada (ramo sem aberturas)
    assert montada.endswith("Faco algo.")


def test_cauda_on_duas_respostas(monkeypatch):
    cap, box = _patch(monkeypatch, contexto=CTX)
    estado = jogo.EstadoTurno(_seed(["Primeira prosa aqui.", "Segunda prosa diferente."]),
                              2, 1, "modelo", None)
    _run(_um_turno(estado, box, "Olho em volta.", _resp("Nada se move.", 2), cauda_voz=True))
    montada = cap["msgs"][-1]
    assert montada.count('- "') == 2
    assert '- "Primeira prosa aqui."' in montada
    assert '- "Segunda prosa diferente."' in montada
    assert montada.endswith("Olho em volta.")


def test_cauda_on_teto_n4_ignora_mais_antigas(monkeypatch):
    """6 respostas no historico -> so as 4 ULTIMAS aberturas entram (N=4 teto)."""
    cap, box = _patch(monkeypatch, contexto=CTX)
    seis = [f"Prosa numero {i} de teste." for i in range(6)]
    estado = jogo.EstadoTurno(_seed(seis), 2, 1, "modelo", None)
    _run(_um_turno(estado, box, "Sigo em frente.", _resp("O chao range.", 3), cauda_voz=True))
    montada = cap["msgs"][-1]
    assert montada.count('- "') == 4
    # as 2 primeiras (0,1) ficam de fora; as 4 ultimas (2,3,4,5) entram
    assert '- "Prosa numero 0 de teste."' not in montada
    assert '- "Prosa numero 1 de teste."' not in montada
    assert '- "Prosa numero 5 de teste."' in montada
