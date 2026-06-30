import secrets
import random

# Rotulos legiveis das 5 faixas (canon)
ROTULOS = {
    "falha_critica":   "FALHA CRITICA",
    "falha":           "FALHA",
    "sucesso_parcial": "SUCESSO PARCIAL",
    "sucesso":         "SUCESSO",
    "sucesso_critico": "SUCESSO CRITICO",
}

def classificar_faixa(d1: int, d2: int, modificador: int, cd: int) -> str:
    """Logica pura e deterministica: 2d10 + mod vs CD -> 1 das 5 faixas.
    Escala canonica Alderyn. Gatilhos naturais sempre ligados."""
    if d1 == 10 and d2 == 10:
        return "sucesso_critico"
    if d1 == 1 and d2 == 1:
        return "falha_critica"
    margem = (d1 + d2 + modificador) - cd
    if margem <= -5:
        return "falha_critica"
    if margem <= -1:          # -4 a -1
        return "falha"
    if margem <= 2:           # 0 a +2
        return "sucesso_parcial"
    if margem <= 6:           # +3 a +6
        return "sucesso"
    return "sucesso_critico"  # +7 ou mais

def rolar_resolucao(modo, rng=random.randint):
    """Rola os dados de resolucao em 3 modos e devolve os 2 dados ESCOLHIDOS (d1, d2).

    O modo entra ja resolvido por quem chama (acumulo binario e externo a esta camada):
      - "normal"      -> rola rng() 2x e devolve (d1, d2) na ORDEM rolada, sem reordenar.
      - "vantagem"    -> rola rng() 3x, descarta a 1a ocorrencia do MENOR, devolve os 2
                         restantes na ordem original.
      - "desvantagem" -> rola rng() 3x, descarta a 1a ocorrencia do MAIOR, devolve os 2
                         restantes na ordem original.

    `rng` e injetavel (default random.randint) -> testavel sem monkeypatch. O par volta
    cru pra classificar_faixa, que ja detecta Kokusen/Refluxo sobre os 2 dados recebidos:
    o dado e honesto nos 3 modos (vantagem [1,1,1] ainda da Refluxo; desvantagem
    [10,10,10] ainda da Kokusen). NAO aplica modificador nem decide gatilhos."""
    if modo == "normal":
        return rng(1, 10), rng(1, 10)
    rolagem = [rng(1, 10), rng(1, 10), rng(1, 10)]
    extremo = min(rolagem) if modo == "vantagem" else max(rolagem)
    rolagem.remove(extremo)   # remove a 1a ocorrencia -> preserva a ordem dos 2 restantes
    return rolagem[0], rolagem[1]

def resolver_2d10(modificador: int, cd: int) -> dict:
    """Rola 2d10 (crypto) + mod vs CD e classifica.
    O modificador ja deve incluir vantagem/desvantagem (flat: +-2,
    ou +-1 leve na infancia) embutida por quem chama."""
    d1 = secrets.randbelow(10) + 1
    d2 = secrets.randbelow(10) + 1
    soma = d1 + d2
    total = soma + modificador
    faixa = classificar_faixa(d1, d2, modificador, cd)
    return {
        "d1": d1, "d2": d2, "soma": soma,
        "modificador": modificador, "cd": cd,
        "total": total, "margem": total - cd,
        "faixa": faixa, "rotulo": ROTULOS[faixa],
    }

if __name__ == "__main__":
    casos = [
        # (d1, d2, mod, cd, faixa_esperada)
        (1, 1, 5, 10, "falha_critica"),     # natural 2 vence mod alto
        (10, 10, 0, 20, "sucesso_critico"), # natural 20 vence cd alta
        (2, 2, 0, 12, "falha_critica"),     # margem -8
        (5, 5, 0, 12, "falha"),             # margem -2
        (6, 6, 0, 12, "sucesso_parcial"),   # margem 0
        (7, 7, 0, 12, "sucesso_parcial"),   # margem +2
        (8, 7, 0, 12, "sucesso"),           # margem +3
        (9, 9, 0, 12, "sucesso"),           # margem +6
        (10, 9, 0, 12, "sucesso_critico"),  # margem +7
    ]
    ok = True
    for d1, d2, mod, cd, esp in casos:
        got = classificar_faixa(d1, d2, mod, cd)
        st = "OK" if got == esp else "ERRO"
        if got != esp:
            ok = False
        print(f"[{st}] ({d1},{d2}) mod{mod:+d} vs CD{cd} -> {got} (esp {esp})")
    print("TODOS OK" if ok else "FALHOU")
