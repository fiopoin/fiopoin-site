#!/usr/bin/env python3
"""Build fiopoin.com from content/*.json.

Usage: python3 tools/build.py            (builds the newest edition as the homepage)
Outputs: index.html, archive/<date>.html, archive/index.html, feed.xml,
         social/<date>.png, social/<date>-story.png, social/latest.png, social/<date>.txt
"""
import json, glob, os, html, textwrap
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
page = env.get_template("page.html.j2")

editions = sorted(glob.glob("content/*.json"))
if not editions:
    raise SystemExit("no content files")
data = [json.load(open(p)) for p in editions]
latest = data[-1]

os.makedirs("archive", exist_ok=True)
os.makedirs("social", exist_ok=True)

open("index.html", "w").write(page.render(d=latest, root="", archived=False))
for d in data:
    open(f"archive/{d['date']}.html", "w").write(page.render(d=d, root="../", archived=True))

# archive index
items = "\n".join(
    f'<li><a href="{d["date"]}.html">{html.escape(d["date_long"])}</a><br><span>{html.escape(d["hero"]["headline"])}</span></li>'
    for d in reversed(data))
arch = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Past editions | FIOPO Intelligence</title><link rel="icon" href="../fiopo-logo.png"><link rel="stylesheet" href="../assets/style.css"></head>
<body><header class="top"><div class="wrap"><a class="brand" href="../"><img src="../fiopo-logo.png" alt="FIOPO" width="160" height="32"><span>Intelligence</span></a>
<nav class="main"><a href="../">Today</a></nav></div></header>
<main><section class="block"><div class="wrap"><div class="shead"><h2>Past editions</h2><p>Every morning's brief, kept so you can check our calls against what happened.</p></div>
<ul class="archive-list">{items}</ul></div></section></main>
<footer><div class="wrap"><div class="fgrid"><img class="flogo" src="../fiopo-logo.png" alt="FIOPO"><div><p>FIOPO Intelligence, fiopoin.com. General information, not financial advice.</p></div></div></div></footer></body></html>"""
open("archive/index.html", "w").write(arch)

# RSS feed (latest 30) with the daily graphic attached for social automation tools
def rfc822(ds):
    return datetime.strptime(ds, "%Y-%m-%d").replace(hour=11).strftime("%a, %d %b %Y %H:%M:%S +0000")
entries = []
for d in reversed(data[-30:]):
    s = d.get("social", {})
    entries.append(f"""<item><title>{html.escape(d['hero']['headline'])}</title>
<link>https://fiopoin.com/archive/{d['date']}.html</link><guid>https://fiopoin.com/archive/{d['date']}.html</guid>
<pubDate>{rfc822(d['date'])}</pubDate><description>{html.escape(s.get('caption', d['hero']['dek']))}</description>
<enclosure url="https://fiopoin.com/social/{d['date']}.png" type="image/png" length="0"/></item>""")
feed = f"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
<title>FIOPO Intelligence</title><link>https://fiopoin.com/</link>
<description>What happened, what is happening, and what could happen next, connected to your money.</description>
{''.join(entries)}</channel></rss>"""
open("feed.xml", "w").write(feed)

# Daily social graphics
NAVY, INK, BLUE, GREEN, AMBER, WHITE, MUTE = (27,42,74), (15,26,49), (0,145,210), (140,198,63), (233,162,59), (255,255,255), (159,179,207)
F = lambda w, s: ImageFont.truetype(f"tools/fonts/Inter-{w}.otf", s)
logo = Image.open("fiopo-logo.png").convert("RGBA")

def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines

def card(d, W, H, path):
    s = d["social"]
    im = Image.new("RGB", (W, H), NAVY)
    dr = ImageDraw.Draw(im)
    M = 80
    lg = logo.resize((300, int(300 * logo.height / logo.width)), Image.LANCZOS)
    im.paste(lg, (M, M), lg)
    dr.text((M + 318, M + 12), "Intelligence", font=F("Regular", 34), fill=MUTE)
    y = M + 150
    dr.text((M, y), s["kicker"], font=F("SemiBold", 34), fill=GREEN)
    y += 70
    hf = F("ExtraBold", 84 if H > W * 1.5 else 72)
    for line in wrap(dr, s["headline"], hf, W - 2 * M):
        dr.text((M, y), line, font=hf, fill=WHITE); y += int(hf.size * 1.12)
    y += 50
    # ripple bar
    dr.rectangle((M, y, W - M, y + 8), fill=BLUE)
    dr.rectangle((M, y, M + (W - 2 * M) // 3, y + 8), fill=AMBER)
    dr.rectangle((W - M - (W - 2 * M) // 3, y, W - M, y + 8), fill=GREEN)
    y += 60
    pf = F("Bold", 44)
    for p in s["points"]:
        dr.ellipse((M, y + 14, M + 20, y + 34), fill=GREEN)
        for i, line in enumerate(wrap(dr, p, pf, W - 2 * M - 50)):
            dr.text((M + 50, y), line, font=pf, fill=WHITE); y += 58
        y += 22
    # the ripple chain: how the story reaches you
    chain = d["hero"].get("chain", [])
    foot_top = H - M - 110
    row = 92 if H > W * 1.5 else 60
    tall = H > W * 1.5
    if chain and y + (86 if tall else 30) + row * (len(chain) - 1) + 44 < foot_top + 40:
        y += 30 if tall else 0
        dr.text((M, y), "How it reaches you", font=F("SemiBold", 30), fill=MUTE); y += 56 if tall else 50
        cols = [AMBER, BLUE, BLUE, BLUE, GREEN]
        x0 = M + 22
        dr.line((x0, y + 22, x0, y + 22 + row * (len(chain) - 1)), fill=BLUE, width=4)
        for i, n in enumerate(chain):
            c = cols[min(i, 4)] if i < len(chain) - 1 else GREEN
            dr.ellipse((x0 - 22, y, x0 + 22, y + 44), fill=NAVY, outline=c, width=5)
            if i == len(chain) - 1:
                dr.ellipse((x0 - 22, y, x0 + 22, y + 44), fill=GREEN)
            dr.text((M + 70, y - 2), n["label"], font=F("Regular", 26), fill=MUTE)
            dr.text((M + 70 + dr.textlength(n["label"], font=F("Regular", 26)) + 18, y - 8), n["value"], font=F("Bold", 36), fill=WHITE)
            y += row
    dr.line((M, H - M - 96, W - M, H - M - 96), fill=(58, 78, 117), width=2)
    dr.text((M, H - M - 70), d["date_long"], font=F("Regular", 28), fill=MUTE)
    dr.text((M, H - M - 30), "What it means for you: fiopoin.com", font=F("SemiBold", 36), fill=GREEN)
    im.save(path, optimize=True)

for d in data:
    if "social" not in d:
        continue
    p = f"social/{d['date']}.png"
    if d is latest or not os.path.exists(p):
        card(d, 1080, 1350, p)
        card(d, 1080, 1920, f"social/{d['date']}-story.png")
        open(f"social/{d['date']}.txt", "w").write(d["social"]["caption"] + "\n")
Image.open(f"social/{latest['date']}.png").save("social/latest.png")
open("social/latest.txt", "w").write(latest["social"]["caption"] + "\n")
print("built", latest["date"], "editions:", len(data))
