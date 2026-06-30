# Fiacao dos 32 sigilos: estende ELEMENTO_ESCOLA + FORMA_ESCOLA e corrige 2 cores.
# Le os forma_{slug}.svg byte-a-byte (sem transcrever SVG na mao). Asserts param tudo.
import io, sys

PARES = [
    ("Hemomancia","hemomancia"), ("Biomancia","biomancia"), ("Fitomancia","fitomancia"),
    ("Zoomancia","zoomancia"), ("Metamorfomancia","metamorfomancia"),
    ("Mnemomancia","mnemomancia"), ("Psicomancia","psicomancia"), ("Emociomancia","emociomancia"),
    ("Oniromancia","oniromancia"), ("Encantomancia","encantomancia"),
    ("Umbramancia","umbramancia"), ("Ilusionismo","ilusionismo"), ("Magia do Veu","magia-do-veu"),
    ("Cronomancia","cronomancia"), ("Fatomancia","fatomancia"), ("Gravitomancia","gravitomancia"),
    ("Dimensiomancia","dimensiomancia"), ("Entropiomancia","entropiomancia"),
    ("Teomancia","teomancia"), ("Sacromancia","sacromancia"), ("Pactomancia","pactomancia"),
    ("Magia Ancestral","magia-ancestral"), ("Necromancia","necromancia"), ("Divinomancia","divinomancia"),
    ("Nomomancia","nomomancia"), ("Runomancia","runomancia"), ("Artificiomancia","artificiomancia"),
    ("Combatomancia","combatomancia"), ("Aegimancia","aegimancia"),
    ("Magia Aberrante","magia-aberrante"), ("Magia Feerica","magia-feerica"), ("Magia Musical","magia-musical"),
]
assert len(PARES) == 32

# --- ler os 32 forma_ byte-a-byte ---
formas = {}
for key, slug in PARES:
    with io.open("forma_%s.svg" % slug, "r", encoding="utf-8") as fh:
        svg = fh.read().strip()
    assert svg.startswith("<svg") and svg.endswith("</svg>"), "forma_%s mal formado" % slug
    assert "'" not in svg, "forma_%s tem aspas simples!" % slug   # delimitador seguro
    formas[key] = svg

with io.open("oficina_app.py", "r", encoding="utf-8") as fh:
    src = fh.read()

# --- ELEMENTO_ESCOLA: inserir 32 pares antes do } de fechamento ---
anc_el = '    "Sonomancia": "trovao",\n}'
assert src.count(anc_el) == 1, "anchor ELEMENTO nao unico: %d" % src.count(anc_el)
add_el = "".join('    "%s": "%s",\n' % (k, s) for k, s in PARES)
src = src.replace(anc_el, '    "Sonomancia": "trovao",\n' + add_el + '}', 1)

# --- FORMA_ESCOLA: inserir 32 entradas inline antes do } -> # Marca da Sombra ---
anc_fo = "</svg>',\n}\n\n# Marca da Sombra"
assert src.count(anc_fo) == 1, "anchor FORMA nao unico: %d" % src.count(anc_fo)
add_fo = "".join('"%s": %s,\n' % (k, "'" + formas[k] + "'") for k, _ in PARES)
src = src.replace(anc_fo, "</svg>',\n" + add_fo + "}\n\n# Marca da Sombra", 1)

# --- PASSO 4: trocar as 2 cores (4 ocorrencias cada, todas Mente/Curso) ---
n1 = src.count("#9a82ad"); n2 = src.count("#4fa89c")
assert n1 == 4 and n2 == 4, "cor antiga inesperada: 9a82ad=%d 4fa89c=%d" % (n1, n2)
src = src.replace("#9a82ad", "#3a8c94").replace("#4fa89c", "#3f8c6e")

with io.open("oficina_app.py", "w", encoding="utf-8") as fh:
    fh.write(src)

print("OK: ELEMENTO +32, FORMA +32, cores trocadas (9a82ad->3a8c94, 4fa89c->3f8c6e)")
