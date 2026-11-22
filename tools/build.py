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

# Daily social graphics (Raj, Nov 22, 2026): news first, money angle at the bottom in "What to watch".
# Each slot has its own colors and layout, plus a visual: a bar chart (slot "chart") or a drawn topic illustration.
#   morning = sunrise blue gradient, illustration or chart, market strip in the watch box
#   midday  = light paper, amber accents, chart or big number
#   evening = dark ink with globe linework, green watch box
# Slot fields: kicker, headline, points[3] (news facts), watch (the money angle), optional
#   chart{title, items[2..6]{label, value(number), display?}, source}, optional stats[1]{label,value,note} (midday big number),
#   optional icon (oil chip bank ship market globe briefcase coins factory bolt drop plane scales).
NAVY, INK, BLUE, GREEN, AMBER, WHITE, MUTE = (27,42,74), (15,26,49), (0,145,210), (140,198,63), (233,162,59), (255,255,255), (159,179,207)
PAPER, RED = (246,242,234), (214,82,74)
F = lambda w, s: ImageFont.truetype(f"tools/fonts/Inter-{w}.otf", s)
logo = Image.open("brand/fiopo-intelligence-white-1000.png").convert("RGBA")
small = Image.open("brand/fiopoin-logo-white-900.png").convert("RGBA")

def navyize(img):
    px = img.copy(); data = px.load()
    for yy in range(px.height):
        for xx in range(px.width):
            r, g, b, a = data[xx, yy]
            if a and min(r, g, b) > 200:
                data[xx, yy] = (*NAVY, a)
    return px
logo_n, small_n = navyize(logo), navyize(small)

THEMES = {
    "morning": dict(top=(8, 128, 196), bottom=(10, 70, 128), text=WHITE, sub=(205, 228, 245), accent=AMBER,
                    pill=AMBER, pillfg=NAVY, card=(255, 255, 255, 34), watch=AMBER, light=False),
    "midday": dict(top=PAPER, bottom=PAPER, text=NAVY, sub=(110, 118, 135), accent=(196, 124, 20),
                   pill=NAVY, pillfg=AMBER, card=(27, 42, 74, 255), watch=(196, 124, 20), light=True),
    "evening": dict(top=(17, 22, 38), bottom=(6, 9, 18), text=WHITE, sub=MUTE, accent=GREEN,
                    pill=GREEN, pillfg=INK, card=(255, 255, 255, 22), watch=GREEN, light=False),
}

def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
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

# ---------- drawn illustrations (flat, brand colors, no people, no flags, no symbols of any group) ----------
ICON_WORDS = [
    ("oil", "oil crude brent wti opec barrel fuel gasoline diesel refin"),
    ("ship", "ship tanker hormuz shipping port freight strait red sea canal"),
    ("chip", "chip nvidia semiconductor ai tsmc data center gpu software tech"),
    ("bank", "fed central bank rate ecb boj pboc yield treasury bond inflation pce cpi"),
    ("bolt", "power grid electricity nuclear solar wind utility"),
    ("drop", "water desal drought flood"),
    ("plane", "airline travel flight airfare"),
    ("factory", "factory manufactur tariff trade export import supply"),
    ("briefcase", "deal merger acquisition ipo buyout stake funding raise"),
    ("coins", "bitcoin crypto gold dollar currency yen euro"),
    ("market", "stock s&p nasdaq dow nikkei kospi index sell-off rally shares market"),
    ("globe", "world global war talks summit ceasefire"),
]

def pick_icon(s):
    if s.get("icon"):
        return s["icon"]
    txt = (s["headline"] + " " + " ".join(s.get("points", []))).lower()
    for name, words in ICON_WORDS:
        if any(w in txt for w in words.split()):
            return name
    return "globe"

