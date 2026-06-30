# -*- coding: utf-8 -*-
"""
SESSAO DE COMBATE AO VIVO — runner hibrido (conducao-por-closure + sessao descartavel).

Cola as pecas que ja existem:
  - Conducao-por-closure (reuse de harness_combate.py): dirige os closures REAIS
    narrar + ao_rolar_dado de jogo._pagina_jogar(com_ficha=True), le o estado pelas
    cells, detecta `armarDado`, dispara ao_rolar quando o dado e armado.
  - Setup/teardown descartavel (reuse de harness_sessao_real.py): personagem+campanha+
    sessao [DESCARTAVEL], travas duras (nunca pid 2/3/8, nunca cid 1/2, exige
    "[DESCARTAVEL]" no nome), teardown no finally mesmo em falha parcial, rastro zero.

PASSO A (este arquivo, MOCK=True): prova a SECO, SEM Opus. Cronista STUBADO (roteiro
sintetico com tags de combate) + faixa FORCADA. Prova que a CAPTURA registra tudo:
jsonl rico por turno + sumario (ramos exercitados) + grade salva em disco. ZERO token.
O BANCO e real (db.get_session NAO stubado): o dano e gravado no personagem descartavel
e o teardown apaga tudo.

PASSO B (flip MOCK=False, sob ordem): troca cronista mock->Opus real e faixa forcada->
dado real. O seletor de acao, a captura e a grade sao os MESMOS — so muda quem dita o
<estado> (Opus) e a faixa (dado real). ~8-20 turnos, custo de Opus.

NAO toca jogo.py, resolver_dado, processar_combate. NAO e coletado pela suite (sem test_).
Roda sob demanda:  .venv\\Scripts\\python.exe tests\\harness_combate_vivo.py
"""
from __future__ import annotations

import asyncio
import datetime
import json
import os
import re
import sys

REPO = r"C:\Users\Luis\Downloads\nexus-monolito"
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import jogo  # noqa: E402
from db import get_session  # noqa: E402
from sqlalchemy import text  # noqa: E402

from harness_combate import _FakeUI, Motor  # noqa: E402
from harness_sessao_real import teardown, _ProxyClient  # noqa: E402

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
MOCK = True             # Passo A = True (sem Opus). Passo B (sob ordem) = False.
TETO_TURNOS = 20        # teto duro de turnos de Opus
TETO_CUSTO_USD = 6.0    # rede dura: aborta se o custo real acumulado passar disto
COMBATE_ATE_TURNO = 6   # rede: se o Cronista nao entrar em combate ate aqui -> aborta (achado).
                        # 4->6: da 2 turnos a mais de PROVOCACAO antes de desistir (a abertura e
                        # do Cronista; o harness so convida). Teto de custo/turnos intactos.
REPROVOCA_ATE_TURNO = 13  # combate fechou ANTES disto -> re-provoca um 2o encontro
MAX_REPROVOCA = 2       # quantas reaberturas no maximo
MODELO = "claude-opus-4-8"

# Cobaia ROBUSTA o suficiente p/ um arco de 20 turnos (magico+combo+cura e sobreviver).
COBAIA_HP = 100         # hp_atual = hp_maximo
COBAIA_VIGOR = 24       # vigor_atual = vigor_maximo
COBAIA_MP = 60          # mp_atual = mp_maximo
COBAIA_FADIGA_MAX = 10

# precos REAIS Opus 4.8 (US$/Mtok, confirmados pela fatura Anthropic) — SO p/ estimar custo.
# Antigos (15/75/1.5/18.75) inflavam o custo reportado ~2,5x. cache_write = 5m TTL.
RATE = {"input": 5.0, "output": 25.0, "cache_read": 0.5, "cache_write": 6.25}

_RE_DADO = re.compile(
    r'__resolverDado\((\d+),(\d+),(-?\d+),(\d+),"([^"]+)","([^"]+)"\)')


