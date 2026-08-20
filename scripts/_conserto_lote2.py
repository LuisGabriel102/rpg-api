# Conserto Lote 2: refaz a FORMA de 6 escolas. Mesma maquina do Lote 1.
# Cor de dominio LIDA do #fl mid do proprio arquivo atual (preservar tom).
import io, re, math

K = 4.5
def mk_map(big):
    if big:
        return (lambda x: round(300+(x-20)*K,1), lambda y: round(300+(y-20)*K,1), lambda v: round(v*K,2))
    return (lambda x: round(x,2), lambda y: round(y,2), lambda v: round(v,2))

def dom_color(slug):
    src = io.open(f"{slug}.svg", encoding="utf-8").read()
    m = re.search(r'id="fl"[^>]*>\s*<stop offset="0"[^>]*/>\s*<stop offset="0.5" stop-color="(#[0-9a-fA-F]{6})"', src)
    assert m, f"{slug}: nao achei #fl mid"
    return m.group(1)

def diamond(cx, cy, r, fx, fy):
    return " ".join(f"{fx(a)},{fy(b)}" for a,b in [(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)])

# ---- (1) ABERRANTE: vidro trincado angular ----
def corpo_aberrante(big, C):
    fx,fy,fs = mk_map(big)
    P = lambda x,y: f"{fx(x)} {fy(y)}"
    main = f'<path d="M {P(18,5)} L {P(23,13)} L {P(15.5,19)} L {P(24,26)} L {P(18.5,33)} L {P(21,37)}" fill="none" stroke="{C}" stroke-width="{fs(2.7)}" stroke-linejoin="miter" stroke-linecap="round"/>'
    branch = (f'<path d="M {P(23,13)} L {P(29.5,10.5)} M {P(15.5,19)} L {P(8.5,22)} '
              f'M {P(15.5,19)} L {P(13,14)} M {P(24,26)} L {P(30,29.5)}" '
              f'fill="none" stroke="{C}" stroke-width="{fs(1.5)}" stroke-linejoin="miter" stroke-linecap="round"/>')
    sh = "".join(f'<polygon points="{diamond(cx,cy,r,fx,fy)}" fill="#c8d4a0"/>'
                 for cx,cy,r in [(26.5,17.5,1.3),(11.5,26,1.1),(20.5,9,0.9)])
    return main + branch + sh

# ---- (2) BIOMANCIA: celula em divisao (membrana + organelas) ----
def corpo_biomancia(big, C):
    fx,fy,fs = mk_map(big)
    P = lambda x,y: f"{fx(x)} {fy(y)}"
    mem = (f'<path d="M {P(20,7.5)} C {P(27,7.5)} {P(28,14)} {P(25.5,18)} '
           f'C {P(24.5,19.5)} {P(24.5,20.5)} {P(25.5,22)} '
           f'C {P(28,26)} {P(27,32.5)} {P(20,32.5)} '
           f'C {P(13,32.5)} {P(12,26)} {P(14.5,22)} '
           f'C {P(15.5,20.5)} {P(15.5,19.5)} {P(14.5,18)} '
           f'C {P(12,14)} {P(13,7.5)} {P(20,7.5)} Z" '
           f'fill="{C}" fill-opacity="0.15" stroke="{C}" stroke-width="{fs(1.8)}"/>')
    org = "".join(f'<circle cx="{fx(cx)}" cy="{fy(cy)}" r="{fs(r)}" fill="{C}"/>'
                  for cx,cy,r in [(18,13,2.2),(22.5,15,1.5),(19,27,2.6),(16.5,24,1.3)])
    return mem + org

# ---- (3) HEMOMANCIA: respingo (mancha pontuda + satelites) ----
def corpo_hemomancia(big, C):
    fx,fy,fs = mk_map(big)
    blob = [(19,11),(22,16),(27,15),(24,20),(28,24),(22,24.5),(20,30.5),(17,25),(11.5,27),(15,21),(10,18),(16,16)]
    pb = " ".join(f"{fx(x)},{fy(y)}" for x,y in blob)
    s = f'<polygon points="{pb}" fill="{C}"/>'
    s += "".join(f'<circle cx="{fx(cx)}" cy="{fy(cy)}" r="{fs(r)}" fill="{C}"/>'
                 for cx,cy,r in [(30,12,2.0),(31,26,1.4),(9,30,1.6),(26.5,32,1.1),(8,13,1.2)])
    return s

