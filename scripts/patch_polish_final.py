"""patch_polish_final.py - 4 ajustes cosmeticos finais."""
from pathlib import Path
import sys

MAIN = Path("main.py")

SUBSTITUICOES = [
    # 1. Versao
    (
        '"v0.4.3"',
        '"v0.6.0"',
        "Versao v0.4.3 -> v0.6.0",
    ),
    # 2. Rodape da home
    (
        "Módulo 5.3 OK. Catedral ergue-se: NPCs + Estrelas online.",
        "Módulo 6.3 OK. Catedral ergue-se: NPCs, Estrelas e Vocações online.",
        "Rodape home atualizado",
    ),
    # 3. Acento em DISPONIVEL
    (
        'ui.label("Disponivel:").classes',
        'ui.label("Disponível:").classes',
        "Acento em DISPONIVEL",
    ),
    # 4. Card de vocacoes na home (texto anti-traducao)
    (
        '"Classes e multiclasses narradas."',
        '"Vocações e multiclasses narradas."',
        "Card de vocacoes: Classes -> Vocacoes (anti-traducao Chrome)",
    ),
]


def main() -> int:
    c = MAIN.read_text(encoding="utf-8")
    antes = len(c)

    print("=" * 72)
    aplicadas = 0
    for old, new, descricao in SUBSTITUICOES:
        if new in c and old not in c:
            print(f"  [IDEMPOTENTE] {descricao}")
            continue
        if old not in c:
            print(f"  [AVISO] Nao encontrado: {descricao}")
            print(f"           Procurou: {old[:60]!r}")
            continue
        c = c.replace(old, new, 1)
        aplicadas += 1
        print(f"  [OK] {descricao}")

    if aplicadas == 0:
        print("\n  Nada mudou.")
        return 0

    MAIN.write_text(c, encoding="utf-8")
    depois = len(c)

    print("=" * 72)
    print(f"  {aplicadas} substituicoes aplicadas.")
    print(f"  Antes: {antes} | Depois: {depois} ({depois - antes:+d})")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())