# -*- coding: utf-8 -*-
"""Mapeamento atributo -> coluna mod_* da ficha. Puro, sem I/O."""

ATRIBUTO_COL = {
    "forca": "mod_forca",
    "destreza": "mod_destreza",
    "constituicao": "mod_constituicao",
    "inteligencia": "mod_inteligencia",
    "sabedoria": "mod_sabedoria",
    "carisma": "mod_carisma",
    # acentos
    "força": "mod_forca",
    "constituição": "mod_constituicao",
    "inteligência": "mod_inteligencia",
    # siglas PT (3 letras)
    "for": "mod_forca",
    "des": "mod_destreza",
    "con": "mod_constituicao",
    "int": "mod_inteligencia",
    "sab": "mod_sabedoria",
    "car": "mod_carisma",
}


def normalizar_atributo(texto: str) -> str | None:
    """Recebe o atributo cru que o Cronista escreveu (sigla/nome/acento/case).
    Devolve o NOME DA COLUNA mod_* correspondente, ou None se nao reconhecer."""
    if not texto:
        return None
    return ATRIBUTO_COL.get(texto.strip().lower())
