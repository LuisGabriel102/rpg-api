# -*- coding: utf-8 -*-
"""
FATIA 3 — RUNNER MANUAL (NAO e um teste pytest): dirige uma sessao narrada REAL por
baixo do /jogar, com Opus 4.8 de verdade, numa sessao DESCARTAVEL com teardown total.

  - GASTA CREDITOS (Opus real, ~8 turnos). Autorizado pelo Gabriel.
  - GRAVA NO BANCO, mas SO numa campanha+personagem+sessao criados aqui e apagados no fim.
    NUNCA toca Doran (id 2/3), Varekhor (id 8) nem as campanhas 1/2 (guardas explicitas).
  - NAO toca jogo.py. NAO roda combate (inimigos=()). NAO da push.

Roda sob demanda:  .venv\Scripts\python.exe tests\harness_sessao_real.py
NAO e coletado pela suite (nome sem prefixo test_, sem funcoes test_).

Fluxo: setup() cria o alvo descartavel -> loop chama jogo.executar_turno_narrado (Opus real)
e, como o caller do /jogar faz depois do combate, grava narrador+pressao via *_safe ->
transcript jsonl em disco -> auditoria automatica (5 greps) -> teardown() apaga tudo por ID
e confirma rastro zero. O teardown roda mesmo em falha parcial (finally).
"""
from __future__ import annotations

import asyncio
import datetime
import glob
import json
import os
import re
import sys
from collections import Counter

REPO = r"C:\Users\Luis\Downloads\nexus-monolito"
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import jogo  # noqa: E402
from db import get_session  # noqa: E402
from sqlalchemy import text  # noqa: E402

# IDs que esta fatia se RECUSA a apagar (trava dura de seguranca).
PERSONAGENS_PROTEGIDOS = {2, 3, 8}      # Doran (2/3), Varekhor (8)
CAMPANHAS_PROTEGIDAS = {1, 2}           # Teste ADR-003 (1), Catedral do Alderyn (2)

MODELO = "claude-opus-4-8"

# ---------------------------------------------------------------------------
# [2] ROTEIROS — 8 acoes narradas cada, ZERO gatilho de combate (sem atacar/golpear/
#     fugir-de-inimigo). Cada roteiro mira um conserto do Bloco B.
# ---------------------------------------------------------------------------
# SESSAO 2 — O FIADOR SOB PRESSAO (alvo B2: segura, nao cede, nao mente, devolve a escolha)
ROTEIRO_FIADOR = [
    "Entro na casa de penhores fechada ha anos, atras de quem dizem que empresta o que ninguem mais empresta.",
    "Digo ao homem atras do balcao que preciso de algo que so ele pode dar, e pergunto o que ele aceita em troca.",
    "Ele faz a oferta; antes de aceitar, pergunto o que voce nao esta me dizendo.",
    "Insisto: quanto isso custa de verdade, nao o que esta escrito no papel.",
    "Digo que nao assino nada ate ele me dizer o preco todo, em voz alta.",
    "Pergunto quem ja pagou esse preco antes de mim, e o que sobrou dessa pessoa.",
    "Olho nos olhos dele e digo que sei que ele esta segurando a pior parte.",
    "Recuo um passo da mesa e pergunto por que ele quer tanto que eu aceite.",
]
# SESSAO 3 — CENA CORAL (alvo B3: 3 figuras na mesma cena, vozes que divergem)
ROTEIRO_CORAL = [
    "Chego ao posto de fronteira ao anoitecer, onde uma fila parou diante da cancela baixada.",
    "Pergunto ao guarda da cancela por que ninguem esta passando esta noite.",
    "O mercador atras de mim resmunga; viro-me e pergunto a ele o que o atrasa tanto.",
    "Um terceiro, de habito e cinzas, prega aos que esperam; aproximo-me e pergunto o que ele anuncia.",
    "Coloco a pergunta para os tres ao mesmo tempo: o que ha do outro lado que ninguem quer dizer.",
    "Aponto a contradicao entre o que o guarda diz e o que o pregador grita, e peco que se entendam.",
    "Pergunto ao mercador se ele pagaria para passar mesmo assim, e quanto.",
    "Antes de decidir, peco que cada um dos tres me diga o que faria no meu lugar.",
]
# SESSAO 4 — VITORIA CUSTOSA (alvo B4: esperanca paga, suja, sem promessa de durar)
ROTEIRO_VITORIA = [
    "Chego a ponte velha sobre o rio cheio, onde uma carroca tombou e a agua sobe rapido sobre quem ficou preso embaixo.",
    "Vejo, presa sob a carroca, uma mulher; e mais longe, levada pela correnteza, a bolsa de remedios que vim buscar de tao longe.",
    "Entro na agua gelada e firmo o pe contra a correnteza para alcancar a mulher primeiro.",
    "Erguo a carroca com o ombro o quanto da e puxo a mulher pelo braco, deixando a bolsa ir.",
    "Arrasto os dois para a margem enquanto a bolsa some na curva escura do rio.",
    "Ajoelho na lama ao lado dela, conferindo se ela respira, e digo que vai ficar bem.",
    "Olho rio abaixo, para onde a bolsa se foi, e penso em quem nao vou poder curar agora.",
    "Levanto a mulher, ponho o braco dela sobre meu ombro e comeco o caminho de volta na chuva.",
]
ROTEIROS = {2: ROTEIRO_FIADOR, 3: ROTEIRO_CORAL, 4: ROTEIRO_VITORIA}