# ===========================================================================
# SETUP descartavel (cobaia robusta)
# ===========================================================================
async def setup_combate(ts: str) -> dict:
    marker = f"COMBATEVIVO-{ts}"
    async with get_session() as s:
        cid = (await s.execute(text(
            "INSERT INTO campanhas (nome, status, data_atual_narrativa) "
            "VALUES (:n, 'ativa', :d) RETURNING id"
        ), {"n": f"[DESCARTAVEL] CombateVivo {marker}", "d": "Noite de Vesperas"})).scalar()
        pid = (await s.execute(text(
            "INSERT INTO personagens (campanha_id, nome, classe_primaria, nivel, "
            "hp_atual, hp_maximo, vigor_atual, vigor_maximo, "
            "fadiga_atual, fadiga_maximo, ferida_infeccao_pendente, status_narrativo, "
            "mod_forca, mod_destreza, mod_constituicao, mod_inteligencia, mod_sabedoria, mod_carisma) "
            "VALUES (:c, :n, :cl, 3, :hp, :hp, :vg, :vg, 0, :fm, CAST('[]' AS jsonb), 'ativo', "
            "2, 2, 1, 1, 1, 1) RETURNING id"
        ), {"c": cid, "n": f"[DESCARTAVEL] Cobaia-C {marker}", "cl": "Lutador",
            "hp": COBAIA_HP, "vg": COBAIA_VIGOR, "fm": COBAIA_FADIGA_MAX})).scalar()
        await s.execute(text(
            "INSERT INTO personagem_mana (personagem_id, mp_atual, mp_maximo) VALUES (:p, :mp, :mp)"
        ), {"p": pid, "mp": COBAIA_MP})
        sid = (await s.execute(text(
            "INSERT INTO sessoes (campanha_id, personagem_id, numero_sessao, status, "
            "data_narrativa_inicio) VALUES (:c, :p, 1, 'ativa', :d) RETURNING id"
        ), {"c": cid, "p": pid, "d": "Noite de Vesperas, ano da Vigilia Quebrada"})).scalar()
        await s.commit()
    ids = {"campanha_id": int(cid), "personagem_id": int(pid), "sessao_id": int(sid), "marker": marker}
    print(f"[setup] cobaia de combate criada -> {ids}")
    return ids


# ===========================================================================
# MONTAGEM dos closures reais + BANCO REAL + (mock cronista / faixa forcada)
# + captura plugada (usage proxy + wrap de _separar_estado)
# ===========================================================================
_PATCH_ATTRS = ("ui", "aguardar_conexao_websocket", "MODO_MOCK", "_cronista_mock",
                "classificar_faixa", "_montar_estado_safe", "_carregar_contexto_safe",
                "_resolver_mod_atributo", "_separar_estado", "_get_aclient")


def _salvar_globais() -> dict:
    return {a: getattr(jogo, a) for a in _PATCH_ATTRS}


def _restaurar_globais(orig: dict) -> None:
    for a, v in orig.items():
        setattr(jogo, a, v)


async def montar_vivo(personagem_id: int):
    fake_ui = _FakeUI()
    forced = {"f": None}
    cronista = {"resp": "...\n\n<estado>\npressao_emocional: 0\n</estado>"}
    usage_sink: list = []
    cap = {"resposta": None, "prosa": None}

    jogo.ui = fake_ui

    async def _noop_ws(*a, **k):
        return None
    jogo.aguardar_conexao_websocket = _noop_ws

    # captura de PROSA/ESTADO ditado: wrap de _separar_estado (vale p/ mock E Opus real).
    _orig_sep = jogo._separar_estado

    def _sep(resposta, pressao):
        out = _orig_sep(resposta, pressao)
        cap["resposta"] = resposta
        cap["prosa"] = out[0]
        return out
    jogo._separar_estado = _sep

    if MOCK:
        # Cronista STUBADO -> ZERO Opus. Faixa FORCADA.
        jogo.MODO_MOCK = True
        jogo._cronista_mock = lambda historico: cronista["resp"]
        _orig_cf = jogo.classificar_faixa

        def _fake_cf(d1, d2, mod, cd):
            return forced["f"] if forced["f"] else _orig_cf(d1, d2, mod, cd)
        jogo.classificar_faixa = _fake_cf
        # espinha leve: estado/contexto/mod stubados (rapidos)
        async def _stub_estado(sid, pressao, resultado=None):
            return "[ESTADO]"

        async def _stub_ctx(sid, q=None):
            return ""

        async def _stub_mod(sid, attr):
            return 1
        jogo._montar_estado_safe = _stub_estado
        jogo._carregar_contexto_safe = _stub_ctx
        jogo._resolver_mod_atributo = _stub_mod
    else:
        jogo.MODO_MOCK = False  # Opus real (Passo B)

    # PONTO DE CAPTURA DE USAGE: plugado SEMPRE. A seco (mock) o stream nao roda ->
    # usage_sink fica vazio (campo grava null). No Passo B captura de verdade.
    try:
        _real = jogo._get_aclient()
        jogo._get_aclient = lambda: _ProxyClient(_real, usage_sink)
    except Exception as _e:  # noqa: BLE001 - a seco, sem cliente: degrada, campo segue existindo
        print(f"[usage] proxy nao plugado (a seco, ok): {type(_e).__name__}")

    await jogo._pagina_jogar(com_ficha=True, personagem=personagem_id)
    ao_agir = fake_ui.handlers["jogar_action"]
    ao_rolar = fake_ui.handlers["rolar_dado"]
    fv = ao_agir.__code__.co_freevars
    narrar = ao_agir.__closure__[fv.index("narrar")].cell_contents
    m = Motor(fake_ui, None, [], forced, cronista, narrar, ao_rolar)
    return m, forced, cronista, usage_sink, cap


