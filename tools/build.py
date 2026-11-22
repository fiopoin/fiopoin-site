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
import hashlib
CFG = json.load(open("site.json")) if os.path.exists("site.json") else {}
_ga = "https://www.googletagmanager.com https://*.google-analytics.com https://*.analytics.google.com" if CFG.get("ga_id") else ""
CSP = (f"default-src 'self'; script-src 'self' {('https://www.googletagmanager.com' if _ga else '')}; style-src 'self' 'unsafe-inline'; "
       f"img-src 'self' data: https://upload.wikimedia.org {_ga}; font-src 'self'; connect-src 'self' {_ga}; object-src 'none'; "
       "base-uri 'self'; form-action 'self'; upgrade-insecure-requests").replace("  ", " ").replace(" ;", ";")
V = hashlib.md5((open("assets/style.css").read() + open("assets/calc.js").read() + open("assets/ga.js").read()).encode()).hexdigest()[:8]


# FIOPO scorecard: every odds call labeled as FIOPO judgment, checked 30 days after it was made.
# Results are recorded in content/scorecard.json as {"YYYY-MM-DD|label": "hit" or "miss"}.
from datetime import timedelta
_results = json.load(open("content/scorecard.json")) if os.path.exists("content/scorecard.json") else {}
def _long(dt): return dt.strftime("%B %-d, %Y")
def score_for(asof):
    # One call per odds set: the outcome FIOPO rated most likely (a 20% call that does not happen is not a miss).
    # A call carried over unchanged (same label and pct) while its 30 day window is still open counts once,
    # under the date it was first made.
    calls = []
    for e in sorted(data, key=lambda x: x["date"]):
        if e["date"] > asof: continue
        made = datetime.strptime(e["date"], "%Y-%m-%d")
        for s in e.get("stories", []):
            c = s.get("could", {})
            note = c.get("note", "")
            if "FIOPO" not in note or "Not a FIOPO" in note or "Market odds" in note or not c.get("odds"): continue
            o = max(c["odds"], key=lambda x: x["pct"])
            if any(p["label"] == o["label"] and p["pct"] == o["pct"] and made < p["check_dt"] for p in calls): continue
            calls.append({"label": o["label"], "pct": o["pct"], "made": e["date"], "made_long": _long(made),
                          "check_dt": made + timedelta(days=30),
                          "check_long": _long(made + timedelta(days=30)), "res": _results.get(e["date"] + "|" + o["label"])})
    hit = sum(1 for c in calls if c["res"] == "hit"); miss = sum(1 for c in calls if c["res"] == "miss")
    open_calls = [c for c in calls if not c["res"]]
    return {"open": len(open_calls), "hit": hit, "miss": miss, "next": open_calls[-1] if open_calls else None}

os.makedirs("archive", exist_ok=True)
os.makedirs("social", exist_ok=True)

# Search and AI discovery: canonical URLs, publish times and schema.org structured data
from zoneinfo import ZoneInfo
SITE = "https://fiopoin.com/"
ORG = {"@type": "NewsMediaOrganization", "@id": SITE + "#org", "name": "FIOPO Intelligence",
       "alternateName": ["fiopoin", "fiopoin.com", "FIOPO"],
       "areaServed": "Worldwide",
       "url": SITE, "email": "hello@fiopoin.com", "publishingPrinciples": SITE + "about.html",
       "logo": {"@type": "ImageObject", "url": SITE + "brand/fiopoin-icon-512.png", "width": 512, "height": 512},
       "slogan": "Intelligence for prosperity",
       "sameAs": ["https://www.linkedin.com/company/fiopoin/", "https://x.com/fiopoinx", "https://www.instagram.com/fiopoin/", "https://www.facebook.com/profile.php?id=61596657421058"]}
def published(d):
    return datetime.strptime(d["date"] + " 05:12", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("America/Chicago")).isoformat()
def summary(d):
    """Edition-specific description: the first paragraph of the morning caption, without hashtags or the site plug."""
    t = d.get("social", {}).get("caption", "").split("\n")[0].strip() or d["hero"]["dek"]
    for tail in ("What it means for you at fiopoin.com", "More at fiopoin.com.", "More at fiopoin.com"):
        t = t.replace(tail, "").strip()
    if len(t) > 300:
        t = t[:300].rsplit(". ", 1)[0] + "."
    return t
