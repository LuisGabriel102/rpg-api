# -*- coding: utf-8 -*-
"""
ADR-008 peca 3, Fatias 3b + 3c — validador de narracao + 1 retry com correcao.

3b: em combate (em_combate=True), apos a geracao a narracao passa por _validar_narracao.
Se violar, executar_turno_narrado RE-GERA uma vez injetando a correcao e usa a 2a resposta
— mesmo se ainda violar (1 retry SO, sem re-validar). Fora de combate, o validador nao roda.

3c: _validar_narracao virou ASYNC e chama o Haiku real (via asyncio.to_thread + cliente sync
lazy, espelhando narrador/memoria/fim_sessao.py). Seam haiku_fn injetavel -> o teste mocka a
chamada de rede (zero token) e exercita o PARSE real (fail-open: so os 4 nomes viram violacao).

Seam: MODO_MOCK=True + helpers *_safe stubados (sem Opus, sem DB), reusando o de
test_buffer_combate. _cronista_mock vira um _Seq SINCRONO (resposta por chamada) -> a
contagem prova quantas vezes _gerar rodou. _validar_narracao (agora async) e monkeypatchado
com um _ASeq ASYNC por caso.
"""
import asyncio

import jogo


def _run(coro):
    return asyncio.run(coro)


class _NoopUI:
    """UI de turno silenciosa (o foco e quantas geracoes, nao os pings)."""
    def arrive(self, *a, **k): pass
    def pondera(self, *a, **k): pass
    def stream_iniciar(self, *a, **k): pass
    def stream_update(self, *a, **k): pass
    def stream_finalizar(self, *a, **k): pass
    def stream_abortar(self, *a, **k): pass


class _Seq:
    """Callable SINCRONO: devolve a proxima resposta da lista (clamp na ultima) e CONTA
    chamadas. Usado pro _cronista_mock, que e chamado sincronamente dentro de _gerar."""
    def __init__(self, valores):
        self.valores = list(valores)
        self.n = 0
    def __call__(self, *a, **k):
        i = min(self.n, len(self.valores) - 1)
        self.n += 1
        return self.valores[i]


class _ASeq:
    """Callable ASYNC: igual ao _Seq, mas awaitable. Usado pro _validar_narracao (3c: async)."""
    def __init__(self, valores):
        self.valores = list(valores)
        self.n = 0
    async def __call__(self, *a, **k):
        i = min(self.n, len(self.valores) - 1)
        self.n += 1
        return self.valores[i]


PROSA1 = "Primeira narracao, a que viola e seria descartada no retry."
PROSA2 = "Segunda narracao, a corrigida que deve ser a usada."


def _resp(prosa):
    return prosa + "\n\n<estado>\npressao_emocional: 2\n</estado>"


def _patch(monkeypatch):
    monkeypatch.setattr(jogo, "MODO_MOCK", True)
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


# ---------------------------------------------------------------------------
# 3b — fluxo de retry (validador monkeypatchado, agora async)
# ---------------------------------------------------------------------------

# 1. em combate + validador viola -> _gerar roda 2x (original + retry); a 2a resposta e a usada
def test_retry_usa_segunda_resposta(monkeypatch):
    _patch(monkeypatch)
    mock = _Seq([_resp(PROSA1), _resp(PROSA2)])
    monkeypatch.setattr(jogo, "_cronista_mock", mock)
    monkeypatch.setattr(jogo, "_validar_narracao", _ASeq(["numero_cru", None]))
    res = _run(_turno(_NoopUI(), em_combate=True))
    assert mock.n == 2, "validador violou -> _gerar deve rodar 2x (original + retry)"
    assert res.prosa == PROSA2, "a 2a resposta (corrigida) deve ser a usada"
    assert res.abortado is False


# 2. em combate + validador limpo -> _gerar roda 1x (sem retry)
def test_sem_violacao_sem_retry(monkeypatch):
    _patch(monkeypatch)
    mock = _Seq([_resp(PROSA1), _resp(PROSA2)])
    monkeypatch.setattr(jogo, "_cronista_mock", mock)
    monkeypatch.setattr(jogo, "_validar_narracao", _ASeq([None]))
    res = _run(_turno(_NoopUI(), em_combate=True))
    assert mock.n == 1, "validador limpo -> _gerar roda 1x (sem retry)"
    assert res.prosa == PROSA1
    assert res.abortado is False