def draw_icon(name, size, bg, fg, ac):
    S = size * 3
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, S, S), fill=bg)
    c, u = S / 2, S / 100
    if name == "oil":
        d.rounded_rectangle((c - 22*u, c - 30*u, c + 22*u, c + 32*u), radius=6*u, fill=fg)
        for yy in (-14, 2, 18):
            d.rectangle((c - 22*u, c + yy*u, c + 22*u, c + (yy + 4)*u), fill=bg)
        d.polygon([(c + 30*u, c - 40*u), (c + 22*u, c - 24*u), (c + 38*u, c - 24*u)], fill=ac)
        d.ellipse((c + 22*u, c - 30*u, c + 38*u, c - 14*u), fill=ac)
    elif name == "ship":
        d.polygon([(c - 36*u, c + 4*u), (c + 36*u, c + 4*u), (c + 26*u, c + 24*u), (c - 26*u, c + 24*u)], fill=fg)
        for i, col in enumerate((ac, (0, 145, 210), GREEN)):
            d.rectangle((c - 26*u + i * 18*u, c - 12*u, c - 12*u + i * 18*u, c + 4*u), fill=col)
        d.rectangle((c + 22*u, c - 22*u, c + 30*u, c + 4*u), fill=fg)
        d.arc((c - 40*u, c + 26*u, c - 10*u, c + 38*u), 180, 360, fill=fg, width=int(3*u))
        d.arc((c + 10*u, c + 26*u, c + 40*u, c + 38*u), 180, 360, fill=fg, width=int(3*u))
    elif name == "chip":
        d.rounded_rectangle((c - 24*u, c - 24*u, c + 24*u, c + 24*u), radius=5*u, fill=fg)
        d.rounded_rectangle((c - 12*u, c - 12*u, c + 12*u, c + 12*u), radius=3*u, fill=ac)
        for k in (-14, 0, 14):
            for (x1, y1, x2, y2) in [(c + k*u - 2*u, c - 36*u, c + k*u + 2*u, c - 24*u), (c + k*u - 2*u, c + 24*u, c + k*u + 2*u, c + 36*u),
                                     (c - 36*u, c + k*u - 2*u, c - 24*u, c + k*u + 2*u), (c + 24*u, c + k*u - 2*u, c + 36*u, c + k*u + 2*u)]:
                d.rectangle((x1, y1, x2, y2), fill=fg)
    elif name == "bank":
        d.polygon([(c - 36*u, c - 14*u), (c, c - 36*u), (c + 36*u, c - 14*u)], fill=fg)
        for k in (-26, -9, 8, 25):
            d.rectangle((c + k*u - 4*u, c - 10*u, c + k*u + 4*u, c + 20*u), fill=fg)
        d.rectangle((c - 38*u, c + 22*u, c + 38*u, c + 30*u), fill=ac)
    elif name == "bolt":
        d.polygon([(c + 6*u, c - 40*u), (c - 22*u, c + 6*u), (c - 2*u, c + 6*u), (c - 8*u, c + 40*u), (c + 22*u, c - 8*u), (c + 2*u, c - 8*u)], fill=ac)
    elif name == "drop":
        d.polygon([(c, c - 38*u), (c - 24*u, c + 4*u), (c + 24*u, c + 4*u)], fill=(0, 145, 210))
        d.ellipse((c - 25*u, c - 14*u, c + 25*u, c + 36*u), fill=(0, 145, 210))
        d.ellipse((c - 12*u, c + 2*u, c - 4*u, c + 14*u), fill=WHITE)
    elif name == "plane":
        d.polygon([(c - 38*u, c + 2*u), (c + 30*u, c - 6*u), (c + 38*u, c), (c + 30*u, c + 6*u)], fill=fg)
        d.polygon([(c - 4*u, c - 2*u), (c + 10*u, c - 2*u), (c - 10*u, c - 30*u), (c - 18*u, c - 30*u)], fill=fg)
        d.polygon([(c - 4*u, c + 4*u), (c + 10*u, c + 4*u), (c - 10*u, c + 30*u), (c - 18*u, c + 30*u)], fill=fg)
        d.polygon([(c - 34*u, c + 1*u), (c - 26*u, c), (c - 34*u, c - 14*u), (c - 40*u, c - 14*u)], fill=ac)
    elif name == "factory":
        d.polygon([(c - 36*u, c + 28*u), (c - 36*u, c - 4*u), (c - 18*u, c + 8*u), (c - 18*u, c - 4*u), (c, c + 8*u), (c, c - 4*u),
                   (c + 18*u, c + 8*u), (c + 18*u, c - 30*u), (c + 30*u, c - 30*u), (c + 30*u, c + 28*u)], fill=fg)
        d.ellipse((c + 16*u, c - 44*u, c + 30*u, c - 32*u), fill=ac)
        for k in (-28, -10, 8):
            d.rectangle((c + k*u, c + 14*u, c + (k + 8)*u, c + 20*u), fill=ac)
    elif name == "briefcase":
        d.rounded_rectangle((c - 36*u, c - 16*u, c + 36*u, c + 28*u), radius=6*u, fill=fg)
        d.rounded_rectangle((c - 12*u, c - 28*u, c + 12*u, c - 14*u), radius=4*u, outline=fg, width=int(5*u))
        d.rectangle((c - 36*u, c + 2*u, c + 36*u, c + 6*u), fill=bg)
        d.rounded_rectangle((c - 6*u, c - 2*u, c + 6*u, c + 10*u), radius=2*u, fill=ac)
    elif name == "coins":
        for k, col in ((14, fg), (0, ac), (-14, ac)):
            d.ellipse((c - 26*u, c + k*u - 8*u, c + 26*u, c + k*u + 8*u), fill=col, outline=bg, width=int(2*u))
        d.ellipse((c + 6*u, c - 34*u, c + 38*u, c - 2*u), fill=ac, outline=bg, width=int(2*u))
    elif name == "market":
        for i, (h0, h1, col) in enumerate([(10, 26, GREEN), (-6, 14, RED), (-20, 2, GREEN), (-30, -10, GREEN)]):
            x = c - 30*u + i * 19*u
            d.line((x + 5*u, c + (h0 - 8)*u, x + 5*u, c + (h1 + 8)*u), fill=fg, width=int(2*u))
            d.rectangle((x, c + h0*u, x + 10*u, c + h1*u), fill=col)
        d.line((c - 36*u, c + 34*u, c + 38*u, c + 34*u), fill=fg, width=int(3*u))
    else:  # globe
        d.ellipse((c - 34*u, c - 34*u, c + 34*u, c + 34*u), fill=(0, 145, 210))
        d.ellipse((c - 34*u, c - 34*u, c + 34*u, c + 34*u), outline=fg, width=int(3*u))
        d.ellipse((c - 14*u, c - 34*u, c + 14*u, c + 34*u), outline=fg, width=int(3*u))
        d.line((c - 34*u, c, c + 34*u, c), fill=fg, width=int(3*u))
        d.line((c - 30*u, c - 16*u, c + 30*u, c - 16*u), fill=fg, width=int(2*u))
        d.line((c - 30*u, c + 16*u, c + 30*u, c + 16*u), fill=fg, width=int(2*u))
    return im.resize((size, size), Image.LANCZOS)