# ---- (4) METAMORFOMANCIA: duas metades (angular | curva) ----
def corpo_metamorfo(big, C):
    fx,fy,fs = mk_map(big)
    P = lambda x,y: f"{fx(x)} {fy(y)}"
    esq = f'<path d="M {P(20,6)} L {P(11,12)} L {P(14,20)} L {P(9,27)} L {P(20,34)} Z" fill="{C}"/>'
    dire = f'<path d="M {P(20,6)} C {P(28,8)} {P(31,16)} {P(26,21)} C {P(31,25)} {P(28,31)} {P(20,34)} Z" fill="{C}" fill-opacity="0.5"/>'
    div = f'<line x1="{fx(20)}" y1="{fy(6)}" x2="{fx(20)}" y2="{fy(34)}" stroke="{C}" stroke-width="{fs(1.3)}"/>'
    return esq + dire + div

# ---- (5) ZOOMANCIA: pegada (coxim + dedos em arco no topo) ----
def corpo_zoomancia(big, C):
    fx,fy,fs = mk_map(big)
    pad = f'<ellipse cx="{fx(20)}" cy="{fy(28)}" rx="{fs(7.8)}" ry="{fs(6.2)}" fill="{C}"/>'
    dedos = ""
    for cx,cy,rx,ry,rot in [(12,16.5,1.9,2.7,28),(17,12,2.0,2.9,8),(23,12,2.0,2.9,-8),(28,16.5,1.9,2.7,-28)]:
        dedos += (f'<ellipse cx="{fx(cx)}" cy="{fy(cy)}" rx="{fs(rx)}" ry="{fs(ry)}" '
                  f'fill="{C}" transform="rotate({rot} {fx(cx)} {fy(cy)})"/>')
    return pad + dedos

# ---- (6) ENCANTOMANCIA: espiral hipnotica (2.75 voltas pra dentro) ----
def corpo_encantomancia(big, C):
    fx,fy,fs = mk_map(big)
    R, N, voltas = 14.0, 90, 2.75
    pts = []
    for i in range(N+1):
        t = i/N
        ang = t*voltas*2*math.pi
        r = R*(1-t)
        pts.append((20+r*math.cos(ang), 20+r*math.sin(ang)))
    d = "M " + " L ".join(f"{fx(x)} {fy(y)}" for x,y in pts)
    return f'<path d="{d}" fill="none" stroke="{C}" stroke-width="{fs(2.0)}" stroke-linecap="round" stroke-linejoin="round"/>'

FORMAS = {
    "magia-aberrante": ("Magia Aberrante", corpo_aberrante),
    "biomancia":       ("Biomancia",       corpo_biomancia),
    "hemomancia":      ("Hemomancia",      corpo_hemomancia),
    "metamorfomancia": ("Metamorfomancia", corpo_metamorfo),
    "zoomancia":       ("Zoomancia",       corpo_zoomancia),
    "encantomancia":   ("Encantomancia",   corpo_encantomancia),
}

WRAP_A = ('<g transform="translate(300 300)"><g>'
          '<animateTransform attributeName="transform" type="scale" values="1 1;1.05 1;1 1" '
          'dur="3.5s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>'
          '<g transform="translate(-300 -300)">')
WRAP_B = '</g></g>'

for slug,(nome,fn) in FORMAS.items():
    C = dom_color(slug)
    inner40 = fn(False, C)
    forma = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">{inner40}</svg>'
    assert "'" not in forma, f"{slug}: aspas simples!"
    io.open(f"forma_{slug}.svg","w",encoding="utf-8").write(forma)
    src = io.open(f"{slug}.svg",encoding="utf-8").read()
    marca = '<g id="corpoReact">'
    assert src.count(marca)==1, f"{slug}: corpoReact nao unico"
    head = src[:src.index(marca)] + marca
    novo = head + WRAP_A + fn(True, C) + WRAP_B + "</g></svg>"
    io.open(f"{slug}.svg","w",encoding="utf-8").write(novo)
    print(f"OK {slug}: cor={C} forma_={len(forma)}B grande={len(novo)}B")
print("12 arquivos regerados.")