# ===========================================================================
# LEITURA dos vitais REAIS + snapshot de cells + parse do dado
# ===========================================================================
async def ler_vitais(sid: int) -> dict:
    async with get_session() as s:
        r = (await s.execute(text(
            "SELECT p.hp_atual, p.vigor_atual, p.fadiga_atual, m.mp_atual "
            "FROM sessoes s JOIN personagens p ON p.id = s.personagem_id "
            "LEFT JOIN personagem_mana m ON m.personagem_id = s.personagem_id "
            "WHERE s.id = :sid"
        ), {"sid": sid})).mappings().first()
    return {"hp": r["hp_atual"], "vigor": r["vigor_atual"], "fadiga": r["fadiga_atual"],
            "mp": r["mp_atual"]} if r else {}


def snap_cells(m) -> dict:
    return {
        "teste": m.teste_pendente["intencao"] if m.teste_pendente else None,
        "resultado": m.resultado_pendente,
        "tensao": m.tensao,
        "alvo": m.inimigo["nome"] if m.inimigo else None,
        "bando": [[e["nome"], e["hp"], e["tier"]] for e in m.inimigos],
        "acao": m.acao,
        "via": m._cell("via_atual"),
        "feridas": [[f["nome"], f.get("infectada", False)] for f in m._cell("feridas_ativas")],
        "usadas": list(m._cell("feridas_ja_usadas")),
        "infeccao": [[p["nome"], p["severidade"]] for p in m._cell("_infeccao_pendente")],
    }


def parse_dado(js_list) -> dict | None:
    for c in js_list:
        mo = _RE_DADO.search(str(c))
        if mo:
            return {"d1": int(mo[1]), "d2": int(mo[2]), "mod": int(mo[3]), "cd": int(mo[4]),
                    "faixa": mo[5], "rotulo": mo[6]}
    return None


def _estado_ditado(resposta: str | None) -> str:
    if not resposta:
        return ""
    mo = jogo._RE_ESTADO.search(resposta) or jogo._RE_ESTADO_ABERTO.search(resposta)
    return mo.group(1).strip() if mo else ""


