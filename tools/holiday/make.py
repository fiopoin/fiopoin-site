"""Holiday greeting graphics for the four sister publications, one distinct layout per brand.
Usage: python3 make.py <out_dir> <spec.json>
"""
import json, math, os, random, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(os.environ.get("HOLIDAY_ROOT", "/home/claude"))


def wheat(x, y, h, ang, col, rnd):
    """One wheat stalk rooted at (x,y), height h, leaning ang degrees."""
    g = [f'<g transform="translate({x},{y}) rotate({ang})">',
         f'<path d="M0 0 Q {rnd.uniform(-8,8):.1f} {-h*0.5:.1f} 0 {-h:.1f}" stroke="{col}" stroke-width="4" fill="none" stroke-linecap="round"/>']
    n = 9
    for i in range(n):
        t = h * (0.55 + 0.45 * i / n)
        s = 1 - i / (n * 1.6)
        for side in (-1, 1):
            g.append(f'<ellipse cx="{side*9*s:.1f}" cy="{-t:.1f}" rx="{6*s:.1f}" ry="{15*s:.1f}" fill="{col}" transform="rotate({side*28} {side*9*s:.1f} {-t:.1f})"/>')
    g.append(f'<ellipse cx="0" cy="{-h-12:.1f}" rx="5" ry="13" fill="{col}"/>')
    for side in (-1, 1):
        g.append(f'<path d="M0 {-h*0.3:.1f} q {side*40} {-30} {side*62} {-90}" stroke="{col}" stroke-width="3" fill="none" opacity=".75"/>')
    g.append('</g>')
    return ''.join(g)


def leaf(x, y, s, ang, col):
    return (f'<g transform="translate({x},{y}) rotate({ang}) scale({s})">'
            f'<path d="M0 -40 C 26 -26 28 10 0 40 C -28 10 -26 -26 0 -40 Z" fill="{col}"/>'
            f'<path d="M0 -36 L0 52" stroke="rgba(0,0,0,.25)" stroke-width="2.5"/>'
            f'<path d="M0 -8 L13 -20 M0 8 L15 -4 M0 -8 L-13 -20 M0 8 L-15 -4" stroke="rgba(0,0,0,.2)" stroke-width="2"/></g>')


def star(x, y, r, col, op=1.0):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append(f"{x + rr*math.cos(a):.1f},{y - rr*math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{col}" opacity="{op}"/>'


def burst(x, y, r, col, rnd):
    g = []
    for i in range(16):
        a = i * math.pi / 8
        g.append(f'<line x1="{x + r*0.25*math.cos(a):.1f}" y1="{y + r*0.25*math.sin(a):.1f}" x2="{x + r*math.cos(a):.1f}" y2="{y + r*math.sin(a):.1f}" stroke="{col}" stroke-width="5" stroke-linecap="round"/>')
        g.append(f'<circle cx="{x + r*1.12*math.cos(a):.1f}" cy="{y + r*1.12*math.sin(a):.1f}" r="5" fill="{col}"/>')
    return ''.join(g)


def flake(x, y, r, col):
    g = []
    for i in range(6):
        a = i * math.pi / 3
        ex, ey = x + r*math.cos(a), y + r*math.sin(a)
        g.append(f'<line x1="{x}" y1="{y}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{col}" stroke-width="4" stroke-linecap="round"/>')
        for t in (0.55,):
            mx, my = x + r*t*math.cos(a), y + r*t*math.sin(a)
            for d in (-0.6, 0.6):
                g.append(f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx + r*0.3*math.cos(a+d):.1f}" y2="{my + r*0.3*math.sin(a+d):.1f}" stroke="{col}" stroke-width="3.5" stroke-linecap="round"/>')
    return ''.join(g)


def branch(x, y, ln, ang, col):
    g = [f'<g transform="translate({x},{y}) rotate({ang})"><line x1="0" y1="0" x2="0" y2="{-ln}" stroke="#6b4a2b" stroke-width="5"/>']
    for i in range(14):
        t = -ln * (0.1 + 0.9 * i / 14)
        for side in (-1, 1):
            g.append(f'<line x1="0" y1="{t:.1f}" x2="{side*34*(1-i/20):.1f}" y2="{t-26:.1f}" stroke="{col}" stroke-width="6" stroke-linecap="round"/>')
    g.append('</g>')
    return ''.join(g)


def lantern(x, y, s, col):
    return (f'<g transform="translate({x},{y}) scale({s})"><line x1="0" y1="-160" x2="0" y2="-52" stroke="#C9A227" stroke-width="3"/>'
            f'<rect x="-22" y="-56" width="44" height="10" rx="3" fill="#C9A227"/>'
            f'<ellipse cx="0" cy="0" rx="52" ry="48" fill="{col}"/>'
            f'<path d="M-26 -42 Q -40 0 -26 42 M0 -48 L0 48 M26 -42 Q 40 0 26 42" stroke="rgba(0,0,0,.18)" stroke-width="3" fill="none"/>'
            f'<rect x="-22" y="44" width="44" height="10" rx="3" fill="#C9A227"/>'
            f'<line x1="0" y1="54" x2="0" y2="92" stroke="#C9A227" stroke-width="4"/></g>')


def lamp(x, y, s, col):
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<circle cx="0" cy="-44" r="46" fill="{col}" opacity=".18"/>'
            f'<path d="M0 -78 C 16 -54 14 -34 0 -26 C -14 -34 -16 -54 0 -78 Z" fill="#F7C548"/>'
            f'<path d="M0 -66 C 7 -52 6 -40 0 -34 C -6 -40 -7 -52 0 -66 Z" fill="#fff3c4"/>'
            f'<path d="M-46 -22 Q 0 34 46 -22 Z" fill="#C8553D"/><path d="M-46 -22 L46 -22" stroke="#E9A23B" stroke-width="5"/></g>')


