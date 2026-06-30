# -*- coding: utf-8 -*-
"""
test_obediencia_cronista.py — testa se o CRONISTA (o modelo) OBEDECE o loop.

Diferente do test_loop_peca3.py (que testa o encanamento, custo zero), ESTE
chama um modelo de verdade. Foi feito pra gastar o MINIMO:
  - 1 rodada = 2 chamadas (turno 1 + turno 2)
  - comece no Haiku (fracao de centavo); so suba pro Opus quando a FORMA passar
  - veredito automatico no que da pra checar; marca o que precisa do seu olho

Uso:
  python test_obediencia_cronista.py --self-test     # R$0: prova que os checks discriminam (roda em qualquer lugar)
  python test_obediencia_cronista.py --modelo haiku  # centavos: roda contra Haiku (na raiz)
  python test_obediencia_cronista.py --modelo opus   # mais caro: teste final de tom (na raiz)

Pre-requisitos do modo real (na raiz do projeto):
  - existir cronista_prompt.py (o system prompt vivo)
  - ANTHROPIC_API_KEY no ambiente
  - pip install anthropic
"""
import re
import sys

# --- pecas de leitura (mesmas do encanamento) ---
_RE_ESTADO = re.compile(r"<estado>(.*?)</estado>", re.S | re.I)
_RE_TESTE = re.compile(r"teste_pedido\s*:\s*(.+?)\s*\|\s*mod\s*(-?\d+)\s*\|\s*cd\s*(\d+)", re.I)
_FAIXA_CRONISTA = {
    "sucesso_critico": "sucesso crítico", "sucesso": "sucesso",
    "sucesso_parcial": "sucesso parcial", "falha": "falha", "falha_critica": "falha crítica",
}
_NOMES_FAIXA = list(_FAIXA_CRONISTA.values()) + ["sucesso crítico", "falha crítica"]
# pistas fracas de que o Cronista "resolveu" em vez de parar no limiar
_PISTAS_DESFECHO = (
    "consegue", "conseguiu", "conseguindo", "sem dificuldade", "sem problema",
    "com facilidade", "alcança o outro lado", "alcançou o outro lado",
    "pega a bola", "pegou a bola", "desce em seguida", "caiu", "despenca", "despencou",
)

def classificar_faixa_ref(d1, d2, mod, cd):
    soma = d1 + d2
    if soma == 2:  return "falha_critica"
    if soma == 20: return "sucesso_critico"
    M = soma + mod - cd
    if M <= -5: return "falha_critica"
    if M <= -1: return "falha"
    if M <= 2:  return "sucesso_parcial"
    if M <= 6:  return "sucesso"
    return "sucesso_critico"

def _so_prosa(saida):
    m = _RE_ESTADO.search(saida)
    return (saida[: m.start()] if m else saida)

def checar_turno1(saida):
    """Retorna lista de (criterio, status, nota). status: 'PASS'|'FALHA'|'OLHO'."""
    r = []
    bloco = ""
    m = _RE_ESTADO.search(saida)
    if m:
        bloco = m.group(1)
    mt = _RE_TESTE.search(bloco)
    # FIRME: emitiu teste_pedido bem-formado?
    if mt:
        r.append(("C2 emitiu teste_pedido + formato", "PASS",
                  f"intencao='{mt.group(1).strip()}' mod={mt.group(2)} cd={mt.group(3)}"))
    else:
        r.append(("C2 emitiu teste_pedido + formato", "FALHA",
                  "nao achei 'teste_pedido: ... | mod N | cd N' no <estado>"))
    # OLHO: parou no limiar? (heuristica fraca)
    prosa = _so_prosa(saida).lower()
    achou = [p for p in _PISTAS_DESFECHO if p in prosa]
    if achou:
        r.append(("C1 parou no limiar", "OLHO",
                  f"ALERTA: prosa parece resolver ({achou}). Confirme voce se ele ja narrou o desfecho."))
    else:
        r.append(("C1 parou no limiar", "OLHO",
                  "provavel-ok (sem pista de desfecho). Confirme voce: a prosa para ANTES de revelar?"))
    return r, mt

