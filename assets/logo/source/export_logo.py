"""Rainbow BIM – final logo export (clean vector outlines).

Each band is ONE closed contour made only of straight lines and circular arcs
(exact offsets of the centre-line). No clipPath, no mask, no strokes: the files
open the same way in browsers, Inkscape, Illustrator, Figma, cairosvg...

Colour version = "stacked" regions (outer band painted first, each next band
painted on top of it) so neighbouring colours never leave a hairline gap.
"""
import math, os

# writes into the parent folder (assets/logo/svg/...) when run from assets/logo/source/
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE = ["#E5383B", "#F3802B", "#F6C324", "#34B36B", "#2B8BD8", "#7A4FD0"]
SMALL_PALETTE = ["#E5383B", "#F6C324", "#2B8BD8"]          # 16 px version (3 bands)
DARK = "#1B1B1F"

def f(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

# ------------------------------------------------------------------ geometry
GEOM = dict(top=40, bottom=472, x_left=96, bowl_r=74, rb=62, leg_angle=66,
            loop_turn=-246, joint=4, width=78)   # width = total bundle width (6 x 13)

def chains(g=GEOM):
    """Return the two centre-line chains of the logo.
    A chain = dict(start=(x,y), h=heading, segs=[...], start_clip=?, end_clip=?)
    seg = ("L", length) or ("A", radius, turn_rad)   (turn > 0 = right/clockwise)."""
    H = g["width"] / 2
    corner = H + 12
    sx = g["x_left"] + H
    stem_edge = sx + H
    yt = g["top"] + H
    y_w = yt + 2 * g["bowl_r"]
    j = g["joint"]
    # --- leg / drop first (its size fixes the bowl width)
    th = math.radians(g["leg_angle"])
    rb = g["rb"]
    y_c = y_w + H + j
    cy = g["bottom"] - H - rb
    x0 = stem_edge + j + H / math.sin(th) + 4
    L = (cy - y_c + rb * math.cos(th)) / math.sin(th)
    cx = x0 + L * math.cos(th) + rb * math.sin(th)
    drop_right = cx + rb + H
    bar_len = drop_right - g["bowl_r"] - H - (sx + corner)
    xb = sx + corner + bar_len
    # chain 1 : stem -> top bar -> bowl -> waist bar ending flush against the stem (tee)
    c1 = dict(start=(sx, g["bottom"]), h=-math.pi / 2,
              segs=[("L", g["bottom"] - (yt + corner)), ("A", corner, math.pi / 2), ("L", bar_len),
                    ("A", g["bowl_r"], math.pi), ("L", xb - (stem_edge + j))],
              start_clip=None, end_clip=None)
    # chain 2 : leg (starts flush under the bar) -> drop loop -> return teeing into the leg
    n = (math.sin(th), -math.cos(th))
    k = H + j
    c2 = dict(start=(x0, y_c), h=th,
              segs=[("L", L), ("A", rb, math.radians(g["loop_turn"])), ("L", 400)],
              start_clip=((x0, y_c), (0.0, 1.0)),                      # line y = y_c
              end_clip=((x0 + k * n[0], y_c + k * n[1]), n))           # leg edge + joint
    bbox = (g["x_left"], g["top"], drop_right, g["bottom"])
    return [c1, c2], bbox

def offset_prims(chain, o):
    """Offset of a chain by o (o > 0 = left of travel). Returns primitives
    ("L", p0, p1) / ("A", p0, p1, r, large, sweep) with clipped start/end."""
    x, y = chain["start"]; h = chain["h"]
    prims = []
    for seg in chain["segs"]:
        nx, ny = math.sin(h), -math.cos(h)
        if seg[0] == "L":
            Lg = seg[1]
            p0 = (x + o * nx, y + o * ny)
            x, y = x + Lg * math.cos(h), y + Lg * math.sin(h)
            prims.append(["L", p0, (x + o * nx, y + o * ny)])
        else:
            r, t = seg[1], seg[2]
            s = 1 if t > 0 else -1
            ccx, ccy = x + s * r * -math.sin(h), y + s * r * math.cos(h)
            ro = r + o if t > 0 else r - o
            assert ro > 0, "offset larger than bend radius"
            p0 = (ccx - s * ro * -math.sin(h), ccy - s * ro * math.cos(h))
            h += t
            x, y = ccx - s * r * -math.sin(h), ccy - s * r * math.cos(h)
            p1 = (ccx - s * ro * -math.sin(h), ccy - s * ro * math.cos(h))
            prims.append(["A", p0, p1, ro, 1 if abs(t) > math.pi else 0, 1 if t > 0 else 0])
    # clip first / last straight primitive on its clip line
    def cut(p_on_line, d_line, c, m):
        # point P = p + s d with (P - c).m = 0
        s = ((c[0] - p_on_line[0]) * m[0] + (c[1] - p_on_line[1]) * m[1]) / (d_line[0] * m[0] + d_line[1] * m[1])
        return (p_on_line[0] + s * d_line[0], p_on_line[1] + s * d_line[1])
    if chain["start_clip"]:
        a, b = prims[0][1], prims[0][2]
        prims[0][1] = cut(a, (b[0] - a[0], b[1] - a[1]), *chain["start_clip"])
    if chain["end_clip"]:
        a, b = prims[-1][1], prims[-1][2]
        prims[-1][2] = cut(a, (b[0] - a[0], b[1] - a[1]), *chain["end_clip"])
    return prims

def region(chain, o_left, o_right):
    """Closed contour between two offsets (one SVG sub-path)."""
    A = offset_prims(chain, o_left)
    B = offset_prims(chain, o_right)
    d = [f"M{f(A[0][1][0])} {f(A[0][1][1])}"]
    for p in A:
        d.append(f"L{f(p[2][0])} {f(p[2][1])}" if p[0] == "L"
                 else f"A{f(p[3])} {f(p[3])} 0 {p[4]} {p[5]} {f(p[2][0])} {f(p[2][1])}")
    d.append(f"L{f(B[-1][2][0])} {f(B[-1][2][1])}")
    for p in reversed(B):
        d.append(f"L{f(p[1][0])} {f(p[1][1])}" if p[0] == "L"
                 else f"A{f(p[3])} {f(p[3])} 0 {p[4]} {1 - p[5]} {f(p[1][0])} {f(p[1][1])}")
    d.append("Z")
    return "".join(d)

def logo_svg(colors=PALETTE, mono=None, margin=24, opacity=None, bg=None, title="Rainbow BIM", g=None):
    cs, (x0, y0, x1, y1) = chains(g or GEOM)
    H = GEOM["width"] / 2
    n = len(colors)
    band = GEOM["width"] / n
    side = max(x1 - x0, y1 - y0) + 2 * margin
    vx, vy = (x0 + x1) / 2 - side / 2, (y0 + y1) / 2 - side / 2
    paths = []
    if mono:
        paths.append(f'<path fill="{mono}" d="{"".join(region(c, H, -H) for c in cs)}"/>')
    else:
        for i, col in enumerate(colors):   # stacked: band i covers from its outer edge to the inner edge
            paths.append(f'<path fill="{col}" d="{"".join(region(c, H - i * band, -H) for c in cs)}"/>')
    g_open = f'<g opacity="{opacity}">' if opacity is not None else "<g>"
    back = f'<rect x="{f(vx)}" y="{f(vy)}" width="{f(side)}" height="{f(side)}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(vx)} {f(vy)} {f(side)} {f(side)}" '
            f'width="512" height="512"><title>{title}</title>{back}{g_open}{"".join(paths)}</g></svg>\n')

if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "svg"), exist_ok=True)
    files = {
        "svg/rainbow-bim_couleur.svg": logo_svg(),
        "svg/rainbow-bim_noir.svg": logo_svg(mono=DARK),
        "svg/rainbow-bim_blanc.svg": logo_svg(mono="#FFFFFF"),
        "svg/rainbow-bim_couleur_16px.svg": logo_svg(SMALL_PALETTE, margin=12),
        "svg/rainbow-bim_filigrane.svg": logo_svg(opacity=0.12),
    }
    for name, s in files.items():
        open(os.path.join(OUT, name), "w").write(s)
    print("svg ok", {k: len(v) for k, v in files.items()})