def bloom(x, y, r, col):
    g = [f'<g transform="translate({x},{y})">']
    for i in range(5):
        a = i * 72
        g.append(f'<ellipse cx="0" cy="{-r*0.55:.1f}" rx="{r*0.36:.1f}" ry="{r*0.55:.1f}" fill="{col}" transform="rotate({a})"/>')
    g.append(f'<circle r="{r*0.24:.1f}" fill="#F7C548"/></g>')
    return ''.join(g)


def drop(x, y, s, col):
    return (f'<g transform="translate({x},{y}) scale({s})"><path d="M0 -60 C 26 -24 40 0 40 20 A 40 40 0 0 1 -40 20 C -40 0 -26 -24 0 -60 Z" fill="{col}"/>'
            f'<path d="M-18 14 A 20 20 0 0 0 -4 38" stroke="rgba(255,255,255,.6)" stroke-width="6" fill="none" stroke-linecap="round"/></g>')




def kite(x, y, s, col, col2, ang):
    return (f'<g transform="translate({x},{y}) rotate({ang}) scale({s})">'
            f'<path d="M0 -70 L48 0 L0 70 L-48 0 Z" fill="{col}"/><path d="M0 -70 L0 70 M-48 0 L48 0" stroke="{col2}" stroke-width="4"/>'
            f'<path d="M0 70 q 14 40 -6 80 q -18 40 8 90" stroke="{col2}" stroke-width="3" fill="none"/></g>')


def marigold(x, y, r):
    g = [f'<g transform="translate({x},{y})">']
    for ring, (rr, c) in enumerate([(1.0, '#E07B12'), (0.72, '#F29B1D'), (0.45, '#F7B733')]):
        for i in range(12):
            a = i * 30 + ring * 15
            g.append(f'<ellipse cx="0" cy="{-r*rr*0.62:.1f}" rx="{r*rr*0.28:.1f}" ry="{r*rr*0.42:.1f}" fill="{c}" transform="rotate({a})"/>')
    g.append('</g>')
    return ''.join(g)