# 3. FORA de combate -> _validar_narracao NAO e chamado (validador nao roda fora de combate)
def test_fora_de_combate_nao_valida(monkeypatch):
    _patch(monkeypatch)
    mock = _Seq([_resp(PROSA1), _resp(PROSA2)])
    monkeypatch.setattr(jogo, "_cronista_mock", mock)
    val = _ASeq(["numero_cru"])   # violaria SE chamado
    monkeypatch.setattr(jogo, "_validar_narracao", val)
    res = _run(_turno(_NoopUI(), em_combate=False))
    assert val.n == 0, "fora de combate _validar_narracao NAO deve ser chamado"
    assert mock.n == 1, "_gerar roda 1x fora de combate"
    assert res.prosa == PROSA1
    assert res.abortado is False


# 4. retry + abort no meio da 2a geracao -> res.abortado True
def test_abort_na_segunda_geracao(monkeypatch):
    _patch(monkeypatch)
    mock = _Seq([_resp(PROSA1), _resp(PROSA2)])
    monkeypatch.setattr(jogo, "_cronista_mock", mock)
    monkeypatch.setattr(jogo, "_validar_narracao", _ASeq(["numero_cru"]))
    # mock.n vira 1 na 1a geracao (completa) e 2 na 2a (aborta no 1o chunk do loop).
    def _ab():
        return mock.n >= 2
    res = _run(_turno(_NoopUI(), em_combate=True, abortar=_ab))
    assert res.abortado is True, "abort na 2a geracao deve propagar abortado=True"
    assert mock.n == 2, "abortou ja na 2a geracao"


# 5. 1 retry SO: validador violaria sempre -> _gerar roda EXATAMENTE 2x, nunca re-valida
def test_um_retry_so_sem_revalidar(monkeypatch):
    _patch(monkeypatch)
    mock = _Seq([_resp(PROSA1), _resp(PROSA2)])
    monkeypatch.setattr(jogo, "_cronista_mock", mock)
    val = _ASeq(["numero_cru", "numero_cru", "numero_cru"])   # violaria toda vez que chamado
    monkeypatch.setattr(jogo, "_validar_narracao", val)
    res = _run(_turno(_NoopUI(), em_combate=True))
    assert mock.n == 2, "1 retry SO -> _gerar roda exatamente 2x, nunca 3+"
    assert val.n == 1, "NAO re-valida -> _validar_narracao chamado 1x so"
    assert res.prosa == PROSA2, "a 2a resposta e usada mesmo ainda violando"
    assert res.abortado is False


# ---------------------------------------------------------------------------
# 3c — PARSE real de _validar_narracao (haiku_fn mockado; caminho real exercitado)
# ---------------------------------------------------------------------------

_PROSA_ISCA = "Ele cruzou o salao em silencio.\n\n<estado>\npressao_emocional: 3\n</estado>"


# parse fail-open: so os 4 nomes exatos viram violacao; ok/lixo/vazio/case-espaco tratados certo
def test_parse_retorno_haiku(monkeypatch):
    casos = {
        "ok": None,                          # limpa
        "numero_cru": "numero_cru",          # cada violacao passa intacta
        "moldura_esprita": "moldura_esprita",
        "pessoa_tempo": "pessoa_tempo",
        "meta_vazado": "meta_vazado",
        "  NUMERO_CRU \n": "numero_cru",     # strip() + lower() normalizam
        "blá blá qualquer coisa": None,      # lixo -> fail-open (nao dispara retry)
        "": None,                            # vazio -> None
    }
    for retorno, esperado in casos.items():
        got = _run(jogo._validar_narracao(_PROSA_ISCA, haiku_fn=lambda r, _x=retorno: _x))
        assert got == esperado, f"retorno {retorno!r} deveria virar {esperado!r}, veio {got!r}"


# haiku_fn que estoura -> fail-open None (degrada sem travar o turno)
def test_parse_haiku_erro_fail_open():
    def _boom(r):
        raise RuntimeError("haiku caiu")
    got = _run(jogo._validar_narracao(_PROSA_ISCA, haiku_fn=_boom))
    assert got is None, "erro no Haiku -> None (fail-open)"


# o .md do validador carrega e e cortado em '## Entrada' (regressao: arquivo sumiu/quebrou)
def test_system_prompt_validador_carrega():
    sp = jogo._system_prompt_validador()
    assert sp.strip() != "", "system prompt do validador nao pode vir vazio"
    assert "## Entrada" not in sp, "o system prompt deve ser cortado ANTES de '## Entrada'"
    for nome in ("numero_cru", "moldura_esprita", "pessoa_tempo", "meta_vazado"):
        assert nome in sp, f"o system prompt deveria descrever a violacao {nome}"
