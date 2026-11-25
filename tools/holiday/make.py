"""Holiday greeting graphics for the four sister publications.
Usage: python3 make.py <out_dir> <slug> "<Headline>" "<kicker>" "<date line>" messages.json
messages.json maps brand key -> message text.
Renders <brand>-<slug>.png (1080x1350) and <brand>-<slug>-story.png (1080x1920).
"""
import json, math, random, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

import os
H = Path(os.environ.get('HOLIDAY_ROOT', '/home/claude'))

BRANDS = {
 'fiopoin': dict(repo='fiopoin-site', url='fiopoin.com',
    bg='linear-gradient(165deg,#22365e 0%,#1B2A4A 55%,#121d35 100%)', ink='#ffffff', sub='#c9d3e6',
    accent='#E9A23B', c2='#8CC63F', c3='#0091D2',
    head=('Inter', 'tools/fonts/Inter-ExtraBold.otf', 800), body=('InterR', 'tools/fonts/Inter-Regular.otf', 400),
    lock='<img src="{R}/brand/fiopo-white.svg" style="height:64px"><span style="font:600 46px InterS;color:#fff;margin-left:16px;border-bottom:4px solid #0091D2;padding-bottom:2px">Intelligence</span>',
    extra_font=('InterS', 'tools/fonts/Inter-SemiBold.otf', 600),
    foot='<img src="{R}/brand/fiopoin-logo-white.svg" style="height:46px">'),
 'carbonenergynexus': dict(repo='carbonenergynexus-site', url='carbonenergynexus.com',
    bg='linear-gradient(170deg,#F7F8F6 0%,#EEF1EF 100%)', ink='#1A2226', sub='#3d4a50',
    accent='#D0481E', c2='#F2C14E', c3='#1F7A8C',
    head=('SS4', 'tools/fonts/SourceSerif4-Bold.ttf', 700), body=('Plex', 'tools/fonts/IBMPlexSans-Regular.ttf', 400),
    lock='<img src="{R}/brand/cen-lockup-navy.svg" style="height:120px;margin:-24px 0 -24px -28px">',
    extra_font=('PlexS', 'tools/fonts/IBMPlexSans-SemiBold.ttf', 600),
    foot='<img src="{R}/brand/cen-mark.svg" style="height:78px">'),
 'uticamidstream': dict(repo='uticamidstream-site', url='uticamidstream.com',
    bg='linear-gradient(165deg,#1C3550 0%,#13263A 60%,#0d1b2a 100%)', ink='#ffffff', sub='#c6d2df',
    accent='#F5B000', c2='#3E8ED0', c3='#2E8FD6',
    head=('Barlow', 'tools/fonts/BarlowSemiCondensed-Bold.ttf', 700), body=('Plex', 'tools/fonts/IBMPlexSans-Regular.ttf', 400),
    lock='<img src="{R}/brand/um-lockup-dark.svg" style="height:84px">',
    extra_font=('PlexS', 'tools/fonts/IBMPlexSans-SemiBold.ttf', 600),
    foot='<img src="{R}/brand/um-mark-white.svg" style="height:60px">'),
 'watercapitalwire': dict(repo='watercapitalwire-site', url='watercapitalwire.com',
    bg='linear-gradient(165deg,#10263f 0%,#0b1a2b 60%,#07121f 100%)', ink='#ffffff', sub='#c3d0de',
    accent='#E9A23B', c2='#8CC63F', c3='#2E9BE6',
    head=('News', 'tools/fonts/newsreader-latin-700-normal.ttf', 700), body=('Arch', 'tools/fonts/archivo-latin-400-normal.ttf', 400),
    lock='<img src="{R}/brand/wcw-lockup-white-1200.png" style="height:96px">',
    extra_font=('ArchS', 'tools/fonts/archivo-latin-600-normal.ttf', 600),
    foot='<img src="{R}/brand/wcw-ring-white.svg" style="height:62px">'),
}


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