def motif(name, box, b, rnd, dark):
    """Draw a holiday motif inside box (x, y, w, h)."""
    x0, y0, w, h = box
    cx, cy = x0 + w / 2, y0 + h / 2
    gold = '#D9A441' if dark else '#C08A2B'
    P = []
    R = lambda a, c: rnd.uniform(a, c)
    if name == 'harvest':
        n = 9
        for i in range(n):
            P.append(wheat(cx + (i - n // 2) * w * 0.045, y0 + h, h * R(0.62, 0.82), (i - n // 2) * 7 + R(-3, 3), gold, rnd))
        cols = [b['accent'], '#C8553D', '#B5651D', b['c2'], '#D98E04', '#A44A1F']
        for i in range(7):
            P.append(leaf(x0 + w * R(0.05, 0.95), y0 + h * R(0.02, 0.42), R(0.55, 0.95), R(-80, 80), cols[i % 6]))
    elif name == 'fireworks':
        cols = [b['accent'], b['c2'], b['c3'], gold]
        for i, (fx, fy, r) in enumerate([(0.5, 0.45, 0.24), (0.2, 0.3, 0.13), (0.82, 0.25, 0.14), (0.75, 0.75, 0.11), (0.22, 0.75, 0.1)]):
            P.append(burst(x0 + w * fx, y0 + h * fy, min(w, h) * r, cols[i % 4], rnd))
        for _ in range(14):
            P.append(star(x0 + w * R(0, 1), y0 + h * R(0, 1), R(5, 10), gold, 0.8))
    elif name == 'snow':
        green = '#2F6B4F' if dark else '#3C7A57'
        for i in range(3):
            P.append(branch(cx + (i - 1) * w * 0.18, y0 + h, h * (0.75 - abs(i - 1) * 0.15), (i - 1) * 24, green))
        for _ in range(9):
            P.append(flake(x0 + w * R(0.05, 0.95), y0 + h * R(0.05, 0.6), R(14, 28), '#ffffff' if dark else '#8fb0c6'))
        for _ in range(8):
            P.append(f'<circle cx="{cx + R(-w*0.3, w*0.3):.0f}" cy="{y0 + h*R(0.5, 0.95):.0f}" r="9" fill="{b["accent"]}"/>')
    elif name == 'lanterns':
        cols = ['#C8312C', '#D8442F', '#B8261F']
        for i, fx in enumerate([0.15, 0.38, 0.62, 0.85]):
            s = min(w, h) / 380 * (1.1 if i in (1, 2) else 0.85)
            P.append(lantern(x0 + w * fx, y0 + h * (0.45 if i in (1, 2) else 0.32) + 40, s, cols[i % 3]))
    elif name == 'crescent':
        r = min(w, h) * 0.32
        mid = f"m{rnd.randint(0, 99999)}"
        P.append(f'<mask id="{mid}"><rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#fff"/><circle cx="{cx + r*0.42:.0f}" cy="{cy - r*0.28:.0f}" r="{r*0.86:.0f}" fill="#000"/></mask>'
                 f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="{gold}" mask="url(#{mid})"/>')
        for _ in range(9):
            P.append(star(x0 + w * R(0.05, 0.95), y0 + h * R(0.05, 0.95), R(7, 14), gold, 0.9))
    elif name == 'lights':
        n = 5
        for i in range(n):
            P.append(lamp(x0 + w * (0.1 + 0.8 * i / (n - 1)), y0 + h * (0.82 if i % 2 else 0.72), min(w, h) / 260, gold))
        for _ in range(8):
            fx, fy = x0 + w * R(0.05, 0.95), y0 + h * R(0.05, 0.5)
            P.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="8" fill="#F7C548" opacity=".9"/><circle cx="{fx:.0f}" cy="{fy:.0f}" r="24" fill="#F7C548" opacity=".18"/>')
    elif name == 'blooms':
        cols = ['#E58FB0', '#B07CC6', b['accent'], '#F2C14E', '#E86A6A']
        for i in range(9):
            P.append(bloom(x0 + w * R(0.1, 0.9), y0 + h * R(0.15, 0.9), min(w, h) * R(0.07, 0.13), cols[i % 5]))
    elif name == 'drops':
        cols = [b['c3'], '#5FB8E6', '#2E9BE6', b['c2']]
        P.append(drop(cx, cy + h * 0.08, min(w, h) / 120 * 0.9, cols[0]))
        for i in range(6):
            P.append(drop(x0 + w * R(0.08, 0.92), y0 + h * R(0.1, 0.9), R(0.3, 0.6), cols[(i + 1) % 4]))
    elif name == 'earth':
        r = min(w, h) * 0.32
        P.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="#2E9BE6"/>'
                 f'<path d="M{cx - r*0.75:.0f} {cy - r*0.25:.0f} q {r*0.3:.0f} {-r*0.45:.0f} {r*0.6:.0f} {-r*0.2:.0f} q {r*0.2:.0f} {r*0.25:.0f} {-r*0.05:.0f} {r*0.45:.0f} q {-r*0.3:.0f} {r*0.15:.0f} {-r*0.55:.0f} {-r*0.25:.0f} z '
                 f'M{cx + r*0.1:.0f} {cy + r*0.2:.0f} q {r*0.4:.0f} {-r*0.2:.0f} {r*0.6:.0f} {r*0.1:.0f} q {-r*0.15:.0f} {r*0.4:.0f} {-r*0.45:.0f} {r*0.35:.0f} z" fill="#4F8F1F"/>')
        for i in range(6):
            P.append(leaf(x0 + w * R(0.05, 0.95), y0 + h * R(0.05, 0.95), R(0.5, 0.8), R(-80, 80), ['#4F8F1F', b['c2'], '#6FAF3F'][i % 3]))
    elif name == 'stars':
        for i in range(5):
            P.append(star(x0 + w * (0.1 + 0.2 * i), cy + (i % 2) * h * 0.12, min(w, h) * 0.08, gold if i % 2 else b['accent'], 0.95))
        for _ in range(10):
            P.append(star(x0 + w * R(0, 1), y0 + h * R(0, 1), R(5, 9), gold, 0.7))
    elif name == 'kites':
        cols = [('#E4572E', '#F7C548'), ('#2E9BE6', '#ffffff'), ('#8CC63F', '#1B2A4A'), ('#B07CC6', '#F7C548')]
        for i, (fx, fy) in enumerate([(0.22, 0.22), (0.6, 0.14), (0.84, 0.32), (0.4, 0.4)]):
            c1, c2 = cols[i]
            P.append(kite(x0 + w * fx, y0 + h * fy, min(w, h) / 520, c1, c2, R(-25, 25)))
        P.append(marigold(x0 + w * 0.1, y0 + h * 0.85, 24) + marigold(x0 + w * 0.9, y0 + h * 0.85, 22))
    elif name == 'tihar':
        n = 5
        for i in range(n):
            P.append(lamp(x0 + w * (0.1 + 0.8 * i / (n - 1)), y0 + h * 0.86, min(w, h) / 300, gold))
        for i in range(9):
            P.append(marigold(x0 + w * (0.06 + 0.88 * i / 8), y0 + h * (0.18 + 0.12 * math.sin(i / 8 * math.pi)), 22))
    return ''.join(P)


# ------------------------------------------------------------------ brands

BRANDS = {
 'fiopoin': dict(repo='fiopoin-site', url='fiopoin.com', ink='#ffffff', sub='#d5e2f3',
    accent='#E9A23B', c2='#8CC63F', c3='#0091D2', moonbg='#16325e',
    fonts=[('Head', 'tools/fonts/Inter-ExtraBold.otf'), ('Body', 'tools/fonts/Inter-Regular.otf'), ('Semi', 'tools/fonts/Inter-SemiBold.otf')]),
 'carbonenergynexus': dict(repo='carbonenergynexus-site', url='carbonenergynexus.com', ink='#1A2226', sub='#3d4a50',
    accent='#D0481E', c2='#F2C14E', c3='#1F7A8C', moonbg='#F4F6F5',
    fonts=[('Head', 'tools/fonts/SourceSerif4-Bold.ttf'), ('Body', 'tools/fonts/IBMPlexSans-Regular.ttf'), ('Semi', 'tools/fonts/IBMPlexSans-SemiBold.ttf')]),
 'uticamidstream': dict(repo='uticamidstream-site', url='uticamidstream.com', ink='#ffffff', sub='#c6d2df',
    accent='#F5B000', c2='#3E8ED0', c3='#2E8FD6', moonbg='#13263A',
    fonts=[('Head', 'tools/fonts/BarlowSemiCondensed-Bold.ttf'), ('Body', 'tools/fonts/IBMPlexSans-Regular.ttf'), ('Semi', 'tools/fonts/IBMPlexSans-SemiBold.ttf'), ('Mono', 'tools/fonts/IBMPlexMono-SemiBold.ttf')]),
 'watercapitalwire': dict(repo='watercapitalwire-site', url='watercapitalwire.com', ink='#ffffff', sub='#c9d6e4',
    accent='#E9A23B', c2='#8CC63F', c3='#2E9BE6', moonbg='#0d2036',
    fonts=[('Head', 'tools/fonts/newsreader-latin-700-normal.ttf'), ('Body', 'tools/fonts/archivo-latin-400-normal.ttf'), ('Semi', 'tools/fonts/archivo-latin-600-normal.ttf')]),
}


def svg(W, H, body):
    return f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="position:absolute;inset:0" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def hexagon(cx, cy, r, b):
    pts = [(cx + r * math.cos(math.radians(90 + 60 * i)), cy - r * math.sin(math.radians(90 + 60 * i))) for i in range(6)]
    cols = ['#F2C14E', '#E4572E', '#2B8A9E', '#F2C14E', '#E4572E', '#2B8A9E']
    g = [f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="#ffffff" stroke="#1A2226" stroke-width="10" stroke-linejoin="round"/>']
    for i in range(0, 6, 2):  # inner double bonds
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 6]
        k = 0.84
        ix1, iy1 = cx + (x1 - cx) * k, cy + (y1 - cy) * k
        ix2, iy2 = cx + (x2 - cx) * k, cy + (y2 - cy) * k
        t = 0.15
        g.append(f'<line x1="{ix1 + (ix2-ix1)*t:.1f}" y1="{iy1 + (iy2-iy1)*t:.1f}" x2="{ix2 - (ix2-ix1)*t:.1f}" y2="{iy2 - (iy2-iy1)*t:.1f}" stroke="#1A2226" stroke-width="7" stroke-linecap="round"/>')
    for i, (x, y) in enumerate(pts):
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="22" fill="{cols[i]}" stroke="#F4F6F5" stroke-width="6"/>')
    return ''.join(g)


def pipe_rack(W, y, b):
    # three pipes side by side as seen along the rack: crude, gas (raised), water
    g = [f'<rect x="0" y="{y + 30}" width="{W}" height="14" fill="#2a4766"/>']
    for x in range(60, W, 250):
        g.append(f'<rect x="{x}" y="{y + 44}" width="18" height="170" fill="#2a4766"/>')
    g.append(f'<rect x="0" y="{y - 104}" width="{W}" height="46" rx="23" fill="#F5B000"/>')
    g.append(f'<rect x="0" y="{y - 52}" width="{W}" height="40" rx="20" fill="#E9EEF3"/>')
    g.append(f'<rect x="0" y="{y - 8}" width="{W}" height="38" rx="19" fill="#2E8FD6"/>')
    for x in range(140, W, 250):  # pipe shoes and highlights
        g.append(f'<rect x="{x}" y="{y - 100}" width="10" height="38" fill="#d29600"/><rect x="{x}" y="{y - 48}" width="10" height="32" fill="#c3ccd6"/><rect x="{x}" y="{y - 4}" width="10" height="30" fill="#2272ad"/>')
    return ''.join(g)


def waves(W, y, H):
    def wave(yy, amp, col, ph, op):
        pts = [f'M0 {yy}']
        for x in range(0, W + 41, 40):
            pts.append(f'L{x} {yy + amp * math.sin(x / 140 + ph):.1f}')
        pts.append(f'L{W} {H} L0 {H} Z')
        return f'<path d="{" ".join(pts)}" fill="{col}" opacity="{op}"/>'
    return wave(y, 16, '#7A3CC2', 0.5, 0.85) + wave(y + 40, 20, '#2E9BE6', 2.0, 0.95) + wave(y + 90, 14, '#1F6FD1', 3.6, 1) + wave(y + 150, 12, '#123a63', 1.2, 1)


def page(key, W, H, headline, kicker, dateline, msg, mname='harvest'):
    b = BRANDS[key]
    R = 'file://' + str(ROOT / b['repo'])
    rnd = random.Random(sum(map(ord, key + mname)) + H)
    fonts = ''.join(f"@font-face{{font-family:{n};src:url('{R}/{p}')}}" for n, p in b['fonts'])
    story = H > 1500
    css = f"""{fonts}*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;position:relative;overflow:hidden;color:{b['ink']}}}
.abs{{position:absolute}} .k{{font:600 28px Semi;letter-spacing:5px;text-transform:uppercase;color:{b['accent']}}}
h1{{font-family:Head;font-weight:700}} p{{font-family:Body;color:{b['sub']}}}
.d{{font:400 27px Body;color:{b['sub']}}} .u{{font:600 34px Semi;margin-top:6px}}"""
    if key == 'fiopoin':
        # centered sunrise card: art on top in a glowing arc, text centered below
        top = 150 if not story else 230
        bh = int(H * (0.33 if not story else 0.38))
        box = (90, top, W - 180, bh)
        art = (f'<defs><radialGradient id="g" cx="50%" cy="100%" r="70%"><stop offset="0" stop-color="#E9A23B" stop-opacity=".35"/><stop offset="1" stop-color="#E9A23B" stop-opacity="0"/></radialGradient></defs>'
               f'<ellipse cx="{W/2}" cy="{top + bh}" rx="{W*0.55}" ry="{bh*0.9}" fill="url(#g)"/>'
               + ''.join(f'<circle cx="{W/2}" cy="{top + bh}" r="{bh*(0.75 + 0.28*i)}" fill="none" stroke="#{c}" stroke-opacity=".35" stroke-width="3"/>' for i, c in enumerate(['E9A23B', '0091D2', '8CC63F']))
               + f'<line x1="70" y1="{top + bh}" x2="{W-70}" y2="{top + bh}" stroke="#ffffff" stroke-opacity=".25" stroke-width="2"/>'
               + motif(mname, box, b, rnd, True))
        body = f"""<style>{css}
body{{background:linear-gradient(180deg,#0f4c8a 0%,#1B2A4A 55%,#141f38 100%)}}
.t{{position:absolute;left:80px;right:80px;top:{top + bh + 36}px;text-align:center;display:flex;flex-direction:column;align-items:center}}
h1{{font-weight:800;font-size:{104 if not story else 124}px;line-height:1;margin-top:16px;letter-spacing:-1px}}
p{{font-size:{34 if not story else 40}px;line-height:1.4;margin-top:26px;max-width:840px}}
.f{{position:absolute;left:80px;right:80px;bottom:{64 if not story else 110}px;display:flex;justify-content:space-between;align-items:flex-end}}
</style>{svg(W, H, art)}
<div class="abs" style="left:80px;top:{60 if not story else 110}px;display:flex;align-items:flex-end"><img src="{R}/brand/fiopo-white.svg" style="height:58px"><span style="font:600 42px Semi;margin-left:14px;border-bottom:4px solid #0091D2">Intelligence</span></div>
<div class="t"><div class="k">{kicker}</div><h1>{headline}</h1><p>{msg}</p></div>
<div class="f"><div><div class="d">{dateline}</div><div class="u">{b['url']}</div></div><img src="{R}/brand/fiopoin-logo-white.svg" style="height:44px"></div>"""
    elif key == 'carbonenergynexus':
        # light editorial page; art lives inside the benzene ring on the right
        hy = int(H * (0.555 if not story else 0.56))
        r = 228 if not story else 270
        cx = W - r - 40
        ring = hexagon(cx, hy + 40, r, b)
        box = (cx - r * 0.72, hy + 40 - r * 0.62, r * 1.44, r * 1.24)
        art = ring + motif(mname, box, b, rnd, False)
        body = f"""<style>{css}
body{{background:#F4F6F5}}
.t{{position:absolute;left:80px;right:80px;top:{200 if not story else 300}px}}
.bar{{width:150px;height:8px;margin-top:20px;background:linear-gradient(90deg,#F2C14E 0 33%,#E4572E 33% 66%,#2B8A9E 66%)}}
h1{{font-size:{118 if not story else 128}px;line-height:.98;margin-top:28px;color:#1A2226}}
p{{position:absolute;left:80px;width:{W - 2*r - 170}px;top:{hy - 60}px;font-size:{34 if not story else 38}px;line-height:1.42}}
.f{{position:absolute;left:80px;right:80px;bottom:{64 if not story else 110}px;border-top:2px solid #cfd8d6;padding-top:22px}}
.u{{color:#1F7A8C}}
</style>{svg(W, H, art)}
<div class="abs" style="left:52px;top:{38 if not story else 90}px"><img src="{R}/brand/cen-lockup-navy.svg" style="height:120px"></div>
<div class="t"><div class="k">{kicker}</div><div class="bar"></div><h1>{headline}</h1></div>
<p>{msg}</p>
<div class="f"><div class="d">{dateline}</div><div class="u">{b['url']}</div></div>"""
    elif key == 'uticamidstream':
        # industrial: amber band, condensed caps headline left, art right, pipe rack across the bottom
        py = int(H * (0.80 if not story else 0.80))
        box = (W * 0.52, H * (0.36 if not story else 0.40), W * 0.44, py - 110 - H * (0.36 if not story else 0.40))
        art = (f'<rect x="0" y="0" width="{W}" height="14" fill="#F5B000"/>' + pipe_rack(W, py, b) + motif(mname, box, b, rnd, True)
               + ''.join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#ffffff" stroke-opacity=".04" stroke-width="2"/>' for y in range(60, py - 120, 60)))
        body = f"""<style>{css}
body{{background:linear-gradient(170deg,#1C3550 0%,#13263A 70%)}}
.t{{position:absolute;left:80px;top:{190 if not story else 300}px;width:{W - 160}px}}
.k{{font-family:Mono;letter-spacing:3px}}
h1{{font-size:{124 if not story else 136}px;line-height:.92;text-transform:uppercase;margin-top:22px;letter-spacing:1px}}
p{{font-size:{33 if not story else 37}px;line-height:1.42;margin-top:34px;max-width:{W*0.44}px}}
.f{{position:absolute;left:80px;right:80px;bottom:{40 if not story else 90}px;display:flex;justify-content:space-between;align-items:flex-end}}
.d{{font-family:Mono;font-size:24px}}
</style>{svg(W, H, art)}
<div class="abs" style="left:66px;top:{56 if not story else 110}px"><img src="{R}/brand/um-lockup-dark.svg" style="height:84px"></div>
<div class="t"><div class="k">{kicker}</div><h1>{headline}</h1><p>{msg}</p></div>
<div class="f"><div class="d">{dateline}</div><div class="u">{b['url']}</div></div>"""
    else:
        # water: centered serif, art above, layered waves at the bottom carrying the footer
        wy = int(H * (0.80 if not story else 0.82))
        top = 160 if not story else 260
        bh = int(H * 0.26)
        box = (W * 0.18, top, W * 0.64, bh)
        art = (f'<rect x="0" y="0" width="{W/3}" height="10" fill="#2E9BE6"/><rect x="{W/3}" y="0" width="{W/3}" height="10" fill="#7A3CC2"/><rect x="{2*W/3}" y="0" width="{W/3}" height="10" fill="#8CC63F"/>'
               f'<circle cx="{W/2}" cy="{top + bh/2}" r="{bh*0.62}" fill="#2E9BE6" opacity=".10"/>'
               + motif(mname, box, b, rnd, True) + waves(W, wy, H))
        body = f"""<style>{css}
body{{background:linear-gradient(180deg,#0b1a2b 0%,#0d2036 100%)}}
.t{{position:absolute;left:70px;right:70px;top:{top + bh + 40}px;text-align:center;display:flex;flex-direction:column;align-items:center}}
h1{{font-size:{118 if not story else 128}px;line-height:1;margin-top:20px}}
p{{font-size:{34 if not story else 38}px;line-height:1.42;margin-top:28px;max-width:800px}}
.f{{position:absolute;left:0;right:0;bottom:{46 if not story else 96}px;text-align:center}}
.d{{color:#e6eef7}}
</style>{svg(W, H, art)}
<div class="abs" style="left:0;right:0;top:{52 if not story else 110}px;text-align:center"><img src="{R}/brand/wcw-lockup-white-1200.png" style="height:92px"></div>
<div class="t"><div class="k">{kicker}</div><h1>{headline}</h1><p>{msg}</p></div>
<div class="f"><div class="d">{dateline}</div><div class="u">{b['url']}</div></div>"""
    return f'<html><head></head><body>{body}</body></html>'


def main():
    """python3 make.py <out_dir> <spec.json>
    spec: {"slug", "headline", "kicker", "dateline", "motif", "messages": {brand: text}}"""
    out, spec = sys.argv[1:3]
    spec = json.loads(Path(spec).read_text())
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        for key, msg in spec['messages'].items():
            for W, H, suf in ((1080, 1350, ''), (1080, 1920, '-story')):
                pg = br.new_page(viewport={'width': W, 'height': H})
                f = out / f"{key}-{spec['slug']}{suf}.html"
                f.write_text(page(key, W, H, spec['headline'], spec['kicker'], spec['dateline'], msg, spec.get('motif', 'harvest')))
                pg.goto('file://' + str(f)); pg.wait_for_timeout(500)
                over = pg.evaluate("() => { const p=document.querySelector('p').getBoundingClientRect(); const f=document.querySelector('.f').getBoundingClientRect(); const h=document.querySelector('h1'); return [p.bottom > f.top - 10, h.scrollWidth > h.clientWidth + 2] }")
                if any(over):
                    print('WARNING layout overflow', key, suf or 'feed', over)
                pg.screenshot(path=str(out / f"{key}-{spec['slug']}{suf}.png"))
                pg.close()
        br.close()


if __name__ == '__main__':
    main()
