# -*- coding: utf-8 -*-
"""
ADR-008 peca 3, Fatia 3a — buffer-gate em combate.

Em combate (em_combate=True), executar_turno_narrado NAO pinga incremental (ui.stream_update
nao e chamado durante o stream); a prosa final sai igual (revelada pelo caller, fora desta
funcao). Fora de combate, o streaming pinga normal. Abort no meio segue funcionando.

Seam: MODO_MOCK=True + helpers *_safe stubados (sem Opus, sem DB). UI gravadora propria
(o _UI_TURNO_NOOP descartaria os pings; aqui contamos).
"""
import asyncio

import jogo


def _run(coro):
    return asyncio.run(coro)


class _RecUI:
    """UI de turno que GRAVA os stream_update (pings incrementais) e os sinais."""
    def __init__(self):
        self.updates = []
        self.iniciou = False
        self.finalizou = False
        self.abortou = False
    def arrive(self, *a, **k): pass
    def pondera(self, *a, **k): pass
    def stream_iniciar(self, *a, **k): self.iniciou = True
    def stream_update(self, prosa, *a, **k): self.updates.append(prosa)
    def stream_finalizar(self, *a, **k): self.finalizou = True
    def stream_abortar(self, *a, **k): self.abortou = True


PROSA = "Linha de prosa longa o bastante para fatiar em varios passos de dezoito caracteres."
RESP = PROSA + "\n\n<estado>\npressao_emocional: 2\n</estado>"


def _patch(monkeypatch, resp=RESP):
    monkeypatch.setattr(jogo, "MODO_MOCK", True)
    monkeypatch.setattr(jogo, "_cronista_mock", lambda msgs: resp)
    async def _est(sid, pressao, resultado=None):
        return "[ESTADO]"
    async def _ctx(sid, q=None):
        return ""
    async def _grv(sid, papel, conteudo):
        return None
    monkeypatch.setattr(jogo, "_montar_estado_safe", _est)
    monkeypatch.setattr(jogo, "_carregar_contexto_safe", _ctx)
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _grv)


async def _turno(ui, *, em_combate, abortar=lambda: False):
    estado = jogo.EstadoTurno([], 0, 1, "modelo", None)
    return await jogo.executar_turno_narrado(
        estado, "ataco o bruto", True,
        ui=ui, inimigos=(), deve_abortar=abortar, em_combate=em_combate,
    )


# fora de combate: pinga incremental (streaming normal), prosa final correta
def test_fora_de_combate_pinga(monkeypatch):
    _patch(monkeypatch)
    ui = _RecUI()
    res = _run(_turno(ui, em_combate=False))
    assert len(ui.updates) > 0, "fora de combate deveria pingar incremental"
    assert res.prosa == PROSA
    assert res.abortado is False


# em combate: NAO pinga (buffer), mas a prosa final e identica
def test_em_combate_bufferiza(monkeypatch):
    _patch(monkeypatch)
    ui = _RecUI()
    res = _run(_turno(ui, em_combate=True))
    assert ui.updates == [], "em combate NAO deveria pingar incremental"
    assert ui.iniciou is True            # stream_iniciar segue intacto
    assert res.prosa == PROSA            # prosa final igual ao streaming
    assert res.abortado is False


# abort no meio + buffer: aborta limpo, sem ter pingado nada
def test_abort_no_meio_com_buffer(monkeypatch):
    _patch(monkeypatch)
    ui = _RecUI()
    calls = {"n": 0}
    def _ab():
        calls["n"] += 1
        return calls["n"] >= 2           # 1a checagem False, 2a True -> aborta no meio
    res = _run(_turno(ui, em_combate=True, abortar=_ab))
    assert res.abortado is True
    assert ui.abortou is True
    assert ui.updates == []