def art(b, W, Hh, seed, motif='harvest'):
    rnd = random.Random(seed)
    dark = b['ink'] == '#ffffff'
    gold = '#D9A441' if dark else '#C08A2B'
    parts = []
    corner = [(0.86, 0.06), (0.70, 0.09), (0.95, 0.19), (0.955, 0.33), (0.93, 0.47)]
    if motif == 'harvest':
        for i in range(9):
            x = W * 0.62 + i * 38 + rnd.uniform(-8, 8)
            parts.append(wheat(x, Hh + 20, rnd.uniform(Hh*0.2, Hh*0.29), -26 + i * 6 + rnd.uniform(-4, 4), gold, rnd))
        cols = [b['accent'], '#C8553D', '#B5651D', b['c2'], '#D98E04']
        for i, (fx, fy) in enumerate(corner):
            parts.append(leaf(W * fx, Hh * fy, rnd.uniform(0.6, 1.0), rnd.uniform(-70, 70), cols[i % len(cols)]))
    elif motif == 'fireworks':
        cols = [b['accent'], b['c2'], b['c3'], gold]
        for i, (fx, fy, r) in enumerate([(0.80, 0.80, 120), (0.62, 0.90, 70), (0.93, 0.66, 60), (0.88, 0.10, 54)]):
            parts.append(burst(W*fx, Hh*fy, r, cols[i % 4], rnd))
        for _ in range(14):
            parts.append(star(W*rnd.uniform(0.55, 0.98), Hh*rnd.uniform(0.55, 0.98), rnd.uniform(5, 11), gold, 0.8))
    elif motif == 'snow':
        green = '#2F6B4F' if dark else '#3C7A57'
        for i in range(3):
            parts.append(branch(W*0.80 + i*70, Hh + 30, Hh*0.30 - i*30, -28 + i*24, green))
        for fx, fy in [(0.58, 0.78), (0.70, 0.68), (0.92, 0.62)] + corner:
            parts.append(flake(W*fx, Hh*fy, rnd.uniform(18, 30), '#ffffff' if dark else '#9db7c9'))
        for _ in range(8):
            parts.append(f'<circle cx="{W*rnd.uniform(0.6,0.98):.0f}" cy="{Hh*rnd.uniform(0.75,0.98):.0f}" r="9" fill="{b["accent"]}"/>')
    elif motif == 'lanterns':
        cols = ['#C8312C', '#D8442F', '#B8261F']
        for i, (fx, fy, s) in enumerate([(0.88, 0.12, 0.9), (0.74, 0.08, 0.7), (0.80, 0.80, 1.1), (0.64, 0.88, 0.8), (0.94, 0.70, 0.75)]):
            parts.append(lantern(W*fx, Hh*fy, s, cols[i % 3]))
    elif motif == 'crescent':
        moon_bg = b['bg'].split('#')[-1][:6]
        cx, cy, r = W*0.82, Hh*0.80, 110
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{gold}"/><circle cx="{cx+44}" cy="{cy-30}" r="{r*0.88}" fill="#{moon_bg}"/>')
        for fx, fy, rr in [(0.64, 0.74, 14), (0.70, 0.90, 9), (0.95, 0.64, 10), (0.90, 0.95, 8)] + [(a, b2, 9) for a, b2 in corner]:
            parts.append(star(W*fx, Hh*fy, rr, gold, 0.9))
    elif motif == 'lights':
        for i in range(7):
            parts.append(lamp(W*(0.58 + i*0.065), Hh*0.94 - (i % 2)*24, 0.9, gold))
        for fx, fy in corner:
            parts.append(f'<circle cx="{W*fx:.0f}" cy="{Hh*fy:.0f}" r="10" fill="#F7C548" opacity=".85"/><circle cx="{W*fx:.0f}" cy="{Hh*fy:.0f}" r="26" fill="#F7C548" opacity=".18"/>')
    elif motif == 'blooms':
        cols = ['#E58FB0', '#B07CC6', b['accent'], '#F2C14E', '#E86A6A']
        for i, (fx, fy) in enumerate([(0.82, 0.84), (0.66, 0.92), (0.95, 0.74), (0.74, 0.74), (0.92, 0.94)] + corner):
            parts.append(bloom(W*fx, Hh*fy, rnd.uniform(36, 62), cols[i % 5]))
    elif motif == 'drops':
        cols = [b['c3'], '#5FB8E6', '#2E9BE6', b['c2']]
        for i, (fx, fy, s) in enumerate([(0.82, 0.80, 1.5), (0.66, 0.90, 0.9), (0.94, 0.66, 0.8)] + [(a, b2, 0.45) for a, b2 in corner]):
            parts.append(drop(W*fx, Hh*fy, s, cols[i % 4]))
    elif motif == 'earth':
        cols = [b['c2'], '#4F8F1F', '#6FAF3F', b['c3']]
        cx, cy = W*0.84, Hh*0.84
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="150" fill="{b["c3"]}" opacity=".9"/>'
                     f'<path d="M{cx-110} {cy-40} q 40 -60 90 -30 q 30 30 -10 60 q -40 20 -80 -30 z M{cx+20} {cy+30} q 60 -30 90 10 q -20 60 -70 50 z" fill="#4F8F1F"/>')
        for i, (fx, fy) in enumerate(corner):
            parts.append(leaf(W*fx, Hh*fy, rnd.uniform(0.6, 0.9), rnd.uniform(-70, 70), cols[i % 4]))
    elif motif == 'stars':
        for i in range(5):
            parts.append(star(W*(0.66 + i*0.07), Hh*(0.90 - (i % 2)*0.05), 30, gold if i % 2 else b['accent'], 0.95))
        for fx, fy in corner:
            parts.append(star(W*fx, Hh*fy, 12, gold, 0.8))
    return f'<svg width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" style="position:absolute;inset:0" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'


