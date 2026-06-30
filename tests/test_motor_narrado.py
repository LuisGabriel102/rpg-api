# -*- coding: utf-8 -*-
"""
FATIA 1 — Golden/caracterizacao do MOTOR DE TURNO NARRADO (sem combate).

Fotografa o comportamento ATUAL do `narrar` para turnos NARRADOS (estado ditado so
com pressao_emocional + atmosfera, ZERO tags de combate). Serve de REDE para a
extracao da funcao-motor: o codigo extraido tem de reproduzir este golden byte-a-byte.

Reusa o harness de combate (FakeUI no-op + MODO_MOCK + _cronista_mock ditado +
DB-log via _FakeSession). Deterministico, isolado (zero DB/Opus/browser).

Captura, por turno:
  (1) msgs[-1].content montada (estado + contexto + fala)  -> via wrapper de _cronista_mock
  (2) prosa retornada                                       -> via wrapper de _separar_estado
  (3) tupla (prosa, pressao, atmosfera, teste, opcoes)      -> via wrapper de _separar_estado
  (4) db_log (jogador, narrador, pressao)                   -> via stubs de gravacao
"""
import asyncio

import jogo
from harness_combate import montar_motor


def _run(coro):
    return asyncio.run(coro)


async def _capturar_golden(monkeypatch):
    """Dirige 3 turnos NARRADOS pelo `narrar` real e devolve o golden capturado."""
    motor = await montar_motor(monkeypatch, com_ficha=False)

    cap = {"msg": None, "sep": None}
    db_log = []

    # (1) captura a ultima msg montada (o que iria pro Cronista)
    def _cron(msgs):
        cap["msg"] = msgs[-1]["content"]
        return motor._cronista["resp"]
    monkeypatch.setattr(jogo, "_cronista_mock", _cron)

    # (2)+(3) captura o retorno de _separar_estado SEM mudar a logica (so observa)
    _orig_sep = jogo._separar_estado
    def _sep(resposta, pressao_anterior):
        out = _orig_sep(resposta, pressao_anterior)
        cap["sep"] = out
        return out
    monkeypatch.setattr(jogo, "_separar_estado", _sep)

    # (4) registra as gravacoes na ordem em que ocorrem
    async def _rec_turno(sid, papel, conteudo):
        db_log.append(("turno", papel, conteudo))
    async def _rec_pressao(sid, valor):
        db_log.append(("pressao", valor))
    monkeypatch.setattr(jogo, "_gravar_turno_safe", _rec_turno)
    monkeypatch.setattr(jogo, "_gravar_pressao", _rec_pressao)

    golden = []

    async def _turno(fala, prosa, estado):
        db_log.clear()
        cap["msg"] = None
        cap["sep"] = None
        await motor.turno(estado, fala=fala, prosa=prosa, mostrar=True)
        golden.append({
            "msg": cap["msg"],
            "prosa": cap["sep"][0],
            "tupla": tuple(cap["sep"]),
            "db_log": list(db_log),
        })

    # turno 1: limpo (pressao sobe de 0 -> 3, sem atmosfera)
    await _turno("Doran cruza o salao em silencio.", "O salao estava vazio.",
                 "pressao_emocional: 3")
    # turno 2: pressao muda (3 -> 6) + atmosfera VALIDA (frio)
    await _turno("Ele forca a porta dos fundos.", "A madeira cedeu.",
                 "pressao_emocional: 6\natmosfera: frio")
    # turno 3: atmosfera FORA da whitelist (neon -> ignorada); pressao estavel (6)
    await _turno("Desce a escada.", "Os degraus afundavam.",
                 "pressao_emocional: 6\natmosfera: neon")

    return golden


# A2.1-flip: o narrar real agora passa cauda_voz=True, entao a msg montada traz o bloco
# <cauda_de_voz> entre o [ESTADO] e a fala. Builder LITERAL do bloco esperado (copia
# independente do formato, p/ o golden continuar sendo byte-check). T1 (0 respostas no
# historico) usa a variante so-lembrete; T2+ trazem as aberturas dos turnos anteriores.
_CAUDA_VOZ = "Voz: terceira pessoa, passado, prosa contida."
_CAUDA_POS = ("Varie a entrada — abra por som, gesto consumado, sensação no corpo "
              "ou mudança de luz.")
_CAUDA_CONT = ("A contenção governa: o peso da cena decide a extensão, não um molde. "
               "Violência de rotina é factual e breve. As palavras mais duras usam o menor número delas.")


def _cauda_esperada(aberturas):
    if not aberturas:
        return f"<cauda_de_voz>\n{_CAUDA_VOZ} {_CAUDA_POS}\n{_CAUDA_CONT}\n</cauda_de_voz>"
    lista = "\n".join(f'- "{a}"' for a in aberturas)
    return (f"<cauda_de_voz>\n{_CAUDA_VOZ} Não reabra como as últimas respostas:\n"
            f"{lista}\n{_CAUDA_POS}\n{_CAUDA_CONT}\n</cauda_de_voz>")


# GOLDEN esperado (caracterizacao do `narrar` ATUAL). Se o `narrar` mudar, isto quebra
# de proposito. A extracao da Fatia 1 tem de reproduzir EXATAMENTE estes valores.
# A unica coisa que mudou no flip foi a PRESENCA da cauda na msg; prosa/tupla/db_log iguais.
ESPERADO = [
    {
        "msg": "[ESTADO]\n\n"
               + _cauda_esperada([])
               + "\n\nDoran cruza o salao em silencio.",
        "prosa": "O salao estava vazio.",
        "tupla": ("O salao estava vazio.", 3, None, None, None),
        "db_log": [
            ("turno", "jogador", "Doran cruza o salao em silencio."),
            ("turno", "narrador", "O salao estava vazio."),
            ("pressao", 3),
        ],
    },
    {
        "msg": "[ESTADO]\n\n"
               + _cauda_esperada(["O salao estava vazio."])
               + "\n\nEle forca a porta dos fundos.",
        "prosa": "A madeira cedeu.",
        "tupla": ("A madeira cedeu.", 6, "frio", None, None),
        "db_log": [
            ("turno", "jogador", "Ele forca a porta dos fundos."),
            ("turno", "narrador", "A madeira cedeu."),
            ("pressao", 6),
        ],
    },
    {
        "msg": "[ESTADO]\n\n"
               + _cauda_esperada(["O salao estava vazio.", "A madeira cedeu."])
               + "\n\nDesce a escada.",
        "prosa": "Os degraus afundavam.",
        "tupla": ("Os degraus afundavam.", 6, None, None, None),
        "db_log": [
            ("turno", "jogador", "Desce a escada."),
            ("turno", "narrador", "Os degraus afundavam."),
            ("pressao", 6),
        ],
    },
]


def test_motor_narrado_golden(monkeypatch):
    golden = _run(_capturar_golden(monkeypatch))
    # imprime o golden capturado (visivel com -s) para auditoria
    print("\n=== GOLDEN CAPTURADO (narrar atual) ===")
    for i, g in enumerate(golden, 1):
        print(f"--- turno {i} ---")
        print("  msg    :", repr(g["msg"]))
        print("  prosa  :", repr(g["prosa"]))
        print("  tupla  :", g["tupla"])
        print("  db_log :", g["db_log"])
    assert golden == ESPERADO