# ===========================================================================
# SELETOR DE ACAO (sequencia-base + override reativo) — vale p/ mock E Opus real
# ===========================================================================
# Falas por FASE (state-driven). O seletor escolhe pela fase/estado do motor, nao por indice.
# ABERTURA: PROVOCACAO escalada que CONVIDA o Cronista a por a ameaca (nao autora inimigo —
# o Opus recusa atacar o vazio). O jogador sente o perigo, saca, encara, avanca pra dentro
# dele. No MOCK a fala e ignorada (spawna por flag); ao vivo, e o que abre a luta.
FALAS_ABRIR = [
    # T1: sente o perigo, NAO ataca nada ainda.
    "O mato a beira da estrada silenciou de vez — nem ave, nem inseto, so o vento alto nas "
    "copas. Levo a mao ao punho da lamina e paro de andar, os olhos na treva entre os "
    "pinheiros. Algo ali me observa; sinto o peso do olhar antes de ver o dono.",
    # T2: provoca — saca a lamina, encara a sombra, chama.
    "Saco a lamina devagar, o aco raspando a bainha, e encaro a sombra fechada entre os "
    "troncos. \"Quem esta ai?\", digo, baixo e firme. \"Mostra-te. Sei que estas ai.\"",
    # T3: avanca pra dentro do perigo, arma erguida, pronto pra cravar no que saltar.
    "Avanco devagar para a mata escura, arma erguida a frente do corpo, o peso nos "
    "calcanhares, pronto pra cravar o aco no primeiro vulto que saltar de entre as arvores.",
]
FALA_ATAQUE     = "Avanco e cravo a lamina no bicho, sem dar espaco nem recuo."
FALA_ESTANCAR   = "Aperto a ferida com a mao livre, sem parar de encarar o bicho."
FALA_DESENGAJAR = "Largo a troca e me afasto pela estrada, deixando o bicho para tras."
FALA_MAGIA_FORA = ("Sozinho na estrada vazia, sem ninguem para atingir, ergo a mao livre e chamo "
                   "a fagulha — so para sentir o que ainda me resta dela; deixo o poder subir e "
                   "arder na palma um instante, contra o ar.")
RESCALDO = ("rescaldo", "Abaixo a arma e respiro, olhando ao redor.")
# re-provocacao FORTE (so no harness): o nudge fraco antigo ("ha mais alguem na estrada")
# deixava o Opus meter um NPC de paz e o 2o combate nunca abria (seed-back nao disparava ao
# vivo). Esta versao e uma acao do jogador que telegrafa AMEACA HOSTIL imediata (besta
# carregando, rosnando) + engajamento corpo-a-corpo -> forca o Cronista a abrir combate:1.
REPROVOCA = ("reprovoca", "Algo grande irrompe da mata a minha frente, rosnando, e vem "
             "rapido pra cima de mim, presas a mostra. Nao recuo: firmo os pes e avanco "
             "com a lamina erguida para cravar nele antes que salte.")
def seletor(turn, m, flags, vitais):
    """MAQUINA DE FASES dirigida pelo ESTADO DO MOTOR (m.tensao/feridas), nao por indice de
    turno nem pela prosa. Devolve (intent, fala, consumiu=False).
      lutar1  -> abre o 1o combate e PRESSIONA o ataque ate o MOTOR fechar (hp<=0, tensao None);
                 estanca UMA ferida no meio (deixa ABERTA p/ o seed-back; nao cura).
      magia   -> 1 turno de conjuracao FORA de combate (tensao None confirmado) -> via:magico.
      reprovocar -> abre o 2o combate (a abertura semeia a infeccao pendente = seed-back).
      lutar2  -> briga curta no 2o combate; depois rescaldo.
    Os SALTOS olham m.tensao is None (fim de combate CONFIRMADO pelo motor), conserta o run
    que ficou preso quando a prosa correu a frente do motor."""
    em_combate = m.tensao is not None
    feridas = m._cell("feridas_ativas")

    if flags["fase"] == "magia_inicial":
        # T1, ANTES de qualquer combate: tensao=None GARANTIDO (nenhuma luta ainda). Conjurar
        # aqui prova (1)(2) ao vivo de forma DETERMINISTICA, sem depender do combate abrir/fechar
        # (que e do Cronista). O arco de combate (e o seed-back, bonus) vem depois.
        flags["fase"] = "lutar1"
        return ("magia_fora", FALA_MAGIA_FORA, False)

    if flags["fase"] == "lutar1":
        if em_combate:
            # estanca UMA ferida (deixa aberta p/ o seed-back; NAO cura), senao pressiona o ataque
            if feridas and flags["estancou"] == 0:
                return ("estancar", FALA_ESTANCAR, False)
            if flags["turnos_lutar1"] >= 9:      # fallback de borda: combate arrastou -> desengaja
                return ("desengajar", FALA_DESENGAJAR, False)
            flags["turnos_lutar1"] += 1
            return ("atk_fisico", FALA_ATAQUE, False)
        elif not flags["ja_combateu"]:
            # PROVOCACAO escalada (convida o spawn): contador proprio (abrir_idx), separado do
            # press em combate (turnos_lutar1). Tardia OK: so sai p/ magia quando tensao virar
            # None DEPOIS de ja_combateu (a luta abriu e fechou). Repete a ultima fala se preciso.
            idx = min(flags["abrir_idx"], len(FALAS_ABRIR) - 1)
            flags["abrir_idx"] += 1
            return ("provoca", FALAS_ABRIR[idx], False)
        else:
            flags["fase"] = "magia"              # motor FECHOU o 1o combate -> magia fora de combate

    if flags["fase"] == "magia":
        flags["fase"] = "reprovocar"
        return ("magia_fora", FALA_MAGIA_FORA, False)   # tensao None confirmado -> via:magico cobra MP

    if flags["fase"] == "reprovocar":
        flags["fase"] = "lutar2"
        flags["encontro"] += 1
        return (REPROVOCA[0], REPROVOCA[1], False)      # abre o 2o combate -> seed-back semeia

    if flags["fase"] == "lutar2":
        if em_combate:
            flags["turnos_lutar2"] += 1
            return ("atk_fisico", FALA_ATAQUE, False)
        flags["fase"] = "rescaldo"
        return (RESCALDO[0], RESCALDO[1], False)

    return (RESCALDO[0], RESCALDO[1], False)