# ---------- chart ----------
def draw_chart(dr, ch, x, y, w, h, th):
    items = ch["items"][:6]
    dr.text((x, y), ch.get("title", ""), font=F("Bold", 30), fill=th["text"])
    y0, n = y + 54, len(items)
    lf = F("SemiBold", 26)
    lw = max(dr.textlength(i["label"], font=lf) for i in items) + 24
    lw = min(lw, w * 0.38)
    vals = [float(i["value"]) for i in items]
    mx = max(abs(v) for v in vals) or 1
    neg = any(v < 0 for v in vals) and any(v > 0 for v in vals)
    bx, bw = x + lw, w - lw - 150
    zero = bx + bw / 2 if neg else bx
    span = bw / 2 if neg else bw
    rowh = min(64, (h - 54 - 40) / n)
    for i, it in enumerate(items):
        yy = y0 + i * rowh
        v = vals[i]
        col = GREEN if v > 0 else RED if v < 0 else MUTE
        if not any(v < 0 for v in vals):
            col = th["accent"]
        lab = it["label"]
        while dr.textlength(lab, font=lf) > lw - 16 and len(lab) > 4:
            lab = lab[:-2] + "…" if not lab.endswith("…") else lab[:-2] + "…"
        dr.text((x, yy + rowh / 2 - 16), lab, font=lf, fill=th["text"])
        L = span * abs(v) / mx
        bh = rowh * 0.62
        if neg:
            x1, x2 = (zero, zero + L) if v >= 0 else (zero - L, zero)
        else:
            x1, x2 = zero, zero + L
        dr.rounded_rectangle((x1, yy + (rowh - bh) / 2, max(x2, x1 + 4), yy + (rowh + bh) / 2), radius=6, fill=col)
        disp = it.get("display") or f"{v:g}"
        vx = (x2 + 12) if (v >= 0 or not neg) else (zero + 12)
        dr.text((vx, yy + rowh / 2 - 18), disp, font=F("Bold", 30), fill=th["text"])
    if neg:
        dr.line((zero, y0 - 6, zero, y0 + n * rowh), fill=th["sub"], width=2)
    if ch.get("source"):
        dr.text((x, y0 + n * rowh + 8), "Source: " + ch["source"], font=F("Regular", 22), fill=th["sub"])

