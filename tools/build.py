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
    calls = []
    for e in data:
        if e["date"] > asof: continue
        made = datetime.strptime(e["date"], "%Y-%m-%d")
        for s in e.get("stories", []):
            c = s.get("could", {})
            if "FIOPO" not in c.get("note", "") or not c.get("odds"): continue
            for o in c["odds"]:
                calls.append({"label": o["label"], "pct": o["pct"], "made": e["date"], "made_long": _long(made),
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
       "alternateName": "fiopoin", "url": SITE, "email": "hello@fiopoin.com",
       "logo": {"@type": "ImageObject", "url": SITE + "brand/fiopoin-icon-512.png", "width": 512, "height": 512},
       "slogan": "Intelligence for prosperity",
       "sameAs": ["https://www.linkedin.com/company/89727570/"]}
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
        graph.append({"@type": "WebSite", "@id": SITE + "#site", "name": "FIOPO Intelligence", "url": SITE,
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
<footer><div class="wrap"><div class="fgrid"><a class="lockup" href="../"><img src="../brand/fiopoin-logo-white.svg" alt="fiopoin"></a><div><p>FIOPO Intelligence, fiopoin.com. General information, not financial advice. <a href="../privacy.html">Privacy</a></p></div></div></div></footer></body></html>"""
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
<footer><div class="wrap"><div class="fgrid"><a class="lockup" href="./"><img src="brand/fiopoin-logo-white.svg" alt="fiopoin"></a><div><p>FIOPO Intelligence. Intelligence for prosperity. fiopoin.com. General information, not financial advice.</p></div></div></div></footer></body></html>"""
open("privacy.html", "w").write(priv.replace("<h3>", '<h3 style="margin:26px 0 8px">'))

# sitemap.xml, robots.txt and llms.txt so search engines and AI assistants can find and cite every edition
urls = [(SITE, latest["date"], "daily", "1.0"), (SITE + "archive/", latest["date"], "daily", "0.6")]
urls += [(page_url(d, True), d["date"], "monthly", "0.7") for d in reversed(data)]
urls.append((SITE + "privacy.html", "2026-11-17", "yearly", "0.2"))
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

# Daily social graphics
NAVY, INK, BLUE, GREEN, AMBER, WHITE, MUTE = (27,42,74), (15,26,49), (0,145,210), (140,198,63), (233,162,59), (255,255,255), (159,179,207)
F = lambda w, s: ImageFont.truetype(f"tools/fonts/Inter-{w}.otf", s)
logo = Image.open("brand/fiopo-intelligence-white-1000.png").convert("RGBA")
small = Image.open("brand/fiopoin-logo-white-900.png").convert("RGBA")

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

def card(d, W, H, path, s=None, show_chain=True):
    s = s or d["social"]
    im = Image.new("RGB", (W, H), NAVY)
    dr = ImageDraw.Draw(im)
    M = 80
    lg = logo.resize((600, int(600 * logo.height / logo.width)), Image.LANCZOS)
    im.paste(lg, (M, M - 10), lg)
    y = M - 10 + lg.height + 60
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
    if s.get("watch") and not show_chain:
        y += 20
        dr.text((M, y), "What to watch", font=F("SemiBold", 30), fill=AMBER); y += 52
        for line in wrap(dr, s["watch"], F("Regular", 38), W - 2 * M):
            dr.text((M, y), line, font=F("Regular", 38), fill=WHITE); y += 52
    chain = d["hero"].get("chain", []) if show_chain else []
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
    sm = small.resize((190, int(190 * small.height / small.width)), Image.LANCZOS)
    im.paste(sm, (W - M - sm.width, H - M - sm.height + 4), sm)
    im.save(path, optimize=True)

for d in data:
    if "social" not in d:
        continue
    p = f"social/{d['date']}.png"
    if d is latest or not os.path.exists(p):
        card(d, 1080, 1350, p)
        card(d, 1080, 1920, f"social/{d['date']}-story.png")
        open(f"social/{d['date']}.txt", "w").write(d["social"]["caption"] + "\n")
        for slot, ss in d.get("social_slots", {}).items():
            card(d, 1080, 1350, f"social/{d['date']}-{slot}.png", ss, show_chain=False)
            open(f"social/{d['date']}-{slot}.txt", "w").write(ss["caption"] + "\n")

# Posting manifest for the scheduled social task: three posts a day
slots = {"morning": {"image": f"https://fiopoin.com/social/{latest['date']}.png", "caption": latest["social"]["caption"]}}
for slot, ss in latest.get("social_slots", {}).items():
    slots[slot] = {"image": f"https://fiopoin.com/social/{latest['date']}-{slot}.png", "caption": ss["caption"]}
json.dump({"date": latest["date"], "slots": slots}, open("social/today.json", "w"), indent=1)
Image.open(f"social/{latest['date']}.png").save("social/latest.png")
open("social/latest.txt", "w").write(latest["social"]["caption"] + "\n")
print("built", latest["date"], "editions:", len(data))