# ===========================================================================
# CRONISTA MOCK (Passo A): traduz o intent + estado atual num <estado> com tags.
# (No Passo B isto NAO roda — o Opus real dita o <estado>.)
# ===========================================================================
FERIDAS_POOL = ["corte no flanco", "talho fundo no ombro", "rasgo na coxa"]


def mock_cronista(intent, m, flags):
    # FECHAR por recuo (fallback do lutar2 / desengajar): tira todos os vivos da luta.
    if (flags.get("forcar_recuo") or intent == "desengajar") and m.inimigos:
        flags["forcar_recuo"] = False
        return "inimigo_recuou: " + ", ".join(e["nome"] for e in m.inimigos)
    # MAGIA fora de combate: SO a via, SEM combate:1 (prova a cobranca de MP fora da luta).
    if intent == "magia_fora":
        return "via: magico"
    # RE-PROVOCACAO: abre o 2o combate (spawn do bravo) -> a abertura semeia a infeccao
    # pendente do 1o combate como ferida INFECTADA (seed-back).
    if intent == "reprovoca":
        return "combate: 1\ninimigo: espreitador | bravo\nacao: ataque"
    tags = []
    # SPAWN do 1o encontro no 1o ataque (lutar1): 1 lobo bravo (hp 12) -> folga p/ ferida nascer
    # (falha_critica), estancar, e o motor zerar o hp em alguns golpes (fecha pela MORTE).
    if intent in ("atk_fisico", "atk_magico", "combo", "provoca") and not flags["spawned"]:
        flags["spawned"] = True
        tags += ["combate: 1", "inimigo: lobo faminto | bravo"]
    elif flags["spawned"] and any(e.get("hp", 0) > 0 for e in m.inimigos) and intent not in ("rescaldo",):
        tags.append("combate: 1")   # SO enquanto ha inimigo VIVO -> sem vivo, a luta fecha
    # acao / via do intent
    if intent in ("atk_fisico", "atk_magico", "combo"):
        via = {"atk_fisico": "fisico", "atk_magico": "magico", "combo": "combo"}[intent]
        tags += ["acao: ataque", f"via: {via}"]
    elif intent == "estancar":
        tags.append("acao: estancar")
    elif intent == "curar":
        tags.append("acao: curar")
    # NASCIMENTO de ferida: turno seguinte a uma falha_critica
    if flags.get("pending_ferida"):
        tags.append(f"ferida: {flags['pending_ferida']}")
        flags["pending_ferida"] = None
    return "\n".join(tags) if tags else "pressao_emocional: 0"


def mock_faixa(intent, m, flags):
    """Faixa FORCADA (so MOCK). A 1a rolagem do combate = falha_critica (cria UMA ferida,
    mantida aberta p/ o seed-back) — vale MESMO se a 1a rolagem vier do turno de PROVOCACAO
    que abriu a luta; depois sucesso ate o alvo cair (motor confirma hp<=0)."""
    if flags["roll_count"] == 0:   # 1a rolagem do combate -> ferida cedo (a semente do seed-back)
        return "falha_critica"
    if intent not in ("atk_fisico", "atk_magico", "combo"):
        return None
    alvo_hp = m.inimigo["hp"] if m.inimigo else 99
    return "sucesso_critico" if alvo_hp <= 6 else "sucesso"


