# -*- coding: utf-8 -*-
"""
test_loop_peca3.py — testa o ENCANAMENTO da peca 3 SEM gastar credito de LLM.

O que prova (deterministico, R$0):
  Cronista emite <estado> com teste_pedido  ->  jogo.py extrai {intencao, mod, cd}
  ->  dado resolve (Dice Engine) escolhendo a faixa  ->  monta resultado_pendente
  ->  proximo turno injeta 'resultado_teste:' no [ESTADO] de entrada.

O que NAO prova (precisa de modelo): se o Opus OBEDECE o prompt (para no limiar,
veste sem nomear). Isso e o teste com Opus/Haiku, nao codigo.

Uso:
  python test_loop_peca3.py          # modo embutido: roda em qualquer lugar
  python test_loop_peca3.py --vivo   # na RAIZ: confere contra o Dice Engine real
                                      # e faz string-match das pecas no jogo.py
"""
import re
import sys

# =================================================================
# Dice Engine de REFERENCIA (spec canonica §7.5 do handoff)
# =================================================================
def classificar_faixa_ref(d1, d2, mod, cd):
    soma = d1 + d2
    if soma == 2:           # natural 2 (1+1) forca falha critica sempre
        return "falha_critica"
    if soma == 20:          # natural 20 (10+10) forca sucesso critico sempre
        return "sucesso_critico"
    M = soma + mod - cd
    if M <= -5:  return "falha_critica"
    if M <= -1:  return "falha"
    if M <= 2:   return "sucesso_parcial"
    if M <= 6:   return "sucesso"
    return "sucesso_critico"

# =================================================================
# PECAS VIVAS da peca 3 (copia verbatim do jogo.py / relatorio Claude Code)
# =================================================================
_RE_ESTADO   = re.compile(r"<estado>(.*?)</estado>", re.S | re.I)
_RE_PRESSAO  = re.compile(r"press[aã]o_emocional\s*:\s*(\d+)", re.I)
ATMOSFERAS   = ("ermo", "mata", "frio", "sangue", "corte")
_RE_ATMOSFERA = re.compile(r"atmosfera\s*:\s*([a-z]+)", re.I)
_RE_TESTE = re.compile(
    r"teste_pedido\s*:\s*(.+?)\s*\|\s*mod\s*(-?\d+)\s*\|\s*cd\s*(\d+)", re.I
)
_FAIXA_CRONISTA = {
    "sucesso_critico": "sucesso crítico",
    "sucesso": "sucesso",
    "sucesso_parcial": "sucesso parcial",
    "falha": "falha",
    "falha_critica": "falha crítica",
}

def _separar_estado(resposta, pressao_anterior):
    m = _RE_ESTADO.search(resposta)
    if not m:
        return resposta.strip(), pressao_anterior, None, None
    prosa = resposta[: m.start()].rstrip()
    bloco = m.group(1)
    nova = pressao_anterior
    mp = _RE_PRESSAO.search(bloco)
    if mp:
        nova = max(0, min(10, int(mp.group(1))))
    atm = None
    ma = _RE_ATMOSFERA.search(bloco)
    if ma and ma.group(1).lower() in ATMOSFERAS:
        atm = ma.group(1).lower()
    teste = None
    mt = _RE_TESTE.search(bloco)
    if mt:
        teste = {"intencao": mt.group(1).strip(), "mod": int(mt.group(2)), "cd": int(mt.group(3))}
    return prosa, nova, atm, teste

def resolver_turno_dado(teste_pendente, d1, d2, classificar):
    """Replica a logica nova de ao_rolar_dado: escolhe mod/cd, classifica, monta o resultado."""
    MOD_MOCK, DC_MOCK = 2, 12
    if teste_pendente:
        mod, cd, intencao = teste_pendente["mod"], teste_pendente["cd"], teste_pendente["intencao"]
    else:
        mod, cd, intencao = MOD_MOCK, DC_MOCK, None
    faixa = classificar(d1, d2, mod, cd)
    resultado_pendente = None
    if intencao is not None:
        resultado_pendente = f"{intencao} — {_FAIXA_CRONISTA[faixa]}"
    return faixa, resultado_pendente

def montar_estado(pressao, resultado_teste=None):
    """Replica a injecao nova de _montar_estado_safe (so a parte da peca 3)."""
    linhas = [f"pressão_emocional: {pressao}"]
    if resultado_teste:
        linhas.append(f"resultado_teste: {resultado_teste}")
    return re.sub(r"\n{2,}", "\n", "[ESTADO]\n" + "\n".join(linhas))

# =================================================================
# Mini-framework de teste
# =================================================================
_passou = 0
_falhou = 0
def check(nome, cond, detalhe=""):
    global _passou, _falhou
    if cond:
        _passou += 1
        print(f"  [PASS] {nome}")
    else:
        _falhou += 1
        print(f"  [FALHA] {nome}  {detalhe}")