# ===========================================================================
# CAPTURA DE USAGE (tokens) — proxy fino sobre o cliente Anthropic, sem tocar jogo.py.
# Intercepta messages.stream(...).get_final_message() so pra ler .usage de cada turno.
# Se a SDK nao deixar instrumentar, degrada (usage=None) sem derrubar o turno.
# ===========================================================================
class _StreamProxy:
    def __init__(self, mgr, sink):
        self._mgr = mgr
        self._sink = sink

    async def __aenter__(self):
        stream = await self._mgr.__aenter__()
        try:
            _orig = stream.get_final_message

            async def _gfm():
                msg = await _orig()
                try:
                    self._sink.append(msg.usage)
                except Exception:  # noqa: BLE001
                    pass
                return msg

            stream.get_final_message = _gfm  # type: ignore[assignment]
        except Exception:  # noqa: BLE001 - sem instrumentacao; turno segue normal
            pass
        return stream

    async def __aexit__(self, *a):
        return await self._mgr.__aexit__(*a)


class _ProxyMessages:
    def __init__(self, real, sink):
        self._real = real
        self._sink = sink

    def stream(self, **kw):
        return _StreamProxy(self._real.stream(**kw), self._sink)


class _ProxyClient:
    def __init__(self, real, sink):
        self.messages = _ProxyMessages(real.messages, sink)


# ===========================================================================
# [1] SETUP / [6] TEARDOWN — sessao descartavel isolada
# ===========================================================================
async def setup(ts: str) -> dict:
    """Cria campanha + personagem (+mana) + sessao descartaveis. Devolve os IDs."""
    marker = f"FATIA3-{ts}"
    async with get_session() as s:
        cid = (await s.execute(text(
            "INSERT INTO campanhas (nome, status, data_atual_narrativa) "
            "VALUES (:n, 'ativa', :d) RETURNING id"
        ), {"n": f"[DESCARTAVEL] Calibracao {marker}",
            "d": "Noite de Vesperas"})).scalar()

        pid = (await s.execute(text(
            "INSERT INTO personagens (campanha_id, nome, classe_primaria, nivel, "
            "hp_atual, hp_maximo, status_narrativo) "
            "VALUES (:c, :n, :cl, 3, 16, 16, 'ativo') RETURNING id"
        ), {"c": cid, "n": f"[DESCARTAVEL] Cobaia {marker}",
            "cl": "Andarilho da Vigilia"})).scalar()

        await s.execute(text(
            "INSERT INTO personagem_mana (personagem_id, mp_atual, mp_maximo) "
            "VALUES (:p, 6, 6)"
        ), {"p": pid})

        sid = (await s.execute(text(
            "INSERT INTO sessoes (campanha_id, personagem_id, numero_sessao, status, "
            "data_narrativa_inicio) VALUES (:c, :p, 1, 'ativa', :d) RETURNING id"
        ), {"c": cid, "p": pid, "d": "Noite de Vesperas, ano da Vigilia Quebrada"})).scalar()

        await s.commit()
    ids = {"campanha_id": int(cid), "personagem_id": int(pid), "sessao_id": int(sid),
           "marker": marker}
    print(f"[setup] criado -> {ids}")
    return ids