def page_url(d, archived):
    return SITE + (f"archive/{d['date']}.html" if archived else "")
def ld_for(d, archived):
    url = page_url(d, archived)
    sections = [s.get("topic") for s in d.get("stories", []) if s.get("topic")]
    art = {"@type": "NewsArticle", "@id": url + "#article", "headline": d["hero"]["headline"][:110],
           "description": summary(d), "url": url, "mainEntityOfPage": url,
           "image": [SITE + f"social/{d['date']}.png"], "datePublished": published(d), "dateModified": published(d),
           "inLanguage": "en-US", "isAccessibleForFree": True, "articleSection": sections,
           "author": {"@id": SITE + "#org"}, "publisher": {"@id": SITE + "#org"}}
    graph = [ORG, art]
    if not archived:
        graph.append({"@type": "WebSite", "@id": SITE + "#site", "name": "FIOPO Intelligence", "alternateName": ["fiopoin", "fiopoin.com"], "url": SITE,
                      "publisher": {"@id": SITE + "#org"}, "inLanguage": "en-US"})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")

open("index.html", "w").write(page.render(d=latest, root="", archived=False, v=V, score=score_for(latest["date"]), cfg=CFG, csp=CSP,
                                          url=SITE, published=published(latest), desc=summary(latest), ld=ld_for(latest, False)))
for d in data:
    open(f"archive/{d['date']}.html", "w").write(page.render(d=d, root="../", archived=True, v=V, score=score_for(d["date"]), cfg=CFG, csp=CSP,
                                                            url=page_url(d, True), published=published(d), desc=summary(d), ld=ld_for(d, True)))

# archive index
items = "\n".join(
    f'<li><a href="{d["date"]}.html">{html.escape(d["date_long"])}</a><br><span>{html.escape(d["hero"]["headline"])}</span></li>'
    for d in reversed(data))
arch = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin">
<title>Past editions | FIOPO Intelligence</title><meta name="description" content="Every FIOPO Intelligence morning edition: what happened, what is happening, what could happen next, and what it means for your money."><link rel="canonical" href="https://fiopoin.com/archive/"><meta name="robots" content="index, follow"><link rel="icon" type="image/svg+xml" href="../brand/fiopoin-icon.svg"><link rel="stylesheet" href="../assets/style.css?v={V}"></head>
<body><header class="top"><div class="wrap"><a class="brand fi" href="../"><span class="fi-r"><img src="../brand/fiopo-white.svg" alt="FIOPO" width="106" height="44"><span class="fi-int">Intelligence</span></span></a>
<nav class="main"><a href="../">Today</a></nav></div></header>
<main><section class="block"><div class="wrap"><div class="shead"><h2>Past editions</h2><p>Every morning's brief, kept so you can check our calls against what happened.</p></div>
<ul class="archive-list">{items}</ul></div></section></main>
<footer><div class="wrap"><div class="fgrid"><a class="lockup" href="../"><img src="../brand/fiopoin-logo-white.svg" alt="fiopoin"></a><div><p>FIOPO Intelligence, fiopoin.com. General information, not financial advice. <a href="../about.html">About</a> <a href="../privacy.html">Privacy</a></p><p class="sister" style="margin-top:8px">Also from the FIOPO family: <a href="https://carbonenergynexus.com/">Carbon Energy Nexus</a> · <a href="https://uticamidstream.com/">Utica Midstream</a> · <a href="https://watercapitalwire.com/">Water Capital Wire</a></p></div></div></div></footer></body></html>"""
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

# privacy page
_ga_text = ("""<h3>Analytics</h3><p>We use Google Analytics 4 to count visits and understand which stories are useful. It records the pages you view, the site that sent you, your general location (city or region, not your address), and your device and browser type. Google Analytics uses cookies to tell new visitors from returning ones. We see totals and trends, not who you are, and we do not combine this with other data about you.</p>
<p>Google processes this data under its own policy: <a href="https://policies.google.com/technologies/partner-sites">how Google uses information from sites that use its services</a>. You can block Google Analytics on every site with Google's <a href="https://tools.google.com/dlpage/gaoptout">opt-out browser add-on</a>, or by blocking cookies in your browser. The site works the same either way.</p>"""
    if CFG.get("ga_id") else "<h3>Analytics</h3><p>We do not currently run analytics or tracking on this site. If we add visitor analytics, this page will say so first.</p>")
