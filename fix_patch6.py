"""fix_patch6.py - Corrige REP_6_OLD/NEW bugados em patch_main_etapa4.py.

O bug: usei \u0027 literal (6 chars) em vez de apostrofe real.
O fix: usa triple-quoted strings pra ter apostrofe literal sem escape.
"""
from pathlib import Path
import sys

p = Path("patch_main_etapa4.py")
if not p.exists():
    print("[ERRO] patch_main_etapa4.py nao encontrado.")
    sys.exit(1)

c = p.read_text(encoding="utf-8")

APO = chr(39)  # apostrofe

# Linhas bugadas (como estao escritas no arquivo patch atual)
BUG_LINE_OLD = 'REP_6_OLD = "ui.label(f\\"Medias {e[\\\\u0027pct_2\\\\u0027]}%\\").classes("'
BUG_LINE_NEW = 'REP_6_NEW = "ui.label(f\\"Médias {e[\\\\u0027pct_2\\\\u0027]}%\\").classes("'

# Linhas corrigidas (usam triple-quoted pra apostrofe literal)
FIX_LINE_OLD = f'REP_6_OLD = """ui.label(f"Medias {{e[{APO}pct_2{APO}]}}%").classes("""'
FIX_LINE_NEW = f'REP_6_NEW = """ui.label(f"Médias {{e[{APO}pct_2{APO}]}}%").classes("""'

if BUG_LINE_OLD not in c:
    print("[ERRO] Nao achou a linha bugada OLD no arquivo.")
    print(f"  Procurava: {BUG_LINE_OLD[:70]}...")
    sys.exit(2)

if BUG_LINE_NEW not in c:
    print("[ERRO] Nao achou a linha bugada NEW no arquivo.")
    sys.exit(3)

c = c.replace(BUG_LINE_OLD, FIX_LINE_OLD)
c = c.replace(BUG_LINE_NEW, FIX_LINE_NEW)

p.write_text(c, encoding="utf-8")
print("[OK] patch_main_etapa4.py corrigido.")
print(f"     REP_6_OLD agora: {FIX_LINE_OLD}")
print(f"     REP_6_NEW agora: {FIX_LINE_NEW}")