async def teardown(ids: dict) -> bool:
    """Apaga TUDO por ID, em ordem segura (sessoes antes de personagens), e confirma
    rastro zero. Guardas duras: recusa apagar personagem/campanha protegidos."""
    if not ids:
        print("[teardown] nada a limpar (setup nao chegou a criar).")
        return True
    pid = ids.get("personagem_id")
    cid = ids.get("campanha_id")
    sid = ids.get("sessao_id")
    # TRAVAS DE SEGURANCA — aborta antes de qualquer DELETE se mirar alvo real.
    assert pid not in PERSONAGENS_PROTEGIDOS, f"ABORT teardown: personagem {pid} PROTEGIDO"
    assert cid not in CAMPANHAS_PROTEGIDAS, f"ABORT teardown: campanha {cid} PROTEGIDA"

    print(f"[teardown] alvo: campanha={cid} personagem={pid} sessao={sid}")
    try:
        async with get_session() as s:
            # confirma a identidade do alvo antes de apagar (mesmo rigor do Doran)
            if pid is not None:
                nome = (await s.execute(text(
                    "SELECT nome FROM personagens WHERE id=:p"), {"p": pid})).scalar()
                if nome is not None:
                    assert "[DESCARTAVEL]" in nome, \
                        f"ABORT: personagem {pid} nao e descartavel ({nome!r})"
            deletes = []
            if sid is not None:
                r = await s.execute(text("DELETE FROM sessao_turnos WHERE sessao_id=:s"), {"s": sid})
                deletes.append(("sessao_turnos", r.rowcount))
                r = await s.execute(text("DELETE FROM sessoes WHERE id=:s"), {"s": sid})
                deletes.append(("sessoes", r.rowcount))
            if pid is not None:
                r = await s.execute(text("DELETE FROM personagem_saude_mental WHERE personagem_id=:p"), {"p": pid})
                deletes.append(("personagem_saude_mental", r.rowcount))
                r = await s.execute(text("DELETE FROM personagem_mana WHERE personagem_id=:p"), {"p": pid})
                deletes.append(("personagem_mana", r.rowcount))
                r = await s.execute(text("DELETE FROM personagens WHERE id=:p"), {"p": pid})
                deletes.append(("personagens", r.rowcount))
            if cid is not None:
                r = await s.execute(text("DELETE FROM campanhas WHERE id=:c"), {"c": cid})
                deletes.append(("campanhas", r.rowcount))
            await s.commit()
            for tbl, n in deletes:
                print(f"[teardown] DELETE {tbl}: {n}")

            # VERIFICACAO read-only: nada pode sobrar
            sobra = {}
            sobra["sessao_turnos"] = (await s.execute(text(
                "SELECT count(*) FROM sessao_turnos WHERE sessao_id=:s"), {"s": sid})).scalar()
            sobra["sessoes"] = (await s.execute(text(
                "SELECT count(*) FROM sessoes WHERE id=:s"), {"s": sid})).scalar()
            sobra["personagem_saude_mental"] = (await s.execute(text(
                "SELECT count(*) FROM personagem_saude_mental WHERE personagem_id=:p"), {"p": pid})).scalar()
            sobra["personagem_mana"] = (await s.execute(text(
                "SELECT count(*) FROM personagem_mana WHERE personagem_id=:p"), {"p": pid})).scalar()
            sobra["personagens"] = (await s.execute(text(
                "SELECT count(*) FROM personagens WHERE id=:p"), {"p": pid})).scalar()
            sobra["campanhas"] = (await s.execute(text(
                "SELECT count(*) FROM campanhas WHERE id=:c"), {"c": cid})).scalar()
        limpo = all(v == 0 for v in sobra.values())
        print(f"[teardown] VERIFICACAO (tudo 0?) -> {sobra} => {'LIMPO' if limpo else 'SOBROU RASTRO!'}")
        return limpo
    except Exception as e:  # noqa: BLE001
        print(f"[teardown] FALHA: {type(e).__name__}: {e}")
        return False