# =================================================================
# TESTES — encanamento
# =================================================================
def testes(classificar):
    print("\n--- A. extracao do teste_pedido (Cronista -> jogo.py) ---")
    saida_viga = (
        "O segundo passo nao. A viga cedeu um dedo e voltou, com um estalo grave.\n"
        "<estado>\n"
        "pressao_emocional: 3\n"
        "teste_pedido: atravessar a viga encharcada ate o outro telhado | mod 0 | cd 15\n"
        "</estado>"
    )
    prosa, pressao, atm, teste = _separar_estado(saida_viga, 0)
    check("extrai intencao", teste and teste["intencao"] == "atravessar a viga encharcada ate o outro telhado", repr(teste))
    check("extrai mod 0", teste and teste["mod"] == 0, repr(teste))
    check("extrai cd 15", teste and teste["cd"] == 15, repr(teste))
    check("pressao = 3 (nao confunde com o 15)", pressao == 3, f"pressao={pressao}")
    check("prosa nao contem o bloco", "<estado>" not in prosa, repr(prosa))

    saida_neg = "Ela hesita.\n<estado>\npressao_emocional: 6\nteste_pedido: recuar sem ser vista | mod -2 | cd 14\n</estado>"
    _, _, _, t2 = _separar_estado(saida_neg, 0)
    check("mod NEGATIVO (-2)", t2 and t2["mod"] == -2, repr(t2))

    print("\n--- B. cena sem risco / sem bloco (degrada sem quebrar) ---")
    _, p3, _, t3 = _separar_estado("<estado>\npressao_emocional: 5\n</estado>", 0)
    check("sem teste_pedido -> teste None", t3 is None, repr(t3))
    check("pressao ainda lida = 5", p3 == 5, f"p={p3}")
    pr4, p4, a4, t4 = _separar_estado("so prosa, sem bloco nenhum", 7)
    check("sem bloco -> teste None e pressao mantida (7)", t4 is None and p4 == 7, f"t={t4} p={p4}")

    print("\n--- C. faixa SEMPRE mapeia (zero KeyError no ao_rolar_dado) ---")
    erros = []
    n = 0
    for d1 in range(1, 11):
        for d2 in range(1, 11):
            for cd in (8, 10, 12, 14, 16, 18, 20):
                for mod in (-3, -1, 0, 2, 5, 8):
                    n += 1
                    f = classificar(d1, d2, mod, cd)
                    if f not in _FAIXA_CRONISTA:
                        erros.append((d1, d2, mod, cd, f))
    check(f"todas as {n} combinacoes mapeiam em _FAIXA_CRONISTA", not erros, str(erros[:3]))

    print("\n--- D. naturais 2/20 forcam o extremo ---")
    check("natural 2 com mod +10 ainda e falha_critica", classificar(1, 1, 10, 1) == "falha_critica")
    check("natural 20 com mod -10 ainda e sucesso_critico", classificar(10, 10, -10, 30) == "sucesso_critico")

    print("\n--- E. limiares de margem (M = soma+mod-cd) ---")
    # usa pares NAO-naturais para isolar a margem
    check("M=-5 -> falha_critica", classificar(4, 3, 0, 12) == "falha_critica", "soma7 M=-5")
    check("M=-4 -> falha",          classificar(4, 4, 0, 12) == "falha", "soma8 M=-4")
    check("M=-1 -> falha",          classificar(5, 6, 0, 12) == "falha", "soma11 M=-1")
    check("M=0  -> sucesso_parcial", classificar(6, 6, 0, 12) == "sucesso_parcial", "soma12 M=0")
    check("M=+2 -> sucesso_parcial", classificar(7, 7, 0, 12) == "sucesso_parcial", "soma14 M=+2")
    check("M=+3 -> sucesso",         classificar(8, 7, 0, 12) == "sucesso", "soma15 M=+3")
    check("M=+6 -> sucesso",         classificar(9, 9, 0, 12) == "sucesso", "soma18 M=+6")
    check("M=+7 -> sucesso_critico", classificar(9, 9, 1, 12) == "sucesso_critico", "soma18 +1 M=+7")

    print("\n--- F. string de retorno (formato exato com travessao) ---")
    faixa, res = resolver_turno_dado({"intencao": "atravessar a viga", "mod": 0, "cd": 15}, 4, 4, classificar)
    check("dado 4+4 vs cd15 = falha_critica", faixa == "falha_critica", f"faixa={faixa}")
    check("resultado = 'atravessar a viga — falha crítica'", res == "atravessar a viga — falha crítica", repr(res))
    check("usa em-dash U+2014", res is not None and "\u2014" in res, repr(res))

    print("\n--- G. tecla 'd' / sem pendente -> NAO gera resultado ---")
    faixa, res = resolver_turno_dado(None, 5, 5, classificar)
    check("sem teste_pendente -> resultado None", res is None, repr(res))

    print("\n--- H. injecao no [ESTADO] de entrada (turno seguinte) ---")
    e_com = montar_estado(4, "atravessar a viga — falha crítica")
    check("com resultado -> linha resultado_teste presente", "resultado_teste: atravessar a viga — falha crítica" in e_com, repr(e_com))
    check("sem linha em branco interna (assert do _montar)", "\n\n" not in e_com, repr(e_com))
    e_sem = montar_estado(4)
    check("sem resultado -> SEM linha resultado_teste", "resultado_teste" not in e_sem, repr(e_sem))

    print("\n--- I. round-trip ponta a ponta (2 turnos) ---")
    # turno 1: Cronista pede o teste
    _, _, _, teste = _separar_estado(saida_viga, 0)
    teste_pendente = teste
    # jogador rola (dado fixo p/ determinismo): 7+2=9, +0, vs 15 -> M=-6 -> falha_critica
    faixa, resultado_pendente = resolver_turno_dado(teste_pendente, 7, 2, classificar)
    teste_pendente = None  # consumido
    # turno 2: entra no [ESTADO]
    estado_entrada = montar_estado(3, resultado_pendente)
    esperado = "resultado_teste: atravessar a viga encharcada ate o outro telhado — falha crítica"
    check("turno 2 carrega o resultado certo", esperado in estado_entrada, repr(estado_entrada))
    check("pendente foi consumido (None)", teste_pendente is None)

