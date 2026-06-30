# -*- coding: utf-8 -*-
"""
test_atributos.py - Teste do mapeamento atributo -> coluna mod_*.

Prova a peca "attribute resolver" no nivel que tem risco: a normalizacao
do que o Cronista escreve (sigla / nome / acento / case) para o nome da
coluna mod_* certa. NAO toca o banco. NAO chama modelo. R$0.

Rodar da RAIZ do projeto (nexus-monolito):
    python test_atributos.py

Contrato testado (app/atributos.py):
    normalizar_atributo(texto: str) -> str | None
      - devolve o NOME DA COLUNA ("mod_destreza", ...) para entradas validas
      - devolve None para qualquer coisa que nao seja um dos 6 atributos
"""

import sys

try:
    from app.atributos import normalizar_atributo
except ImportError as e:
    print("FALHA DE IMPORT: nao achei app/atributos.py.")
    print("  -> Rode da raiz do projeto, e construa app/atributos.py antes.")
    print("  detalhe:", e)
    sys.exit(2)


# entradas que DEVEM mapear -> coluna esperada
CASOS_OK = {
    # nome cru
    "forca": "mod_forca",
    "destreza": "mod_destreza",
    "constituicao": "mod_constituicao",
    "inteligencia": "mod_inteligencia",
    "sabedoria": "mod_sabedoria",
    "carisma": "mod_carisma",
    # com acento
    "força": "mod_forca",
    "constituição": "mod_constituicao",
    "inteligência": "mod_inteligencia",
    # case e espaco
    "Destreza": "mod_destreza",
    " DESTREZA ": "mod_destreza",
    "Força": "mod_forca",
    "  Sabedoria": "mod_sabedoria",
    # sigla PT (3 letras)
    "for": "mod_forca",
    "des": "mod_destreza",
    "con": "mod_constituicao",
    "int": "mod_inteligencia",
    "sab": "mod_sabedoria",
    "car": "mod_carisma",
    "DES": "mod_destreza",
    "Car": "mod_carisma",
}

# entradas que NAO sao atributo -> devem cair no fallback (None)
CASOS_FALLBACK = [
    "sorte",
    "magia",
    "vigor",
    "xyz",
    "destrza",   # typo de propósito
    "",
    "   ",
    "mod",
    "atributo",
]


def main() -> int:
    falhas = []

    for entrada, esperado in CASOS_OK.items():
        obtido = normalizar_atributo(entrada)
        if obtido != esperado:
            falhas.append(
                f"  [OK-CASE] {entrada!r}: esperado {esperado!r}, obtido {obtido!r}"
            )

    for entrada in CASOS_FALLBACK:
        obtido = normalizar_atributo(entrada)
        if obtido is not None:
            falhas.append(
                f"  [FALLBACK] {entrada!r}: esperado None, obtido {obtido!r}"
            )

    total = len(CASOS_OK) + len(CASOS_FALLBACK)
    if falhas:
        print(f"FALHOU: {len(falhas)}/{total} casos errados.")
        for linha in falhas:
            print(linha)
        return 1

    print(f"PASSOU: {total}/{total} casos.")
    print(f"  - {len(CASOS_OK)} variantes mapeadas certo (sigla/nome/acento/case)")
    print(f"  - {len(CASOS_FALLBACK)} nao-atributos caíram no fallback (None)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