# ===========================================================================
# GRADE DE AUDITORIA (gravada como referencia; aplicada no Passo B sobre o jsonl)
# ===========================================================================
GRADE_MD = """# GRADE DE AUDITORIA — Sessao de combate ao vivo (aplicar sobre o .jsonl)

Ler `transcripts/combate_vivo_<ts>.jsonl` (1 linha/turno) + o `.summary`. Cada criterio
cita TURNO + trecho literal. O motor (cells/vitais/dado) e a verdade objetiva; a prosa e
o que se audita contra ele.

## A — A3: vazamento de numero de mecanica na PROSA
A prosa (`prosa_cronista`) contem numero de regra? ("X de dano", "pressao N", "HP", vida/
mana/vigor/fadiga em digito). Esses numeros devem viver SO no `<estado>` (`estado_ditado`),
nunca na prosa. Listar cada ocorrencia: turno + trecho. Esperado: ZERO digito de mecanica
na prosa (numeros por extenso, se houver).

## B — Tom (witcher-grey, consequencia real)
A prosa entrega consequencia fisica (sangue, dor, exaustao, peso) ou vira coreografia
heroica/limpa? Citar 2-3 trechos representativos. Sinal ruim: golpes "elegantes" sem custo,
heroismo, adjetivacao epica.

## C — Coerencia motor <-> narracao
Cruzar `cells`/`vitais`/`dado` com `prosa_cronista` turno a turno:
  - Houve dano no motor (vigor/hp caiu, ou hp do alvo caiu) -> a prosa narra o golpe/ferimento?
  - Ferida nas cells (`feridas` nao vazio) -> a prosa menciona a ferida/sangramento?
  - Alvo com hp 0 / `[X caiu]` em `resultado` -> a prosa fecha aquela luta (nao segue batendo)?
  - `via: magico/combo` -> a prosa mostra a fagulha/magia, nao so a lamina?
Listar divergencias (turno + o que o motor diz vs o que a prosa diz).

## D — Trava de linguagem (moldura espirita)
alma/fantasma/espirito/demonio usados como SER/entidade? Listar ocorrencias (turno + trecho).
Esperado: zero (a moldura do mundo nao e espirita).

## E — Respeito ao dado
A prosa declara o DESFECHO de uma acao testada ANTES do dado rolar? (ex.: narra o inimigo
caindo no mesmo turno em que so ARMOU o dado, antes do roll). Cruzar: turno onde `dado` e
null mas a prosa ja resolve o golpe -> suspeito. Listar turnos.

## F — Fecho (B1): a ultima imagem
O ultimo turno (rescaldo): a imagem final CONFORTA (alivio facil, promessa de que vai
ficar bem) ou deixa a CONSEQUENCIA de pe (custo, cansaco, o que se perdeu)? Citar a frase
final literal.
"""


# ===========================================================================
# SESSAO
# ===========================================================================
def _ramos_iniciais():
    return {"combate_iniciou": False, "ferida_nasceu": False, "curou": False,
            "estancou": False, "magico": False, "combo": False, "defesa": False,
            "fuga": False, "morte": False, "bando_2plus": False}


def _atualiza_ramos(ramos, cells, intent):
    if cells["tensao"] is not None:
        ramos["combate_iniciou"] = True
    if cells["feridas"]:
        ramos["ferida_nasceu"] = True
    if cells["via"] == "magico":
        ramos["magico"] = True
    if cells["via"] == "combo":
        ramos["combo"] = True
    if cells["acao"] == "defesa":
        ramos["defesa"] = True
    if cells["acao"] == "fugir":
        ramos["fuga"] = True
    if len(cells["bando"]) >= 2:
        ramos["bando_2plus"] = True
    if "caiu" in (cells["resultado"] or ""):
        ramos["morte"] = True
    if intent == "curar":
        ramos["curou"] = True
    if intent == "estancar":
        ramos["estancou"] = True