# =================================================================
# MODO --vivo: confere contra o codigo real (rodar na RAIZ)
# =================================================================
def modo_vivo():
    print("\n=== MODO --vivo: conferindo contra o codigo real ===")
    ok = True
    # 1) Dice Engine real
    try:
        from app.resolucao_2d10 import classificar_faixa as vivo
        print("[ok] importou app.resolucao_2d10.classificar_faixa")
    except Exception as e:
        print(f"[ERRO] nao importou o Dice Engine vivo: {e}")
        print("       (rode este script na RAIZ do projeto, onde existe app/resolucao_2d10.py)")
        return False
    # 2) ref == vivo em todas as combinacoes
    div = []
    for d1 in range(1, 11):
        for d2 in range(1, 11):
            for cd in (8, 10, 12, 14, 16, 18, 20):
                for mod in (-3, -1, 0, 2, 5, 8):
                    if classificar_faixa_ref(d1, d2, mod, cd) != vivo(d1, d2, mod, cd):
                        div.append((d1, d2, mod, cd))
    if div:
        ok = False
        print(f"[FALHA] ref != vivo em {len(div)} casos, ex: {div[:5]}")
    else:
        print("[PASS] Dice Engine de referencia == Dice Engine vivo (todas as combinacoes)")
    # 3) string-match das pecas no jogo.py
    try:
        with open("jogo.py", encoding="utf-8") as f:
            jp = f.read()
        marcos = ['_RE_TESTE', 'teste_pedido', '_FAIXA_CRONISTA', 'resultado_teste',
                  '"sucesso crítico"', '"falha crítica"']
        faltam = [m for m in marcos if m not in jp]
        if faltam:
            ok = False
            print(f"[FALHA] jogo.py nao contem: {faltam}")
        else:
            print("[PASS] jogo.py contem todas as pecas da peca 3 (lado-codigo)")
    except Exception as e:
        print(f"[aviso] nao leu jogo.py: {e}")
    # 4) cronista_prompt.py
    try:
        with open("cronista_prompt.py", encoding="utf-8") as f:
            cp = f.read()
        c_res = cp.count("resultado_teste")
        c_ped = cp.count("teste_pedido")
        if c_res == 1 and c_ped == 2:
            print(f"[PASS] cronista_prompt.py: resultado_teste x{c_res}, teste_pedido x{c_ped}")
        else:
            ok = False
            print(f"[FALHA] cronista_prompt.py contagem inesperada: resultado_teste x{c_res}, teste_pedido x{c_ped} (esperado 1 e 2)")
    except Exception as e:
        print(f"[aviso] nao leu cronista_prompt.py: {e}")
    return ok

# =================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO ENCANAMENTO — peca 3 (sem credito de LLM)")
    print("=" * 60)
    vivo_ok = True
    if "--vivo" in sys.argv:
        vivo_ok = modo_vivo()
        try:
            from app.resolucao_2d10 import classificar_faixa as classificar
            print("\n>>> rodando os testes de encanamento contra o Dice Engine VIVO")
        except Exception:
            classificar = classificar_faixa_ref
            print("\n>>> Dice vivo indisponivel; testes contra a REFERENCIA")
    else:
        classificar = classificar_faixa_ref
        print(">>> modo embutido (referencia). Use --vivo na raiz p/ conferir o codigo real.")
    testes(classificar)
    print("\n" + "=" * 60)
    print(f"RESULTADO: {_passou} PASS / {_falhou} FALHA" + ("" if vivo_ok else "  (+ divergencia no modo --vivo)"))
    print("=" * 60)
    sys.exit(0 if (_falhou == 0 and vivo_ok) else 1)