priv = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin">
<title>Privacy | FIOPO Intelligence</title><meta name="description" content="How FIOPO Intelligence (fiopoin.com) handles visitor data."><link rel="canonical" href="https://fiopoin.com/privacy.html"><link rel="icon" type="image/svg+xml" href="brand/fiopoin-icon.svg"><link rel="stylesheet" href="assets/style.css?v={V}"></head>
<body><header class="top"><div class="wrap"><a class="brand fi" href="./"><span class="fi-r"><img src="brand/fiopo-white.svg" alt="FIOPO" width="106" height="44"><span class="fi-int">Intelligence</span></span></a>
<nav class="main"><a href="./">Today</a><a href="archive/">Past editions</a></nav></div></header>
<main><section class="block"><div class="wrap" style="max-width:760px"><div class="shead"><h2>Privacy</h2><p>Last updated November 17, 2026.</p></div>
<p>FIOPO Intelligence (fiopoin.com) is free to read. You do not need an account, and we do not sell, rent or share personal information.</p>
{_ga_text}
<h3>Email</h3><p>If you write to us at <a href="mailto:hello@fiopoin.com">hello@fiopoin.com</a>, we use your message and address only to reply. Email signup is not open yet; when it opens, we will use your address only to send the brief, and every email will have a one click unsubscribe.</p>
<h3>Hosting</h3><p>The site is hosted on GitHub Pages, which keeps standard server logs, including IP addresses, for security. See <a href="https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages#data-collection">GitHub's note on data collection</a>.</p>
<h3>Questions</h3><p>Write to <a href="mailto:hello@fiopoin.com">hello@fiopoin.com</a> and we will answer.</p>
</div></section></main>
<footer><div class="wrap"><div class="fgrid"><a class="lockup" href="./"><img src="brand/fiopoin-logo-white.svg" alt="fiopoin"></a><div><p>FIOPO Intelligence. Intelligence for prosperity. fiopoin.com. General information, not financial advice.</p><p class="sister" style="margin-top:8px">Also from the FIOPO family: <a href="https://carbonenergynexus.com/">Carbon Energy Nexus</a> · <a href="https://uticamidstream.com/">Utica Midstream</a> · <a href="https://watercapitalwire.com/">Water Capital Wire</a></p></div></div></div></footer></body></html>"""
open("privacy.html", "w").write(priv.replace("<h3>", '<h3 style="margin:26px 0 8px">'))

# about page: tells readers and search engines who publishes fiopoin
about_ld = json.dumps({"@context": "https://schema.org", "@graph": [ORG, {"@type": "AboutPage", "@id": SITE + "about.html", "url": SITE + "about.html",
    "name": "About FIOPO Intelligence (fiopoin)", "about": {"@id": SITE + "#org"}, "inLanguage": "en-US"}]}).replace("</", "<\\/")
about = priv.split("<main>")[0].replace("<title>Privacy | FIOPO Intelligence</title>", "<title>About FIOPO Intelligence (fiopoin) | Daily markets, money and world brief</title>").replace(
    'content="How FIOPO Intelligence (fiopoin.com) handles visitor data."', 'content="FIOPO Intelligence, known online as fiopoin, is a free daily brief on markets, money and the world at fiopoin.com."').replace(
    'href="https://fiopoin.com/privacy.html"', 'href="https://fiopoin.com/about.html"').replace("</head>", f'<script type="application/ld+json">{about_ld}</script></head>')
about += """<main><section class="block"><div class="wrap" style="max-width:760px"><div class="shead"><h2>About FIOPO Intelligence</h2></div>
<p><strong>FIOPO Intelligence</strong>, known online as <strong>fiopoin</strong> (FIOPO + IN), is a free morning brief at fiopoin.com. Each edition connects what happened, what is happening and what could happen next in markets, energy, policy and the world to what it means for your money.</p>
<h3>Sister publications</h3><p><a href="https://carbonenergynexus.com/">Carbon Energy Nexus</a> covers carbon, energy, water and capital. <a href="https://uticamidstream.com/">Utica Midstream</a> covers oil and gas. <a href="https://watercapitalwire.com/">Water Capital Wire</a> is also part of the family.</p>
<h3>How we work</h3><p>Every fact is sourced, dated and linked. Outlooks and odds are labeled as our judgment, not fact. We stay politically neutral and write in plain language. Nothing here is personalized financial advice.</p>
<h3>Not to be confused with</h3><p>fiopoin and FIOPO Intelligence are not affiliated with any internet service provider, fiber optic company or cryptocurrency project with a similar name.</p>
<h3>Follow and contact</h3><p><a href="https://www.linkedin.com/company/fiopoin/">LinkedIn</a>, <a href="https://www.instagram.com/fiopoin/">Instagram @fiopoin</a>, <a href="https://www.facebook.com/profile.php?id=61596657421058">Facebook</a> and <a href="https://x.com/fiopoinx">X @fiopoinx</a>. Email <a href="mailto:hello@fiopoin.com">hello@fiopoin.com</a>.</p>
</div></section></main>""" + priv.split("</main>")[1]
open("about.html", "w").write(about.replace("<h3>", '<h3 style="margin:26px 0 8px">'))

# sitemap.xml, robots.txt and llms.txt so search engines and AI assistants can find and cite every edition
urls = [(SITE, latest["date"], "daily", "1.0"), (SITE + "archive/", latest["date"], "daily", "0.6")]
urls += [(page_url(d, True), d["date"], "monthly", "0.7") for d in reversed(data)]
urls.append((SITE + "privacy.html", "2026-11-17", "yearly", "0.2"))
urls.append((SITE + "about.html", "2026-11-19", "monthly", "0.6"))
open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(f"<url><loc>{u}</loc><lastmod>{m}</lastmod><changefreq>{c}</changefreq><priority>{p}</priority></url>" for u, m, c, p in urls)
    + "\n</urlset>\n")
bots = ["Googlebot", "Bingbot", "Applebot", "DuckDuckBot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot",
        "Claude-SearchBot", "Claude-User", "anthropic-ai", "PerplexityBot", "Perplexity-User", "Google-Extended",
        "Applebot-Extended", "meta-externalagent", "Meta-ExternalFetcher", "FacebookBot", "CCBot", "Amazonbot", "cohere-ai"]
open("robots.txt", "w").write("# FIOPO Intelligence welcomes search engines and AI assistants.\n"
    "# Quote and link freely; please credit FIOPO Intelligence and link to fiopoin.com.\n\n"
    + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
    + "User-agent: *\nAllow: /\n\nSitemap: https://fiopoin.com/sitemap.xml\n")
lines = ["# FIOPO Intelligence", "",
         "> A free daily news site from fiopoin.com. Every morning (Central Time) it explains what happened, what is happening and what could happen next in markets, energy, geopolitics, technology, sports and entertainment, and what each story means for ordinary people's money. Facts are sourced and dated; odds and outlooks are labeled as FIOPO judgment or market odds. General information, not financial advice.", "",
         "Please credit FIOPO Intelligence and link to the edition you cite. Contact: hello@fiopoin.com", "",
         "## Today's edition", f"- [{latest['hero']['headline']}]({SITE}): {latest['date_long']}. {summary(latest)}"]
for s in latest.get("stories", []):
    lines.append(f"- [{s.get('topic','Story')}: {s['headline']}]({SITE}#{s['id']})")
lines += ["", "## Archive and feeds", f"- [Past editions]({SITE}archive/): every edition, kept so readers can check FIOPO calls against what happened",
          f"- [RSS feed]({SITE}feed.xml)", f"- [Sitemap]({SITE}sitemap.xml)", "", "## Recent editions"]
lines += [f"- [{d['date_long']}: {d['hero']['headline']}]({page_url(d, True)})" for d in list(reversed(data))[:30]]
open("llms.txt", "w").write("\n".join(lines) + "\n")

# Daily social graphics: three distinct looks (Nov 22, 2026, Raj)
#   morning  = "Global markets": navy, market board (tape or social.stats) + the one big driver
#   midday   = "Business and deals": light paper, amber band, big number callout + numbered points
#   evening  = "World and economy": deep ink, globe linework, numbered list + "What to watch" box
NAVY, INK, BLUE, GREEN, AMBER, WHITE, MUTE = (27,42,74), (15,26,49), (0,145,210), (140,198,63), (233,162,59), (255,255,255), (159,179,207)
PAPER, RED = (246,242,234), (214,82,74)
F = lambda w, s: ImageFont.truetype(f"tools/fonts/Inter-{w}.otf", s)
logo = Image.open("brand/fiopo-intelligence-white-1000.png").convert("RGBA")
small = Image.open("brand/fiopoin-logo-white-900.png").convert("RGBA")

def navyize(img):
    # recolor white (and near white) pixels to navy for light backgrounds, keep brand colors
    px = img.copy(); data = px.load()
    for yy in range(px.height):
        for xx in range(px.width):
            r, g, b, a = data[xx, yy]
            if a and min(r, g, b) > 200:
                data[xx, yy] = (*NAVY, a)
    return px
logo_n, small_n = navyize(logo), navyize(small)

def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    # avoid a single orphan word on the last line
    if len(lines) > 1 and " " not in lines[-1]:
        prev = lines[-2].split()
        if len(prev) > 2:
            lines[-2], lines[-1] = " ".join(prev[:-1]), prev[-1] + " " + lines[-1]
    return lines

def fit(dr, text, w, maxs, mins, maxlines=3, weight="ExtraBold"):
    for sz in range(maxs, mins - 1, -4):
        f = F(weight, sz)
        ls = wrap(dr, text, f, w)
        if len(ls) <= maxlines:
            return f, ls
    return f, ls

def header(im, M, light=False):
    lg = logo_n if light else logo
    lg = lg.resize((520, int(520 * lg.height / lg.width)), Image.LANCZOS)
    im.paste(lg, (M, M - 10), lg)
    return M - 10 + lg.height

def footer(im, dr, d, W, H, M, light=False, cta="Full breakdown: fiopoin.com"):
    line = (200, 192, 176) if light else (58, 78, 117)
    dr.line((M, H - M - 96, W - M, H - M - 96), fill=line, width=2)
    dr.text((M, H - M - 70), d["date_long"], font=F("Regular", 28), fill=(110, 118, 135) if light else MUTE)
    dr.text((M, H - M - 30), cta, font=F("SemiBold", 34), fill=NAVY if light else GREEN)
    sm = (small_n if light else small)
    sm = sm.resize((180, int(180 * sm.height / sm.width)), Image.LANCZOS)
    im.paste(sm, (W - M - sm.width, H - M - sm.height + 4), sm)

def pill(dr, x, y, text, bg, fg, f):
    tw = dr.textlength(text, font=f)
    dr.rounded_rectangle((x, y, x + tw + 40, y + f.size + 24), radius=(f.size + 24) // 2, fill=bg)
    dr.text((x + 20, y + 10), text, font=f, fill=fg)
    return y + f.size + 24

def dir_col(s):
    return {"up": GREEN, "down": RED}.get(s.get("dir"), MUTE)

def arrow(dr, x, y, dirn, col, sz=18):
    if dirn == "up":
        dr.polygon([(x, y + sz), (x + sz, y + sz), (x + sz / 2, y)], fill=col)
    elif dirn == "down":
        dr.polygon([(x, y), (x + sz, y), (x + sz / 2, y + sz)], fill=col)
    else:
        dr.rectangle((x, y + sz / 2 - 3, x + sz, y + sz / 2 + 3), fill=col)

def card_morning(d, s, W, H, path, pad=0):
    tall = H > W * 1.5
    im = Image.new("RGB", (W, H), NAVY); dr = ImageDraw.Draw(im); M = 80
    y = header(im, M) + (70 if tall else 44) + pad
    y = pill(dr, M, y, s["kicker"].upper(), BLUE, WHITE, F("Bold", 28)) + 34
    hf, ls = fit(dr, s["headline"], W - 2 * M, 84 if tall else 72, 56)
    for l in ls:
        dr.text((M, y), l, font=hf, fill=WHITE); y += int(hf.size * 1.12)
    y += 36 if tall else 26
    stats = (s.get("stats") or d.get("tape") or [])[:6]
    if stats:
        cols, gap = 2, (24 if tall else 18)
        cw = (W - 2 * M - gap) // cols
        ch = 170 if tall else 150
        for i, t in enumerate(stats):
            cx, cy = M + (i % cols) * (cw + gap), y + (i // cols) * (ch + gap)
            dr.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=18, fill=(36, 54, 92))
            dr.rectangle((cx, cy + 18, cx + 6, cy + ch - 18), fill=dir_col(t))
            dr.text((cx + 28, cy + 18), t["label"], font=F("SemiBold", 26), fill=MUTE)
            vf = F("ExtraBold", 50 if tall else 44)
            dr.text((cx + 28, cy + 52), t["value"], font=vf, fill=WHITE)
            arrow(dr, cx + 36 + dr.textlength(t["value"], font=vf), cy + 66 if tall else cy + 62, t.get("dir"), dir_col(t), 22)
            if t.get("note"):
                nf = F("Regular", 24)
                note = t["note"]
                while dr.textlength(note, font=nf) > cw - 50 and " " in note:
                    note = note.rsplit(" ", 1)[0]
                dr.text((cx + 28, cy + ch - 42), note, font=nf, fill=MUTE)
        y += ((len(stats) + 1) // 2) * (ch + gap) + (24 if tall else 6)
    pf = F("Bold", 38 if tall else 34)
    dr.text((M, y), "The driver", font=F("SemiBold", 28), fill=AMBER); y += 48
    for p in s["points"]:
        if y > H - M - 150: break
        dr.ellipse((M, y + 12, M + 16, y + 28), fill=AMBER)
        for l in wrap(dr, p, pf, W - 2 * M - 40):
            dr.text((M + 36, y), l, font=pf, fill=WHITE); y += int(pf.size * 1.3)
        y += 10 if tall else 4
    footer(im, dr, d, W, H, M)
    im.save(path, optimize=True)
    return y

def card_midday(d, s, W, H, path, pad=0):
    tall = H > W * 1.5
    im = Image.new("RGB", (W, H), PAPER); dr = ImageDraw.Draw(im); M = 80
    dr.rectangle((0, 0, W, 18), fill=AMBER)
    y = header(im, M + 10, light=True) + (80 if tall else 50) + pad
    dr.text((M, y), s["kicker"].upper(), font=F("Bold", 30), fill=(176, 112, 20)); y += 60
    hf, ls = fit(dr, s["headline"], W - 2 * M, 86 if tall else 74, 56)
    for l in ls:
        dr.text((M, y), l, font=hf, fill=NAVY); y += int(hf.size * 1.12)
    y += 40 if tall else 30
    st = (s.get("stats") or [None])[0]
    if st:
        bh = 250 if tall else 200
        dr.rounded_rectangle((M, y, W - M, y + bh), radius=24, fill=NAVY)
        vf = F("ExtraBold", 120 if tall else 100)
        dr.text((M + 44, y + (34 if tall else 24)), st["value"], font=vf, fill=AMBER)
        ly = y + bh - (78 if tall else 66)
        lab = st["label"] + (f"  ·  {st['note']}" if st.get("note") else "")
        sz = 34 if tall else 30
        while sz > 20 and dr.textlength(lab, font=F("SemiBold", sz)) > W - 2 * M - 88:
            sz -= 2
        lf = F("SemiBold", sz)
        dr.text((M + 44, ly), lab, font=lf, fill=WHITE)
        y += bh + (48 if tall else 34)
    pf = F("Bold", 40 if tall else 36)
    for i, p in enumerate(s["points"]):
        if y > H - M - 200: break
        dr.ellipse((M, y - 2, M + 56, y + 54), fill=AMBER)
        n = str(i + 1); nf = F("ExtraBold", 32)
        dr.text((M + 28 - dr.textlength(n, font=nf) / 2, y + 7), n, font=nf, fill=NAVY)
        for l in wrap(dr, p, pf, W - 2 * M - 84):
            dr.text((M + 84, y + 2), l, font=pf, fill=NAVY); y += int(pf.size * 1.3)
        y += 26 if tall else 16
    if s.get("watch") and y < H - M - 230:
        y += 10
        dr.text((M, y), "WATCH  " + s["watch"], font=F("SemiBold", 32), fill=(176, 112, 20)); y += 44
    footer(im, dr, d, W, H, M, light=True)
    im.save(path, optimize=True)
    return y

def card_evening(d, s, W, H, path, pad=0):
    tall = H > W * 1.5
    im = Image.new("RGB", (W, H), INK); dr = ImageDraw.Draw(im); M = 80
    # globe linework, top right
    cx, cy, r = W - 60, H - 380, 340
    gl = (24, 40, 72)
    for k in range(0, 5):
        dr.ellipse((cx - r + k * 72, cy - r, cx + r - k * 72, cy + r), outline=gl, width=2)
    for k in range(-2, 3):
        yy = cy + k * r / 3
        hw = (r * r - (yy - cy) ** 2) ** 0.5
        dr.line((cx - hw, yy, cx + hw, yy), fill=gl, width=2)
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(0, 70, 115), width=3)
    y = header(im, M) + (90 if tall else 56) + pad
    dr.text((M, y), s["kicker"].upper(), font=F("Bold", 30), fill=BLUE); y += 62
    hf, ls = fit(dr, s["headline"], W - 2 * M, 84 if tall else 72, 56)
    for l in ls:
        dr.text((M, y), l, font=hf, fill=WHITE); y += int(hf.size * 1.12)
    y += 44 if tall else 30
    pf = F("Bold", 40 if tall else 36)
    for i, p in enumerate(s["points"]):
        if y > H - M - 260: break
        n = f"0{i + 1}"
        dr.text((M, y - 4), n, font=F("ExtraBold", 44), fill=BLUE)
        top = y
        for l in wrap(dr, p, pf, W - 2 * M - 100):
            dr.text((M + 100, y), l, font=pf, fill=WHITE); y += int(pf.size * 1.3)
        y += 20 if tall else 12
        dr.line((M + 100, y - 8, W - M, y - 8), fill=(40, 58, 92), width=2)
        y += 14 if tall else 8
    if s.get("watch"):
        y += 16 if tall else 6
        wf = F("SemiBold", 36 if tall else 32)
        wl = wrap(dr, s["watch"], wf, W - 2 * M - 64)
        bh = 74 + len(wl) * int(wf.size * 1.3)
        if y + bh < H - M - 120:
            dr.rounded_rectangle((M, y, W - M, y + bh), radius=20, outline=GREEN, width=3)
            dr.text((M + 32, y + 22), "WHAT TO WATCH", font=F("Bold", 24), fill=GREEN)
            yy = y + 60
            for l in wl:
                dr.text((M + 32, yy), l, font=wf, fill=WHITE); yy += int(wf.size * 1.3)
            y += bh
    footer(im, dr, d, W, H, M)
    im.save(path, optimize=True)
    return y

STYLES = {"morning": card_morning, "midday": card_midday, "evening": card_evening}

def render(fn, d, s, W, H, path):
    # draw once, then center the content block in the free space above the footer
    end = fn(d, s, W, H, path)
    free = (H - 80 - 130) - end
    if free > 60:
        fn(d, s, W, H, path, pad=min(free // 2, 260))

for d in data:
    if "social" not in d:
        continue
    p = f"social/{d['date']}.png"
    if d is latest or not os.path.exists(p):
        render(card_morning, d, d["social"], 1080, 1350, p)
        render(card_morning, d, d["social"], 1080, 1920, f"social/{d['date']}-story.png")
        open(f"social/{d['date']}.txt", "w").write(d["social"]["caption"] + "\n")
        for slot, ss in d.get("social_slots", {}).items():
            fn = STYLES.get(slot, card_evening)
            render(fn, d, ss, 1080, 1350, f"social/{d['date']}-{slot}.png")
            render(fn, d, ss, 1080, 1920, f"social/{d['date']}-{slot}-story.png")
            open(f"social/{d['date']}-{slot}.txt", "w").write(ss["caption"] + "\n")

# Posting manifest for the scheduled social task: three posts a day
slots = {"morning": {"image": f"https://fiopoin.com/social/{latest['date']}.png",
                     "story": f"https://fiopoin.com/social/{latest['date']}-story.png", "caption": latest["social"]["caption"]}}
for slot, ss in latest.get("social_slots", {}).items():
    slots[slot] = {"image": f"https://fiopoin.com/social/{latest['date']}-{slot}.png",
                   "story": f"https://fiopoin.com/social/{latest['date']}-{slot}-story.png", "caption": ss["caption"]}
json.dump({"date": latest["date"], "slots": slots}, open("social/today.json", "w"), indent=1)
Image.open(f"social/{latest['date']}.png").save("social/latest.png")
open("social/latest.txt", "w").write(latest["social"]["caption"] + "\n")
print("built", latest["date"], "editions:", len(data))
