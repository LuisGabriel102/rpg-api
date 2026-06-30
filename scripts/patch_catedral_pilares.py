"""patch_catedral_pilares.py - Atualiza main.py pra nova nomenclatura de pilares."""
from pathlib import Path
import sys

MAIN = Path("main.py")

# 1. Constantes
CONST_OLD = '''_VOC_SORTABLE_FIELDS = {"id", "nome_ptbr", "pilar", "tipo"}
_PILARES_ROMANOS = ("I", "II", "III", "IV", "V")
_PILARES_VALIDOS = _PILARES_ROMANOS + ("Fundida",)'''

CONST_NEW = '''_VOC_SORTABLE_FIELDS = {"id", "nome_ptbr", "pilar", "tipo"}
_PILARES_CONCEITUAIS = ("corpo", "sombra", "arcano", "espirito", "engenho")
_PILARES_VALIDOS = _PILARES_CONCEITUAIS + ("Fundida",)'''

# 2. Botoes de filtro na tela de vocacoes
FILTRO_OLD = '''                for opcao, label in [
                    ("todos", "Todos"),
                    ("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV"), ("V", "V"),
                    ("Fundida", "Fundida"),
                    ("anomalias", "⚠ Anomalias (14)"),
                ]:'''

FILTRO_NEW = '''                for opcao, label in [
                    ("todos", "Todos"),
                    ("corpo", "Corpo"),
                    ("sombra", "Sombra"),
                    ("arcano", "Arcano"),
                    ("espirito", "Espírito"),
                    ("engenho", "Engenho"),
                    ("Fundida", "Fundida"),
                    ("anomalias", "⚠ Anomalias"),
                ]:'''

# 3. Validacao de pilares romanos nos detalhes
DETALHE_OLD = '''    pilares_validos = ("I", "II", "III", "IV", "V", "Fundida")
    is_anomalia = data["pilar"] not in pilares_validos'''

DETALHE_NEW = '''    pilares_validos = ("corpo", "sombra", "arcano", "espirito", "engenho", "Fundida")
    is_anomalia = data["pilar"] not in pilares_validos'''

# 4. Pilar display label (detalhe)
LABEL_OLD = 'pilar_txt = f"⚠ Pilar: {data[\'pilar\']}" if is_anomalia else f"Pilar {data[\'pilar\']}"'
LABEL_NEW = 'pilar_txt = f"⚠ {data[\'pilar\']}" if is_anomalia else f"Pilar {data[\'pilar\']}"'


def main() -> int:
    c = MAIN.read_text(encoding="utf-8")
    antes = len(c)

    subs = [
        (CONST_OLD, CONST_NEW, "Constantes _PILARES_*"),
        (FILTRO_OLD, FILTRO_NEW, "Botoes de filtro na tela"),
        (DETALHE_OLD, DETALHE_NEW, "Validacao de pilares na detalhe"),
        (LABEL_OLD, LABEL_NEW, "Label de pilar no header"),
    ]

    aplicadas = 0
    for old, new, desc in subs:
        if old not in c:
            if new in c:
                print(f"  [IDEMPOTENTE] {desc}")
            else:
                print(f"  [AVISO] Nao encontrado: {desc}")
            continue
        c = c.replace(old, new, 1)
        aplicadas += 1
        print(f"  [OK] {desc}")

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