async def sessao() -> int:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n@@@@@@@@@@ COMBATE VIVO — MOCK={MOCK} (Opus={'NAO' if MOCK else 'SIM'}) — {ts} @@@@@@@@@@")
    pasta = os.path.join(REPO, "transcripts")
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"combate_vivo_{ts}.jsonl")
    # grade de referencia (sempre regravada)
    with open(os.path.join(pasta, "GRADE_AUDITORIA_combate.md"), "w", encoding="utf-8") as f:
        f.write(GRADE_MD)

    ids = None
    exit_code = 0
    orig = _salvar_globais()
    registros: list[dict] = []
    ramos = _ramos_iniciais()
    flags = {"fase": "magia_inicial", "abrir_idx": 0, "turnos_lutar1": 0, "turnos_lutar2": 0,
             "bi": 0, "spawned": False, "combate_iniciou": False, "ja_combateu": False,
             "curou": 0, "estancou": 0, "roll_count": 0, "pending_ferida": None,
             "forcar_recuo": False, "encontro": 1, "reprovocacoes": 0}
    try:
        ids = await setup_combate(ts)
        sid = ids["sessao_id"]
        m, forced, cronista, usage_sink, cap = await montar_vivo(ids["personagem_id"])

        sid_bind = m._cell("sessao_atual")
        assert sid_bind == sid, f"sessao_atual {sid_bind} != descartavel {sid}"
        print(f"[bind] sessao_atual = {sid_bind} (OK)")

        parar_apos = False
        with open(caminho, "w", encoding="utf-8") as fjsonl:
            for turn in range(1, TETO_TURNOS + 1):
                vitais_antes = await ler_vitais(sid)
                intent, fala, consumiu = seletor(turn, m, flags, vitais_antes)
                if consumiu:
                    flags["bi"] += 1

                # Cronista: mock sintetiza o <estado>; Passo B usa Opus real (estado ignorado aqui).
                estado_str = mock_cronista(intent, m, flags) if MOCK else ""
                prosa_mock = f"({intent}) " + fala  # so no mock; no Passo B a prosa vem do Opus

                cap["resposta"] = None
                cap["prosa"] = None
                antes_u = len(usage_sink)
                await m.turno(estado_str, fala=fala, prosa=prosa_mock)

                # dispara o dado se armou
                dado = None
                if m.armou_dado() and m.teste_pendente is not None:
                    faixa = mock_faixa(intent, m, flags) if MOCK else None
                    await m.rolar(faixa)
                    dado = parse_dado(m.ui.js)
                    flags["roll_count"] += 1
                    if dado and dado["faixa"] == "falha_critica" and not flags["pending_ferida"]:
                        idx = min(len([1 for r in registros if r.get("_fc")]), len(FERIDAS_POOL) - 1)
                        flags["pending_ferida"] = FERIDAS_POOL[idx]

                cells = snap_cells(m)
                vitais = await ler_vitais(sid)
                _atualiza_ramos(ramos, cells, intent)
                if cells["tensao"] is not None:
                    flags["combate_iniciou"] = True
                    flags["ja_combateu"] = True   # persiste: a rede de entrada nao re-dispara na re-provocacao
                if intent == "curar":
                    flags["curou"] += 1
                if intent == "estancar":
                    flags["estancou"] += 1

                # (SO MOCK) fecha o 2o combate apos 1 turno de lutar2 (o seed-back ja foi provado
                # na ABERTURA, no turno reprovoca) -> induz o recuo -> motor fecha -> rescaldo. O 1o
                # combate NAO usa isto: fecha pela MORTE (mock_faixa zera o hp) -> exercita o caminho
                # "motor confirma hp<=0", que e o ponto da obra. No Passo B (Opus) nada disto roda.
                if MOCK and flags["fase"] == "lutar2" and m.tensao is not None and flags["turnos_lutar2"] >= 1:
                    flags["forcar_recuo"] = True

                usage = usage_sink[antes_u] if len(usage_sink) > antes_u else None
                u = None
                if usage is not None:
                    u = {"input_tokens": getattr(usage, "input_tokens", None),
                         "output_tokens": getattr(usage, "output_tokens", None),
                         "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
                         "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", None)}

                reg = {
                    "turno_n": turn,
                    "intent": intent,
                    "fala_jogador": fala,
                    "prosa_cronista": cap["prosa"],
                    "estado_ditado": _estado_ditado(cap["resposta"]),
                    "cells": cells,
                    "vitais": vitais,
                    "dado": dado,
                    "usage": u,
                    "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                    "_fc": bool(dado and dado["faixa"] == "falha_critica"),
                }
                registros.append(reg)
                fjsonl.write(json.dumps(reg, ensure_ascii=False) + "\n")
                fjsonl.flush()
                print(f"[T{turn:02d}] {intent:10s} | tensao={cells['tensao']} bando={cells['bando']} "
                      f"| dado={dado['faixa'] if dado else '-'} | vitais={vitais} "
                      f"| feridas={cells['feridas']}")

                # ---- REDES DE SEGURANCA DURAS ----
                # (1) custo real acumulado > teto -> encerra (teardown roda no finally).
                _tin = sum((r["usage"] or {}).get("input_tokens") or 0 for r in registros)
                _tout = sum((r["usage"] or {}).get("output_tokens") or 0 for r in registros)
                _tcr = sum((r["usage"] or {}).get("cache_read_input_tokens") or 0 for r in registros)
                _tcw = sum((r["usage"] or {}).get("cache_creation_input_tokens") or 0 for r in registros)
                _custo = (_tin * RATE["input"] + _tout * RATE["output"]
                          + _tcr * RATE["cache_read"] + _tcw * RATE["cache_write"]) / 1_000_000
                if _custo > TETO_CUSTO_USD:
                    print(f"[ABORT] custo acumulado US${_custo:.2f} > teto US${TETO_CUSTO_USD} -> encerrando.")
                    exit_code = 4
                    break
                # (2) Cronista nao entrou em combate ate o turno limite -> achado, aborta.
                # usa ja_combateu (persistente) p/ NAO re-disparar no intervalo da re-provocacao.
                if turn >= COMBATE_ATE_TURNO and not flags["ja_combateu"]:
                    print(f"[ABORT/ACHADO] Cronista NAO entrou em combate ate o turno {COMBATE_ATE_TURNO} "
                          f"(sem combate:1/inimigo) -> nao queima turnos num arco sem luta.")
                    exit_code = 5
                    break

                if parar_apos:
                    break
                if intent == "rescaldo":
                    parar_apos = True  # grava o rescaldo e encerra no proximo laco-check
                    break

        # ----- sumario -----
        tin = sum((r["usage"] or {}).get("input_tokens") or 0 for r in registros)
        tout = sum((r["usage"] or {}).get("output_tokens") or 0 for r in registros)
        tcr = sum((r["usage"] or {}).get("cache_read_input_tokens") or 0 for r in registros)
        tcw = sum((r["usage"] or {}).get("cache_creation_input_tokens") or 0 for r in registros)
        custo = (tin * RATE["input"] + tout * RATE["output"]
                 + tcr * RATE["cache_read"] + tcw * RATE["cache_write"]) / 1_000_000
        sumario = {
            "_sumario": True, "ts": ts, "mock": MOCK, "modelo": MODELO,
            "total_turnos": len(registros),
            "tokens": {"input": tin, "output": tout, "cache_read": tcr, "cache_write": tcw},
            "custo_estimado_usd": round(custo, 4),
            "ramos_exercitados": {k: bool(v) for k, v in ramos.items()},
        }
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(sumario, ensure_ascii=False) + "\n")
        with open(caminho.replace(".jsonl", ".summary.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(sumario, ensure_ascii=False, indent=2))

        print("\n==================== SUMARIO ====================")
        print(f"  turnos: {sumario['total_turnos']} | mock={MOCK} | custo~US${sumario['custo_estimado_usd']}")
        print(f"  tokens: {sumario['tokens']}")
        print(f"  ramos: {sumario['ramos_exercitados']}")
        print(f"  jsonl: {caminho}")
        if not all(r is not None for r in registros):
            exit_code = 2
    except Exception as e:  # noqa: BLE001
        print(f"[runner] ERRO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        _restaurar_globais(orig)
        limpo = await teardown(ids)
        if not limpo:
            exit_code = exit_code or 3
    print(f"\n[fim] exit_code={exit_code} | Opus={'NAO gasto (mock)' if MOCK else 'gasto'}")
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(sessao()))
