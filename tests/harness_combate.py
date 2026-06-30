# -*- coding: utf-8 -*-
"""
FASE 2 — Harness de caracterizacao do fluxo de combate REAL (narrar + ao_rolar_dado).

Dirige os closures REAIS de jogo._pagina_jogar SEM browser, SEM Opus, SEM DB vivo.
NAO edita jogo.py — so observa.

COMO funciona (reuso do smoke, ~60%):
  - ui FALSO: captura os handlers via ui.on(...) e vira no-op no resto (grava os _js).
  - aguardar_conexao_websocket -> no-op async.
  - MODO_MOCK=True + _cronista_mock STUBADO -> o bloco <estado> do Cronista e DITADO
    por caso de teste (combate/inimigo/acao/inimigo_recuou/teste_pedido).
  - classificar_faixa -> faixa FORCADA por flag (deterministico).
  - db.get_session -> FakeSession em memoria (zero banco). Helpers top-level de DB
    (_resolver_mod_atributo, _montar_estado_safe, _carregar_contexto_safe,
    _gravar_turno_safe) viram stubs sem banco.

ACESSO AO ESTADO: os nonlocals de _pagina_jogar (inimigos, inimigo, tensao_atual,
teste_pendente, resultado_pendente, acao_atual) sao lidos pelas CELLS dos closures
(__closure__/co_freevars). Como narrar e ao_rolar_dado declaram `nonlocal`, as cells
sao COMPARTILHADAS e refletem o estado vivo apos cada turno/rolagem.
"""
import jogo
import db


def char_padrao():
    """Linha-superset do personagem (cobre toda coluna lida por qualquer SELECT)."""
    return {
        "pid": 3, "personagem_id": 3,
        "hp_atual": 80, "hp_maximo": 80,
        "vigor_atual": 18, "vigor_maximo": 18,
        "fadiga_atual": 0, "fadiga_maximo": 10,
        "mp_atual": 38, "mp_maximo": 38,
        "divida_viva": 0, "nivel": 3, "classe_primaria": "Lutador",
        "mod_forca": 1, "mod_destreza": 1, "mod_constituicao": 1,
        "mod_inteligencia": 0, "mod_sabedoria": 0, "mod_carisma": 0,
        "ferida_infeccao_pendente": "[]",
    }


class _FakeResult:
    def __init__(self, row):
        self._row = row
    def mappings(self):
        return self
    def first(self):
        return self._row
    def scalar(self):
        return None


class _FakeSession:
    """Sessao SQLAlchemy falsa em memoria. SELECT -> linha-superset do char;
    UPDATE -> espelha no char os params conhecidos (hp/vig/v/f/m/j). Nunca toca banco."""
    def __init__(self, char, log):
        self.char = char
        self.log = log
    async def __aenter__(self):
        return self
    async def __aexit__(self, *a):
        return False
    async def execute(self, sql, params=None):
        low = str(sql).lower()
        params = dict(params or {})
        self.log.append((low, params))
        if low.lstrip().startswith("select"):
            return _FakeResult(dict(self.char))
        # UPDATE: mesma semantica do banco real, em memoria
        if "hp_atual = :hp" in low and "hp" in params:
            self.char["hp_atual"] = params["hp"]
        if "vigor_atual = :vig" in low and "vig" in params:
            self.char["vigor_atual"] = params["vig"]
        if "vigor_atual = :v" in low and "v" in params:
            self.char["vigor_atual"] = params["v"]
        if "fadiga_atual = :f" in low and "f" in params:
            self.char["fadiga_atual"] = params["f"]
        if "mp_atual = :m" in low and "m" in params:
            self.char["mp_atual"] = params["m"]
        if "ferida_infeccao_pendente" in low and "j" in params:
            self.char["ferida_infeccao_pendente"] = params["j"]
        return _FakeResult(None)
    async def commit(self):
        return None


class _FakeUI:
    def __init__(self):
        self.handlers = {}
        self.js = []
    def on(self, name, fn):
        self.handlers[name] = fn
    def run_javascript(self, code, *a, **k):
        self.js.append(str(code))
        return None
    def add_head_html(self, *a, **k):
        return None
    def add_body_html(self, *a, **k):
        return None
    def html(self, *a, **k):
        return None
    def __getattr__(self, name):
        # qualquer outro ui.* vira no-op
        return lambda *a, **k: None


