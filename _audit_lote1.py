# Audita os 4 forma_ a 40px: renderiza (cairosvg), mede bbox/cobertura (PIL),
# e monta um contact sheet PNG (40px real + zoom 6x lado a lado).
import io, cairosvg
from PIL import Image

SLUGS = ["magia-aberrante", "gravitomancia", "magia-ancestral", "umbramancia"]
ZOOM = 6
BG = (16, 14, 12)  # fundo escuro tipo hub, p/ ver formas claras e escuras

def render(slug, px):
    svg = io.open(f"forma_{slug}.svg", "rb").read()
    png = cairosvg.svg2png(bytestring=svg, output_width=px, output_height=px)
    return Image.open(io.BytesIO(png)).convert("RGBA")

def medir(img40):
    # bbox da tinta (alpha>20); cobertura = area bbox / area caixa, + fracao de pixels pintados
    px = img40.load(); W, H = img40.size
    xs = []; ys = []; pint = 0
    for y in range(H):
        for x in range(W):
            if px[x, y][3] > 20:
                xs.append(x); ys.append(y); pint += 1
    if not xs:
        return 0, 0, 0, 0
    bw = (max(xs) - min(xs) + 1) / W
    bh = (max(ys) - min(ys) + 1) / H
    cob_bbox = bw * bh
    frac_ink = pint / (W * H)
    return bw, bh, cob_bbox, frac_ink

print("=== §8 cobertura a 40px (bbox W%, H%, bbox-area%, tinta%) ===")
for s in SLUGS:
    bw, bh, cob, ink = medir(render(s, 40))
    flag = "OK" if (bw >= 0.6 or bh >= 0.6) else "BAIXO"
    print(f"{s:18s} W={bw*100:4.0f}% H={bh*100:4.0f}% bbox={cob*100:4.0f}% tinta={ink*100:4.0f}%  [{flag}]")

# contact sheet: por escola, 40px real (com moldura) + zoom 6x
pad = 14; cell = 40 + ZOOM * 40 + pad * 3
sheet = Image.new("RGBA", (cell * 2, cell * 2), BG + (255,))
for i, s in enumerate(SLUGS):
    col = i % 2; row = i // 2
    ox = col * cell + pad; oy = row * cell + pad
    real = render(s, 40); zoom = render(s, ZOOM * 40)
    sheet.alpha_composite(real, (ox, oy + (ZOOM*40 - 40)//2))
    sheet.alpha_composite(zoom, (ox + 40 + pad, oy))
out = "_contact_lote1.png"
sheet.convert("RGB").save(out)
print(f"\ncontact sheet: {out}  ({sheet.size[0]}x{sheet.size[1]})")
