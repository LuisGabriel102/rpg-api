# Recola as 4 strings novas em FORMA_ESCOLA (le os forma_ byte-a-byte).
# NAO mexe nas outras 38, NAO mexe em ELEMENTO_ESCOLA.
import io, re

PARES = [
    ("Magia Aberrante", "magia-aberrante"),
    ("Gravitomancia",   "gravitomancia"),
    ("Magia Ancestral", "magia-ancestral"),
    ("Umbramancia",     "umbramancia"),
]
src = io.open("oficina_app.py", "r", encoding="utf-8").read()

for key, slug in PARES:
    svg = io.open(f"forma_{slug}.svg", "r", encoding="utf-8").read().strip()
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert "'" not in svg, f"{slug}: aspas simples"
    # casa  "<key>": '<...>'  (valor entre aspas simples, sem aspas simples internas)
    pat = re.compile(r'("' + re.escape(key) + r'":\s*)\'[^\']*\'')
    n = len(pat.findall(src))
    assert n == 1, f"{key}: {n} ocorrencias (esperado 1)"
    src = pat.sub(lambda m: m.group(1) + "'" + svg + "'", src, count=1)

io.open("oficina_app.py", "w", encoding="utf-8").write(src)
print("4 strings recoladas em FORMA_ESCOLA.")