def page(key, W, Hh, headline, kicker, dateline, msg, motif='harvest'):
    b = BRANDS[key]
    R = 'file://' + str(H / b['repo'])
    fonts = ''.join(f"@font-face{{font-family:{n};src:url('{R}/{p}')}}" for n, p, _ in (b['head'], b['body'], b['extra_font']))
    story = Hh > 1500
    hs = 124 if not story else 128
    leaf_layer = art(b, W, Hh, sum(map(ord, key)) + Hh, motif)
    return f"""<html><head><style>{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{Hh}px;background:{b['bg']};position:relative;overflow:hidden;color:{b['ink']}}}
.c{{position:absolute;inset:0;padding:{120 if story else 76}px 80px;display:flex;flex-direction:column}}
.lock{{display:flex;align-items:flex-end}}
.k{{margin-top:{140 if story else 90}px;font:600 30px {b['extra_font'][0]};letter-spacing:5px;text-transform:uppercase;color:{b['accent']}}}
.bar{{width:120px;height:8px;margin-top:22px;background:linear-gradient(90deg,{b['accent']} 0 33%,{b['c2']} 33% 66%,{b['c3']} 66%)}}
h1{{margin-top:34px;font:{b['head'][2]} {hs}px/0.98 {b['head'][0]};letter-spacing:-1px;max-width:880px}}
p{{margin-top:44px;font:400 {42 if story else 38}px/1.38 {b['body'][0]};color:{b['sub']};max-width:{760 if story else 640}px}}
.f{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;position:relative;z-index:2}}
.d{{font:400 28px {b['body'][0]};color:{b['sub']}}}
.u{{font:600 34px {b['extra_font'][0]};margin-top:8px}}
</style></head><body>{leaf_layer}<div class="c">
<div class="lock">{b['lock'].format(R=R)}</div>
<div class="k">{kicker}</div><div class="bar"></div>
<h1>{headline}</h1><p>{msg}</p>
<div class="f"><div><div class="d">{dateline}</div><div class="u">{b['url']}</div></div></div>
</div></body></html>"""


def main():
    """python3 make.py <out_dir> <spec.json>
    spec: {"slug", "headline", "kicker", "dateline", "motif", "messages": {brand: text}}"""
    out, spec = sys.argv[1:3]
    spec = json.loads(Path(spec).read_text())
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        for key, msg in spec['messages'].items():
            for W, Hh, suf in ((1080, 1350, ''), (1080, 1920, '-story')):
                pg = br.new_page(viewport={'width': W, 'height': Hh})
                f = out / f"{key}-{spec['slug']}{suf}.html"
                f.write_text(page(key, W, Hh, spec['headline'], spec['kicker'], spec['dateline'], msg, spec.get('motif', 'harvest')))
                pg.goto('file://' + str(f)); pg.wait_for_timeout(400)
                pg.screenshot(path=str(out / f"{key}-{spec['slug']}{suf}.png"))
                pg.close()
        br.close()


if __name__ == '__main__':
    main()