# ===========================================================================
# [5] AUDITORIA — os 5 greps sobre as prosas
# ===========================================================================
_RE_ANTITESE = re.compile(r"\bn[aã]o\b[^,.;:!?]{1,70}?(?:,\s*mas\b|\s+mas\b|\s+e\s+sim\b)", re.I)
# Forma-irmA da antItese (achada ~3x na Fatia 3): "NAo era X; era Y" / "NAo era X. Era Y".
_RE_FORMA_IRMA = re.compile(
    r"\bn[ãa]o\s+(?:era|é|e|foi|eram|seria)\b[^.;:!?\n]{0,70}[;.—-]+\s*(?:era|é|foi|eram|seria)\b", re.I)
_RE_BANIDO = re.compile(r"\b(almas?|fantasmas?|esp[ií]ritos?|dem[oô]nios?)\b", re.I)
_RE_NUM_STAT = re.compile(
    r"(press[aã]o|vida|mana|vigor|fadiga|hp|mp)\D{0,12}\d"
    r"|\d\D{0,8}(de\s+vida|de\s+mana|de\s+vigor|de\s+press[aã]o|de\s+fadiga)", re.I)
_RE_DIGITO = re.compile(r"\d")
_RE_PALAVRAS = re.compile(r"\S+")


def _abertura(prosa: str, n: int = 8) -> str:
    return " ".join(_RE_PALAVRAS.findall(prosa)[:n])


def auditar(transcript: list[dict]) -> str:
    L = []
    def w(*a): L.append(" ".join(str(x) for x in a))

    w("=" * 74)
    w("AUDITORIA DA SESSAO DE CALIBRACAO — 5 greps sobre as 8 prosas")
    w("=" * 74)

    # (a) ABERTURAS
    w("\n[a] ABERTURAS (primeiras 8 palavras de cada turno):")
    primeiras = []
    for e in transcript:
        ab = _abertura(e["prosa"])
        primeiras.append(ab)
        w(f"   T{e['numero_turno']}: {ab}")
    prim_palavra = [p.split()[0].lower() if p.split() else "" for p in primeiras]
    rep1 = {x for x in prim_palavra if prim_palavra.count(x) > 1 and x}
    w(f"   -> 1a palavra repetida entre turnos: {sorted(rep1) if rep1 else 'NENHUMA'}")
    bigr = [" ".join(p.split()[:2]).lower() for p in primeiras if len(p.split()) >= 2]
    rep2 = {x for x in bigr if bigr.count(x) > 1}
    w(f"   -> 2 primeiras palavras repetidas: {sorted(rep2) if rep2 else 'NENHUMA'}")

    # (b) LEXICO BANIDO / MOLDURA ESPIRITA
    w("\n[b] LEXICO BANIDO / moldura espirita (alma|fantasma|espirito|demonio):")
    achou_b = 0
    for e in transcript:
        for m in _RE_BANIDO.finditer(e["prosa"]):
            achou_b += 1
            ini = max(0, m.start() - 45); fim = min(len(e["prosa"]), m.end() + 45)
            w(f"   T{e['numero_turno']} <{m.group(0)}>: ...{e['prosa'][ini:fim]}...")
    w(f"   -> total de ocorrencias: {achou_b}  ({'OK (zero)' if achou_b == 0 else 'REVISAR contexto'})")

    # (c) NUMEROS CRUS
    w("\n[c] NUMEROS CRUS na prosa (digito ligado a pressao/vida/mana, ou qualquer digito):")
    achou_c = 0
    for e in transcript:
        for m in _RE_NUM_STAT.finditer(e["prosa"]):
            achou_c += 1
            ini = max(0, m.start() - 30); fim = min(len(e["prosa"]), m.end() + 20)
            w(f"   T{e['numero_turno']} STAT+NUM: ...{e['prosa'][ini:fim]}...")
    digitos = [(e["numero_turno"], m.group(0), e["prosa"][max(0, m.start()-25):m.end()+15])
               for e in transcript for m in _RE_DIGITO.finditer(e["prosa"])]
    w(f"   -> vazamento stat+numero: {achou_c}  ({'OK (zero)' if achou_c == 0 else 'VAZOU'})")
    if digitos:
        w(f"   -> digitos crus quaisquer na prosa ({len(digitos)}):")
        for t, d, ctx in digitos:
            w(f"        T{t} '{d}': ...{ctx}...")
    else:
        w("   -> digitos crus quaisquer na prosa: NENHUM (prosa escreve numeros por extenso)")

    # (d) ANTITESE / CACOETE
    w("\n[d] ANTITESE 'nao X, mas Y' (por prosa) + cacoete entre turnos:")
    total_ant = 0
    for e in transcript:
        achados = _RE_ANTITESE.findall(e["prosa"])
        n = len(achados)
        total_ant += n
        flag = "  <<< >1 na mesma prosa" if n > 1 else ""
        w(f"   T{e['numero_turno']}: {n} antitese(s){flag}")
        for m in _RE_ANTITESE.finditer(e["prosa"]):
            w(f"        '{m.group(0).strip()}'")
    w(f"   -> total de antiteses nas 8 prosas: {total_ant} "
      f"(media {total_ant/len(transcript):.2f}/prosa)")

    # (d2) FORMA-IRMA "Nao era X; era Y" (cacoete candidato achado na Fatia 3)
    w("\n[d2] FORMA-IRMA 'Nao era X; era Y / Nao era X. Era Y':")
    total_fi = 0
    for e in transcript:
        for m in _RE_FORMA_IRMA.finditer(e["prosa"]):
            total_fi += 1
            w(f"   T{e['numero_turno']}: '{m.group(0).strip()}'")
    w(f"   -> total da forma-irma nas 8 prosas: {total_fi}")

    # (e) FIDELIDADE ESTADO<->PROSA (heuristico; sinaliza, nao decide)
    w("\n[e] FIDELIDADE estado<->prosa (heuristico — sinaliza p/ leitura humana):")
    feridos = re.compile(r"\b(sangr\w+|ferid\w+|ferimento|chag\w+|cambale\w+|moribund\w+)\b", re.I)
    combatey = re.compile(r"\b(golpe\w*|lamina|espada|investe|ataca|sangue jorr\w+|estoca\w+)\b", re.I)
    flags = 0
    for e in transcript:
        est = e.get("estado_montado", "") or ""
        vida_cheia = bool(re.search(r"vida:\s*16/16", est))
        combate_inativo = ("combate: inativo" in est) or ("combate:" not in est)
        if vida_cheia and feridos.search(e["prosa"]):
            flags += 1
            w(f"   T{e['numero_turno']}: [ESTADO] vida 16/16 mas prosa fala em ferida/sangue -> conferir causa externa")
        if combate_inativo and combatey.search(e["prosa"]):
            flags += 1
            w(f"   T{e['numero_turno']}: [ESTADO] combate inativo mas prosa tem lexico de briga -> conferir")
    if flags == 0:
        w("   -> nenhuma contradicao estado<->prosa detectada pela heuristica.")
    w("   (NB: heuristico — a leitura final das 8 prosas e do Gabriel.)")

    w("\n" + "=" * 74)
    return "\n".join(L)


