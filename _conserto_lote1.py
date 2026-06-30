# Conserto Lote 1: refaz a FORMA de 4 escolas. Autora cada desenho UMA vez (em
# 40-space) e o mapeia pro 600-space do brasao -> forma_ e grande leem identico.
# Cabeca (defs+selo+AURA) do grande fica byte-a-byte; so o miolo de corpoReact troca.
import io, re

K = 4.5  # fator forma(40) -> corpo grande(600), centro 20->300
def mk_map(big):
    if big:
        fx = lambda x: round(300 + (x - 20) * K, 1)
        fy = lambda y: round(300 + (y - 20) * K, 1)
        fs = lambda v: round(v * K, 2)
    else:
        fx = lambda x: round(x, 2); fy = lambda y: round(y, 2); fs = lambda v: round(v, 2)
    return fx, fy, fs

def diamond(cx, cy, r, fx, fy):
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    return " ".join(f"{fx(px)},{fy(py)}" for px, py in pts)

# ---- (1) MAGIA ABERRANTE: fenda continua vertical, vao preto, bordas oliva, 3 lascas ----
def corpo_aberrante(big):
    fx, fy, fs = mk_map(big)
    # fenda continua: estreita no topo/base, MAIS LARGA no meio; bordas assimetricas
    outer = [(20,4.5),(22.5,11),(24.2,18),(25.5,24),(22.8,30),(20,36),
             (17.5,30.5),(14.8,24),(16,18),(17.8,11)]
    inner = [(20,8.5),(21,12.5),(22,18),(22.5,24),(20.8,29),(20,32.5),
             (19,29),(17.2,24),(18,18),(19,12.5)]
    po = " ".join(f"{fx(x)},{fy(y)}" for x,y in outer)
    pi = " ".join(f"{fx(x)},{fy(y)}" for x,y in inner)
    s = f'<polygon points="{po}" fill="#7a8550"/>'
    s += f'<polygon points="{pi}" fill="#0c0f0a"/>'
    # 3 lascas dispersas, tamanhos diferentes, assimetricas
    for (cx,cy,r) in [(18.7,14,1.0),(21,21.5,1.8),(19.2,28,1.3)]:
        s += f'<polygon points="{diamond(cx,cy,r,fx,fy)}" fill="#c8d4a0"/>'
    return s

# ---- (2) GRAVITOMANCIA: esfera densa + 3 setas RETAS apontando pra dentro ----
def corpo_gravito(big):
    fx, fy, fs = mk_map(big)
    s = f'<circle cx="{fx(20)}" cy="{fy(27.5)}" r="{fs(6.8)}" fill="#387a60"/>'
    s += f'<circle cx="{fx(17.5)}" cy="{fy(25)}" r="{fs(2.2)}" fill="#50ad88" opacity="0.55"/>'
    # cada seta: haste + cabeca em V no ALVO (ponta apontando pra dentro)
    setas = [
        ((20,4.5),(20,18.5),(17.6,15.6),(22.4,15.6)),     # baixo
        ((6.5,8),(15.2,20.2),(12.3,19.4),(14.4,16.6)),    # diagonal sup-esq
        ((33.5,8),(24.8,20.2),(25.6,16.6),(27.7,19.4)),   # diagonal sup-dir
    ]
    s += f'<g fill="none" stroke="#387a60" stroke-width="{fs(1.7)}" stroke-linecap="round" stroke-linejoin="round">'
    for (a,t,b1,b2) in setas:
        s += (f'<path d="M {fx(a[0])} {fy(a[1])} L {fx(t[0])} {fy(t[1])} '
              f'M {fx(b1[0])} {fy(b1[1])} L {fx(t[0])} {fy(t[1])} L {fx(b2[0])} {fy(b2[1])}"/>')
    s += '</g>'
    return s