def checar_turno2(saida):
    r = []
    prosa = _so_prosa(saida)
    pl = prosa.lower()
    # FIRME: nao nomeia a faixa?
    nomes = [n for n in _NOMES_FAIXA if n.lower() in pl]
    if nomes:
        r.append(("C5 nao nomeia a faixa", "FALHA", f"vazou nome: {sorted(set(nomes))}"))
    else:
        r.append(("C5 nao nomeia a faixa", "PASS", "nenhum rotulo de faixa na prosa"))
    # FIRME-ish: nao cita numero cru?
    nums = re.findall(r"\b\d+\b", prosa)
    if nums:
        r.append(("C5 nao cita numero cru", "FALHA", f"numeros na prosa: {nums} (raro ser legitimo em narrativa)"))
    else:
        r.append(("C5 nao cita numero cru", "PASS", "sem numeros crus"))
    # OLHO: vestiu a consequencia?
    r.append(("C4 vestiu a consequencia", "OLHO",
              "Confirme voce: o turno 2 ABRE pela consequencia do dado, antes de atender a acao nova?"))
    return r

def _imprimir(titulo, linhas):
    print(f"\n{titulo}")
    for crit, status, nota in linhas:
        tag = {"PASS": "[PASS]", "FALHA": "[FALHA]", "OLHO": "[OLHO]"}[status]
        print(f"  {tag} {crit}")
        if nota:
            print(f"         {nota}")

# =============================================================
# SELF-TEST: prova que os checks discriminam bom de ruim (R$0)
# =============================================================
def self_test():
    print("=" * 60)
    print("SELF-TEST dos checks (sem chamar modelo)")
    print("=" * 60)
    falhas = 0

    s1_boa = ("Ela encara o muro. As mãos encontram a quina áspera e o corpo sobe um palmo, "
              "depois para — o topo ainda longe, o reboco solto sob os dedos.\n"
              "<estado>\npressão_emocional: 2\n"
              "teste_pedido: subir o muro e pegar a bola | mod 0 | cd 13\n</estado>")
    s1_ruim = ("Ela sobe o muro sem dificuldade e pega a bola, descendo em seguida com um sorriso.\n"
               "<estado>\npressão_emocional: 1\n</estado>")
    s2_boa = ("A bola escapa dos dedos e some no matagal do outro lado. O reboco cede; ela "
              "desiste e desce de mãos vazias, o joelho ardendo onde raspou.")
    s2_ruim = ("Falha crítica: com 9 contra a CD 15, ela não consegue e cai do muro.")

    print("\n[fixture] TURNO 1 — saida BOA (deve: C2 PASS, C1 provavel-ok)")
    l, mt = checar_turno1(s1_boa); _imprimir("resultado:", l)
    if not (l[0][1] == "PASS" and "ALERTA" not in l[1][2]): falhas += 1; print("  >> self-test ERROU aqui")

    print("\n[fixture] TURNO 1 — saida RUIM (deve: C2 FALHA, C1 ALERTA)")
    l, mt = checar_turno1(s1_ruim); _imprimir("resultado:", l)
    if not (l[0][1] == "FALHA" and "ALERTA" in l[1][2]): falhas += 1; print("  >> self-test ERROU aqui")

    print("\n[fixture] TURNO 2 — saida BOA (deve: nome PASS, numero PASS)")
    l = checar_turno2(s2_boa); _imprimir("resultado:", l)
    if not (l[0][1] == "PASS" and l[1][1] == "PASS"): falhas += 1; print("  >> self-test ERROU aqui")

    print("\n[fixture] TURNO 2 — saida RUIM (deve: nome FALHA, numero FALHA)")
    l = checar_turno2(s2_ruim); _imprimir("resultado:", l)
    if not (l[0][1] == "FALHA" and l[1][1] == "FALHA"): falhas += 1; print("  >> self-test ERROU aqui")

    print("\n" + "=" * 60)
    print(f"SELF-TEST: {'TODOS OS CHECKS DISCRIMINAM CERTO' if falhas == 0 else str(falhas)+' ERRO(S)'}")
    print("=" * 60)
    return falhas == 0

# =============================================================
# MODO REAL: chama o modelo (na raiz; gasta credito)
# =============================================================
CENA_RISCO = ("Tem um cão grande rosnando, preso por uma corrente velha e enferrujada, "
              "no quintal do vizinho. A bola caiu bem perto da casinha dele. Eu passo "
              "rente ao muro pra alcançar a bola.")
ACAO_T2 = "Pego a bola e volto devagar pelo mesmo caminho."

MODELOS = {"haiku": "claude-haiku-4-5-20251001", "opus": "claude-opus-4-8"}