def gradient(W, H, top, bottom):
    base = Image.new("RGB", (W, H), top)
    if top == bottom:
        return base
    grad = Image.new("L", (1, H))
    for yy in range(H):
        grad.putpixel((0, yy), int(255 * yy / H))
    grad = grad.resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), bottom), base, grad)

def card(d, s, slot, W, H, path, pad=0):
    th = THEMES[slot]; tall = H > W * 1.5; M = 80
    im = gradient(W, H, th["top"], th["bottom"]).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    if slot == "morning":   # rising sun arcs, top right
        for k, a in enumerate((40, 28, 18)):
            r = 260 + k * 110
            od.ellipse((W - 120 - r, -160 - r, W - 120 + r, -160 + r), outline=(255, 214, 120, a), width=26)
    elif slot == "evening":  # globe linework, bottom right
        cx, cy, r = W - 40, H - 420, 330
        for k in range(5):
            od.ellipse((cx - r + k * 66, cy - r, cx + r - k * 66, cy + r), outline=(80, 120, 190, 55), width=2)
        for k in range(-2, 3):
            yy = cy + k * r / 3; hw = (r * r - (yy - cy) ** 2) ** 0.5
            od.line((cx - hw, yy, cx + hw, yy), fill=(80, 120, 190, 55), width=2)
    else:  # midday amber band
        od.rectangle((0, 0, W, 18), fill=(*AMBER, 255))
    im = Image.alpha_composite(im, ov); dr = ImageDraw.Draw(im)
    lg = logo_n if th["light"] else logo
    lg = lg.resize((500, int(500 * lg.height / lg.width)), Image.LANCZOS)
    im.paste(lg, (M, M - 6), lg)
    y = M - 6 + lg.height + (64 if tall else 40) + pad
    kf = F("Bold", 26)
    kt = s["kicker"].upper()
    dr.rounded_rectangle((M, y, M + dr.textlength(kt, font=kf) + 40, y + 50), radius=25, fill=th["pill"])
    dr.text((M + 20, y + 11), kt, font=kf, fill=th["pillfg"]); y += 76
    hf, ls = fit(dr, s["headline"], W - 2 * M, 82 if tall else 70, 52)
    for l in ls:
        dr.text((M, y), l, font=hf, fill=th["text"]); y += int(hf.size * 1.12)
    y += 34 if tall else 22
    # visual
    chart = s.get("chart")
    big = (s.get("stats") or [None])[0] if slot == "midday" else None
    pf = F("Bold", 38 if tall else 33)
    if chart and chart.get("items"):
        chh = 70 + min(len(chart["items"]), 6) * (64 if tall else 54) + 40
        if th["light"]:
            dr.rounded_rectangle((M - 20, y - 16, W - M + 20, y + chh), radius=22, fill=WHITE, outline=(226, 218, 202), width=2)
        else:
            cv = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(cv).rounded_rectangle((M - 20, y - 16, W - M + 20, y + chh), radius=22, fill=th["card"])
            im.alpha_composite(cv); dr = ImageDraw.Draw(im)
        draw_chart(dr, chart, M, y, W - 2 * M, chh, th)
        y += chh + (36 if tall else 24)
        textw = W - 2 * M - 40
        icon_box = None
    else:
        isz = 250 if tall else 210
        bgc = (255, 255, 255, 40) if not th["light"] else (*NAVY, 255)
        ic = draw_icon(pick_icon(s), isz, bgc if th["light"] else (255, 255, 255, 46), WHITE, AMBER if slot != "evening" else GREEN)
        icon_box = (W - M - isz, y, isz)
        im.paste(ic, (W - M - isz, y), ic); dr = ImageDraw.Draw(im)
        textw = W - 2 * M - isz - 70
    if big:
        bh = 190 if tall else 160
        dr.rounded_rectangle((M, y, M + textw, y + bh), radius=20, fill=NAVY)
        vf, _ = fit(dr, big["value"], textw - 60, 100 if tall else 84, 48, maxlines=1)
        dr.text((M + 30, y + 18), big["value"], font=vf, fill=AMBER)
        lab = big["label"] + (f", {big['note']}" if big.get("note") else "")
        lf, ll = fit(dr, lab, textw - 60, 28, 20, maxlines=1, weight="SemiBold")
        dr.text((M + 30, y + bh - 50), ll[0], font=lf, fill=WHITE)
        y += bh + 26
    ytxt = y
    for i, p in enumerate(s["points"]):
        if slot == "midday":
            dr.ellipse((M, y, M + 46, y + 46), fill=AMBER)
            n = str(i + 1); nf = F("ExtraBold", 28)
            dr.text((M + 23 - dr.textlength(n, font=nf) / 2, y + 7), n, font=nf, fill=NAVY)
        elif slot == "evening":
            dr.text((M, y - 2), f"0{i + 1}", font=F("ExtraBold", 36), fill=GREEN)
        else:
            dr.ellipse((M + 4, y + 12, M + 22, y + 30), fill=AMBER)
        for l in wrap(dr, p, pf, textw - 70):
            dr.text((M + 70, y), l, font=pf, fill=th["text"]); y += int(pf.size * 1.28)
        y += 14 if tall else 8
    if icon_box:
        y = max(y, icon_box[1] + icon_box[2] + 10)
    # bottom: the money angle
    y += 18 if tall else 10
    wf = F("SemiBold", 34 if tall else 30)
    wl = wrap(dr, s.get("watch", ""), wf, W - 2 * M - 60) if s.get("watch") else []
    strip = (d.get("tape") or [])[:3] if slot == "morning" else []
    bh = 64 + len(wl) * int(wf.size * 1.3) + (118 if strip else 0)
    if wl or strip:
        if th["light"]:
            dr.rounded_rectangle((M - 20, y, W - M + 20, y + bh), radius=20, fill=(251, 236, 210))
        else:
            dr.rounded_rectangle((M - 20, y, W - M + 20, y + bh), radius=20, outline=th["watch"], width=3)
        dr.text((M + 10, y + 20), "WHAT TO WATCH", font=F("Bold", 24), fill=th["watch"])
        yy = y + 58
        if strip:
            tw = (W - 2 * M - 40) // 3
            for k, t in enumerate(strip):
                tx = M + 10 + k * (tw + 10)
                dr.text((tx, yy), t["label"], font=F("SemiBold", 22), fill=th["sub"])
                vfnt = F("ExtraBold", 38)
                dr.text((tx, yy + 30), t["value"], font=vfnt, fill=th["text"])
                col = GREEN if t.get("dir") == "up" else RED if t.get("dir") == "down" else th["sub"]
                ax = tx + dr.textlength(t["value"], font=vfnt) + 10
                if t.get("dir") == "up":
                    dr.polygon([(ax, yy + 66), (ax + 18, yy + 66), (ax + 9, yy + 48)], fill=col)
                elif t.get("dir") == "down":
                    dr.polygon([(ax, yy + 48), (ax + 18, yy + 48), (ax + 9, yy + 66)], fill=col)
            yy += 112
        for l in wl:
            dr.text((M + 10, yy), l, font=wf, fill=th["text"]); yy += int(wf.size * 1.3)
        y += bh
    # footer
    line = (200, 192, 176) if th["light"] else (255, 255, 255)
    dr.line((M, H - M - 96, W - M, H - M - 96), fill=line if th["light"] else (90, 120, 170), width=2)
    dr.text((M, H - M - 70), d["date_long"], font=F("Regular", 28), fill=th["sub"])
    dr.text((M, H - M - 30), "Full story: fiopoin.com", font=F("SemiBold", 34), fill=NAVY if th["light"] else GREEN if slot == "evening" else WHITE)
    sm = small_n if th["light"] else small
    sm = sm.resize((180, int(180 * sm.height / sm.width)), Image.LANCZOS)
    im.paste(sm, (W - M - sm.width, H - M - sm.height + 4), sm)
    im.convert("RGB").save(path, optimize=True)
    return y

def render(slot, d, s, W, H, path):
    end = card(d, s, slot, W, H, path)
    room = (H - 80 - 120) - end
    if room < 0:
        print(f"WARNING social overflow {path} by {-room}px")
    elif room > 60:
        card(d, s, slot, W, H, path, pad=min(room // 2, 420))

for d in data:
    if "social" not in d:
        continue
    p = f"social/{d['date']}.png"
    if d is latest or not os.path.exists(p):
        render("morning", d, d["social"], 1080, 1350, p)
        render("morning", d, d["social"], 1080, 1920, f"social/{d['date']}-story.png")
        open(f"social/{d['date']}.txt", "w").write(d["social"]["caption"] + "\n")
        for slot, ss in d.get("social_slots", {}).items():
            sl = slot if slot in THEMES else "evening"
            render(sl, d, ss, 1080, 1350, f"social/{d['date']}-{slot}.png")
            render(sl, d, ss, 1080, 1920, f"social/{d['date']}-{slot}-story.png")
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