# ---- (3) MAGIA ANCESTRAL: corrente de 3 elos verticais, ocos, dourado, elo do meio gasto ----
def corpo_ancestral(big):
    fx, fy, fs = mk_map(big)
    rx, ry = 4.3, 6.0
    sw = fs(2.4)
    def elo(cx, cy):
        return (f'<ellipse cx="{fx(cx)}" cy="{fy(cy)}" rx="{fs(rx)}" ry="{fs(ry)}" '
                f'fill="none" stroke="#a3852f" stroke-width="{sw}"/>')
    s = elo(20, 11)
    # elo do meio com leve desgaste: oval aberto (gap pequeno na borda dir)
    cx, cy = 20, 20
    s += (f'<path d="M {fx(cx)} {fy(cy-ry)} '
          f'A {fs(rx)} {fs(ry)} 0 0 1 {fx(cx+rx)} {fy(cy+1.2)} '
          f'M {fx(cx-rx)} {fy(cy+0.4)} '
          f'A {fs(rx)} {fs(ry)} 0 0 1 {fx(cx)} {fy(cy-ry)} '
          f'M {fx(cx)} {fy(cy+ry)} '
          f'A {fs(rx)} {fs(ry)} 0 0 0 {fx(cx-rx)} {fy(cy-0.6)}" '
          f'fill="none" stroke="#a3852f" stroke-width="{sw}" stroke-linecap="round"/>')
    s += elo(20, 29)
    return s

# ---- (4) UMBRAMANCIA: disco-eclipse, metade luz / metade sombra, terminador curvo ----
def corpo_umbra(big):
    fx, fy, fs = mk_map(big)
    cx, cy, r = 20, 20, 11
    # massa de sombra (direita), limitada por terminador curvo bulindo pra esquerda
    s = (f'<path d="M {fx(cx)} {fy(cy-r)} '
         f'A {fs(r)} {fs(r)} 0 0 1 {fx(cx)} {fy(cy+r)} '
         f'Q {fx(15)} {fy(cy)} {fx(cx)} {fy(cy-r)} Z" fill="#2a2b40"/>')
    # rim do disco (indigo)
    s += f'<circle cx="{fx(cx)}" cy="{fy(cy)}" r="{fs(r)}" fill="none" stroke="#5a5c86" stroke-width="{fs(1.8)}"/>'
    # arco de luz (esquerda)
    s += (f'<path d="M {fx(cx)} {fy(cy-r)} A {fs(r)} {fs(r)} 0 0 0 {fx(cx)} {fy(cy+r)}" '
          f'fill="none" stroke="#8486ad" stroke-width="{fs(2.2)}"/>')
    # terminador sutil
    s += (f'<path d="M {fx(cx)} {fy(cy-r)} Q {fx(15)} {fy(cy)} {fx(cx)} {fy(cy+r)}" '
          f'fill="none" stroke="#8486ad" stroke-width="{fs(0.9)}" opacity="0.6"/>')
    return s

FORMAS = {
    "magia-aberrante": ("Magia Aberrante", corpo_aberrante),
    "gravitomancia":   ("Gravitomancia",   corpo_gravito),
    "magia-ancestral": ("Magia Ancestral", corpo_ancestral),
    "umbramancia":     ("Umbramancia",     corpo_umbra),
}

WRAP_A = ('<g transform="translate(300 300)"><g>'
          '<animateTransform attributeName="transform" type="scale" values="1 1;1.05 1;1 1" '
          'dur="3.5s" repeatCount="indefinite" calcMode="spline" '
          'keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>'
          '<g transform="translate(-300 -300)">')
WRAP_B = '</g></g>'

def escrever(slug, corpo_fn):
    # forma_ (40-space)
    inner40 = corpo_fn(big=False)
    forma = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
             f'width="40" height="40">{inner40}</svg>')
    assert "'" not in forma, f"{slug}: aspas simples no forma!"
    with io.open(f"forma_{slug}.svg", "w", encoding="utf-8") as fh:
        fh.write(forma)
    # grande: cabeca byte-a-byte + corpoReact novo
    with io.open(f"{slug}.svg", "r", encoding="utf-8") as fh:
        src = fh.read()
    marca = '<g id="corpoReact">'
    assert src.count(marca) == 1, f"{slug}: corpoReact nao unico"
    head = src[:src.index(marca)] + marca
    inner600 = corpo_fn(big=True)
    novo = head + WRAP_A + inner600 + WRAP_B + "</g></svg>"
    with io.open(f"{slug}.svg", "w", encoding="utf-8") as fh:
        fh.write(novo)
    return len(forma), len(novo)

for slug, (nome, fn) in FORMAS.items():
    lf, lg = escrever(slug, fn)
    print(f"OK {slug}: forma_={lf}B grande={lg}B")
print("8 arquivos regerados.")