def rodar_real(modelo_chave):
    try:
        from dotenv import load_dotenv
        load_dotenv()  # carrega ANTHROPIC_API_KEY de um .env, se houver (igual ao jogo)
    except Exception:
        pass
    try:
        from cronista_prompt import CRONISTA_SYSTEM_PROMPT
    except Exception as e:
        print(f"[ERRO] nao importei cronista_prompt: {e}\n       rode na RAIZ do projeto.")
        return
    try:
        from anthropic import Anthropic
    except Exception as e:
        print(f"[ERRO] sem SDK: {e}\n       pip install anthropic")
        return
    modelo = MODELOS.get(modelo_chave, modelo_chave)
    cli = Anthropic()  # le ANTHROPIC_API_KEY do ambiente

    def chamar(mensagens):
        resp = cli.messages.create(model=modelo, max_tokens=800,
                                   system=CRONISTA_SYSTEM_PROMPT, messages=mensagens)
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    print("=" * 60)
    print(f"TESTE DE OBEDIENCIA — modelo: {modelo}")
    print("=" * 60)
    print("\n>>> alinhado ao narrar() real: [ESTADO] vem ANTES da fala; max_tokens=800;")
    print("    no turno 2 a 1a fala volta crua (sem [ESTADO]), so a ultima carrega o estado.")
    print("    FORA de proposito (testa o LOOP, nao o mundo): campos do banco e <contexto>.\n")

    # TURNO 1  (ordem FIEL ao narrar(): [ESTADO] PRIMEIRO, fala do jogador POR ULTIMO)
    fala1 = CENA_RISCO
    u1 = f"[ESTADO]\npressão_emocional: 0\n\n{fala1}"
    saida1 = chamar([{"role": "user", "content": u1}])
    print("----- SAIDA CRUA TURNO 1 -----")
    print(saida1)
    l1, mt = checar_turno1(saida1)
    _imprimir(">>> CHECKS TURNO 1", l1)

    # rola o dado por codigo (determinismo: dado fixo p/ forcar uma falha e ver se ele veste)
    if mt:
        teste = {"intencao": mt.group(1).strip(), "mod": int(mt.group(2)), "cd": int(mt.group(3))}
    else:
        teste = {"intencao": "passar pelo cão e pegar a bola", "mod": 0, "cd": 13}
        print("\n[aviso] sem teste_pedido; usando mod 0 cd 13 so pra seguir o turno 2.")
    d1, d2 = 3, 4  # soma 7 -> tende a falha, p/ testar se ele VESTE a consequencia ruim
    faixa = classificar_faixa_ref(d1, d2, teste["mod"], teste["cd"])
    resultado_teste = f"{teste['intencao']} — {_FAIXA_CRONISTA[faixa]}"
    print(f"\n[dado] {d1}+{d2}={d1+d2}, mod {teste['mod']}, cd {teste['cd']} -> faixa CRUA: {faixa}")
    print(f"[dado] injetando no turno 2: resultado_teste: {resultado_teste}")

    # TURNO 2  (FIEL ao historico real: a 1a user volta CRUA, sem [ESTADO];
    #           so a ULTIMA user carrega o [ESTADO] atual com resultado_teste)
    u2 = f"[ESTADO]\npressão_emocional: 2\nresultado_teste: {resultado_teste}\n\n{ACAO_T2}"
    saida2 = chamar([
        {"role": "user", "content": fala1},
        {"role": "assistant", "content": saida1},
        {"role": "user", "content": u2},
    ])
    print("\n----- SAIDA CRUA TURNO 2 -----")
    print(saida2)
    l2 = checar_turno2(saida2)
    _imprimir(">>> CHECKS TURNO 2", l2)

    print("\n" + "=" * 60)
    print("REGUA DE OURO (seu olho): a prosa do turno 2 bate com a faixa do dado?")
    print(f"  dado deu: {faixa}  ->  a consequencia narrada condiz?")
    print("=" * 60)

if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        ok = self_test()
        if len(sys.argv) == 1:
            print("\n(dica: --modelo haiku p/ rodar contra um modelo de verdade, na raiz)")
        sys.exit(0 if ok else 1)
    if "--modelo" in sys.argv:
        i = sys.argv.index("--modelo")
        chave = sys.argv[i + 1] if i + 1 < len(sys.argv) else "haiku"
        rodar_real(chave)