# ===========================================================================
# [3]/[4] LOOP REAL + transcript
# ===========================================================================
async def rodar(roteiro, numero, *, cauda_voz=False, sufixo="") -> dict:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n@@@@@@@@@@ SESSAO {numero}{sufixo} — {len(roteiro)} turnos | cauda_voz={cauda_voz} @@@@@@@@@@")
    usage_sink: list = []

    # instrumenta o cliente p/ ler usage, sem tocar jogo.py
    _orig_get_aclient = jogo._get_aclient
    real_client = _orig_get_aclient()
    proxy = _ProxyClient(real_client, usage_sink)
    jogo._get_aclient = lambda: proxy  # type: ignore[assignment]

    # observa estado/contexto montados (sem alterar logica): captura msg + contexto_presente
    cap = {"estado": "", "ctx": ""}
    _orig_estado = jogo._montar_estado_safe
    _orig_ctx = jogo._carregar_contexto_safe

    async def _wrap_estado(sid, pressao, resultado=None):
        out = await _orig_estado(sid, pressao, resultado)
        cap["estado"] = out
        return out

    async def _wrap_ctx(sid, q=None):
        out = await _orig_ctx(sid, q)
        cap["ctx"] = out
        return out

    jogo._montar_estado_safe = _wrap_estado    # type: ignore[assignment]
    jogo._carregar_contexto_safe = _wrap_ctx   # type: ignore[assignment]

    ids = None
    transcript: list[dict] = []
    caminho = None
    custo = None
    exit_code = 0
    try:
        ids = await setup(ts)
        sid = ids["sessao_id"]
        estado = jogo.EstadoTurno([], 0, sid, MODELO, None)

        for n, fala in enumerate(roteiro, start=1):
            print(f"\n########## TURNO {n}/{len(roteiro)} ##########")
            cap["estado"] = ""; cap["ctx"] = ""
            antes = len(usage_sink)
            pressao_antes = estado.pressao_atual

            res = await jogo.executar_turno_narrado(
                estado, fala, True,
                ui=jogo._UI_TURNO_NOOP, inimigos=(), deve_abortar=lambda: False,
                cauda_voz=cauda_voz,
            )
            if res.abortado:
                print(f"[runner] turno {n} ABORTADO inesperadamente — parando.")
                exit_code = 2
                break

            # CALLER grava narrador + pressao (como o /jogar faz apos o combate)
            await jogo._gravar_turno_safe(sid, "narrador", res.prosa)
            await jogo._gravar_pressao(sid, res.pressao)

            ctx_md = cap["ctx"] or ""
            estado_md = cap["estado"] or ""
            partes = [estado_md]
            if ctx_md:
                partes.append(f"<contexto>\n{ctx_md}\n</contexto>")
            partes.append(fala)
            msg_montada = "\n\n".join(partes)

            usage = usage_sink[antes] if len(usage_sink) > antes else None
            u = None
            if usage is not None:
                u = {
                    "input_tokens": getattr(usage, "input_tokens", None),
                    "output_tokens": getattr(usage, "output_tokens", None),
                    "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", None),
                    "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
                }

            transcript.append({
                "numero_turno": n,
                "fala_jogador": fala,
                "prosa": res.prosa,
                "pressao_antes": pressao_antes,
                "pressao_depois": res.pressao,
                "atmosfera": res.atmosfera,
                "teste": res.teste,
                "contexto_presente": bool(ctx_md),
                "estado_montado": estado_md,
                "msg_montada": msg_montada,
                "usage": u,
            })
            print(f"[runner] T{n} OK | pressao {pressao_antes}->{res.pressao} | "
                  f"atm={res.atmosfera} | contexto={'PRESENTE' if ctx_md else 'vazio'} | usage={u}")

        # [4] grava o transcript jsonl
        pasta = os.path.join(REPO, "transcripts")
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, f"calibracao_{numero}{sufixo}_{ts}.jsonl")
        with open(caminho, "w", encoding="utf-8") as f:
            for e in transcript:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"\n[runner] transcript salvo: {caminho} ({len(transcript)} entradas)")

        # [5] auditoria
        relatorio = auditar(transcript)
        rel_path = os.path.join(pasta, f"auditoria_calib_{numero}{sufixo}_{ts}.txt")
        with open(rel_path, "w", encoding="utf-8") as f:
            f.write(relatorio)
        print("\n" + relatorio)
        print(f"[runner] auditoria salva: {rel_path}")

        # custo total
        tin = sum((e["usage"] or {}).get("input_tokens") or 0 for e in transcript)
        tout = sum((e["usage"] or {}).get("output_tokens") or 0 for e in transcript)
        tcc = sum((e["usage"] or {}).get("cache_creation_input_tokens") or 0 for e in transcript)
        tcr = sum((e["usage"] or {}).get("cache_read_input_tokens") or 0 for e in transcript)
        custo = {"input": tin, "output": tout, "cache_creation": tcc, "cache_read": tcr}
        print(f"\n[CUSTO] sessao {numero} | {len(transcript)} turnos | input={tin} output={tout} "
              f"cache_creation={tcc} cache_read={tcr}")
    except Exception as e:  # noqa: BLE001
        print(f"[runner] ERRO no loop: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        exit_code = 1
    finally:
        # restaura globais e SEMPRE roda teardown
        jogo._get_aclient = _orig_get_aclient        # type: ignore[assignment]
        jogo._montar_estado_safe = _orig_estado      # type: ignore[assignment]
        jogo._carregar_contexto_safe = _orig_ctx     # type: ignore[assignment]
        limpo = await teardown(ids)
        if not limpo:
            exit_code = exit_code or 3
    return {"numero": numero, "exit_code": exit_code, "caminho": caminho,
            "transcript": transcript, "custo": custo}


# ===========================================================================
# AUDITORIA ENTRE SESSOES (Fatia 3.2) — deriva trans-sessao
# ===========================================================================
def _carregar_jsonl(path: str) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def cross_session(arquivos: list[tuple[str, str]]) -> str:
    """arquivos: [(rotulo, caminho_jsonl)]. Compara aberturas + forma-irma + custo."""
    L = []
    def w(*a): L.append(" ".join(str(x) for x in a))
    sessoes = [(rot, _carregar_jsonl(p)) for rot, p in arquivos]

    w("=" * 74)
    w("AUDITORIA ENTRE SESSOES — deriva trans-sessao")
    w("=" * 74)

    # [A2] aberturas lado a lado
    w("\n[A2] Aberturas (6 palavras) por sessao:")
    todas_ab = []
    for rot, ts in sessoes:
        w(f"  -- {rot} --")
        for e in ts:
            ab = " ".join(_RE_PALAVRAS.findall(e["prosa"])[:6])
            todas_ab.append(ab)
            w(f"     T{e['numero_turno']}: {ab}")
    primeiras = [ab.split()[0].lower() for ab in todas_ab if ab.split()]
    w(f"  -> 1a palavra (freq entre TODAS as sessoes): {dict(Counter(primeiras))}")
    bigr = [" ".join(ab.split()[:2]).lower() for ab in todas_ab if len(ab.split()) >= 2]
    rep = {k: v for k, v in Counter(bigr).items() if v > 1}
    w(f"  -> 2-palavras de abertura repetidas (entre/dentro de sessoes): {rep or 'NENHUMA'}")

    # [A1] forma-irma por sessao
    w("\n[A1] Forma-irma 'Nao era X; era Y' por sessao (Fatia 3 achou ~3 na S1):")
    for rot, ts in sessoes:
        achados = [m.group(0).strip() for e in ts for m in _RE_FORMA_IRMA.finditer(e["prosa"])]
        w(f"     {rot}: {len(achados)}")
        for a in achados:
            w(f"        '{a}'")

    # [custo] por sessao
    w("\n[custo] tokens por sessao (curva do historico):")
    for rot, ts in sessoes:
        g = lambda e, k: (e.get("usage") or {}).get(k) or 0
        tin = sum(g(e, "input_tokens") for e in ts)
        tout = sum(g(e, "output_tokens") for e in ts)
        tcc = sum(g(e, "cache_creation_input_tokens") for e in ts)
        tcr = sum(g(e, "cache_read_input_tokens") for e in ts)
        ult = ts[-1] if ts else {}
        last_in = (ult.get("usage") or {}).get("input_tokens") if ult else None
        w(f"     {rot}: in={tin} out={tout} cache_w={tcc} cache_r={tcr} | input_ultimo_turno={last_in}")

    w("\n" + "=" * 74)
    return "\n".join(L)


async def rodar_todas() -> int:
    resultados = []
    for n in (2, 3, 4):
        try:
            r = await rodar(ROTEIROS[n], n)
        except Exception as e:  # noqa: BLE001
            print(f"[main] sessao {n} estourou: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
            r = {"numero": n, "exit_code": 1, "caminho": None, "transcript": [], "custo": None}
        resultados.append(r)

    # cross-session: inclui a Fatia 3 (sessao_calibracao_*.jsonl) como S1, se existir
    pasta = os.path.join(REPO, "transcripts")
    arquivos: list[tuple[str, str]] = []
    f3 = sorted(glob.glob(os.path.join(pasta, "sessao_calibracao_*.jsonl")))
    if f3:
        arquivos.append(("S1 (Fatia 3 — claustro)", f3[-1]))
    rotulos = {2: "S2 (Fiador/B2)", 3: "S3 (Coral/B3)", 4: "S4 (Vitoria/B4)"}
    for r in resultados:
        if r.get("caminho"):
            arquivos.append((rotulos.get(r["numero"], f"S{r['numero']}"), r["caminho"]))
    if arquivos:
        rel = cross_session(arquivos)
        with open(os.path.join(pasta, "auditoria_entre_sessoes.txt"), "w", encoding="utf-8") as f:
            f.write(rel)
        print("\n" + rel)

    return max((r["exit_code"] for r in resultados), default=0)


if __name__ == "__main__":
    sys.exit(asyncio.run(rodar_todas()))