class Motor:
    """Fachada pra dirigir/observar o motor real."""
    def __init__(self, ui, char, db_log, forced, cronista, narrar, rolar_fn):
        self.ui = ui
        self.char = char
        self.db_log = db_log
        self._forced = forced
        self._cronista = cronista
        self._narrar = narrar
        self._rolar = rolar_fn

    # ---------- driver ----------
    async def turno(self, estado, *, fala="ajo.", prosa="A cena se move.", mostrar=True):
        """Um turno do jogador: o Cronista responde com o <estado> DITADO aqui."""
        self._cronista["resp"] = f"{prosa}\n\n<estado>\n{estado}\n</estado>"
        self.ui.js.clear()
        await self._narrar(fala, mostrar_acao=mostrar)

    async def rolar(self, faixa=None):
        """Rola o dado com a faixa FORCADA (None = dado real)."""
        self._forced["f"] = faixa
        self.ui.js.clear()
        try:
            await self._rolar(None)
        finally:
            self._forced["f"] = None

    # ---------- leitura de estado (via cells dos closures) ----------
    def _cell(self, name):
        for fn in (self._narrar, self._rolar):
            fv = fn.__code__.co_freevars
            if name in fv:
                return fn.__closure__[fv.index(name)].cell_contents
        raise KeyError(name)

    @property
    def inimigos(self):
        return self._cell("inimigos")
    @property
    def inimigo(self):
        return self._cell("inimigo")
    @property
    def tensao(self):
        return self._cell("tensao_atual")
    @property
    def teste_pendente(self):
        return self._cell("teste_pendente")
    @property
    def resultado_pendente(self):
        return self._cell("resultado_pendente")
    @property
    def acao(self):
        return self._cell("acao_atual")
    @property
    def feridas_ativas(self):
        return self._cell("feridas_ativas")
    @property
    def feridas_ja_usadas(self):
        return self._cell("feridas_ja_usadas")
    @property
    def infeccao_pendente(self):
        return self._cell("_infeccao_pendente")

    @property
    def vitais_totais(self):
        return self.char["hp_atual"] + self.char["vigor_atual"]

    def armou_dado(self):
        return any("armarDado" in c for c in self.ui.js)


async def montar_motor(monkeypatch, *, com_ficha=False, char=None):
    """Patcha o ambiente, roda _pagina_jogar e devolve o Motor com os closures reais."""
    char = char or char_padrao()
    db_log = []
    fake_ui = _FakeUI()
    forced = {"f": None}
    cronista = {"resp": "...\n\n<estado>\npressao_emocional: 0\n</estado>"}

    # --- ui / websocket ---
    monkeypatch.setattr(jogo, "ui", fake_ui)
    async def _noop_ws(*a, **k):
        return None
    monkeypatch.setattr(jogo, "aguardar_conexao_websocket", _noop_ws)

    # --- Cronista stubado (sem Opus) ---
    monkeypatch.setattr(jogo, "MODO_MOCK", True)
    monkeypatch.setattr(jogo, "_cronista_mock", lambda historico: cronista["resp"])

    # --- dado deterministico ---
    _orig_cf = jogo.classificar_faixa
    def _fake_cf(d1, d2, mod, cd):
        return forced["f"] if forced["f"] else _orig_cf(d1, d2, mod, cd)
    monkeypatch.setattr(jogo, "classificar_faixa", _fake_cf)

    # --- DB isolado ---
    monkeypatch.setattr(db, "get_session", lambda: _FakeSession(char, db_log))
    async def _stub_mod(sid, attr):
        return 1
    async def _stub_estado(sid, pressao, resultado=None):
        return "[ESTADO]"
    async def _stub_ctx(sid, q=None):
        return ""
    async def _stub_grava(sid, papel, conteudo):
        return None
    monkeypatch.setattr(jogo, "_resolver_mod_atributo", _stub_mod)
    monkeypatch.setattr(jogo, "_montar_estado_safe", _stub_estado)
    monkeypatch.setattr(jogo, "_carregar_contexto_safe", _stub_ctx)
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _stub_grava)

    # --- roda a pagina: define + registra os closures via o fake ui.on ---
    await jogo._pagina_jogar(com_ficha=com_ficha)
    ao_agir = fake_ui.handlers["jogar_action"]
    ao_rolar = fake_ui.handlers["rolar_dado"]
    fv = ao_agir.__code__.co_freevars
    narrar = ao_agir.__closure__[fv.index("narrar")].cell_contents
    return Motor(fake_ui, char, db_log, forced, cronista, narrar, ao_rolar)
