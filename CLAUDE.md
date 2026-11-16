# fiopoin.com: FIOPO Intelligence

Static site on GitHub Pages (repo fiopoin/fiopoin-site, branch main, custom domain fiopoin.com via GoDaddy DNS).

## How the site is built
- One JSON file per edition in `content/YYYY-MM-DD.json`. The newest file becomes the homepage.
- `python3 tools/build.py` renders `templates/page.html.j2` into `index.html`, writes `archive/<date>.html`, `archive/index.html`, `feed.xml`, and the social graphics `social/<date>.png` (1080x1350 feed post), `social/<date>-story.png` (1080x1920 story or reel cover), `social/latest.png` and the caption `social/<date>.txt`.
- Never hand edit `index.html`, `archive/` or `feed.xml`. Edit content JSON or the template, then rebuild.
- Requires `jinja2` and `Pillow` (`pip install --break-system-packages jinja2 pillow` if missing). Fonts are bundled in `tools/fonts`.

## Content JSON schema (copy the latest file and replace every field)
date, date_long, edition, hero{headline, dek, chain[5]{label,value,text}, caption}, tape[6]{label,value,note,dir: up|down|flat}, stories[4]{id, topic, headline, stake{level: hi|md|lo, text}, happened, happening, could{odds[]{label,pct}, text, note}, you[], watch, sources[]{name,url}}, culture[2]{topic, headline, happened, happening, could, you[], sources[]}, calc{gas_now, gas_year_ago, gas_note}, social{kicker, headline, points[3], caption}.
Story ids "money" and "world" must exist (the nav links to them).

## Editorial rules
- Every fact is sourced, dated and linked. Never invent numbers. If a figure cannot be confirmed, leave it out.
- Odds and outlooks are FIOPO judgment and must be labeled in `could.note` ("FIOPO read. Judgment, not fact."). Market odds are labeled as market odds.
- No em dashes or en dashes used as punctuation. Plain, direct, human prose. No hype.
- Stay politically neutral: report positions and facts, no endorsements.
- Every story ends with concrete "what it means for you" actions. General information only, never personalized investment advice.
- Social headline under 60 characters; points under 40 characters each; caption under 600 characters with 4 to 6 hashtags.

## Publishing
Commit as user "fiopoin" and push to main. GitHub Pages deploys within about a minute.

## Brand
- Official logo: the fiopoin wordmark in `brand/` (white letters for navy backgrounds `fiopoin-logo-white.svg`, navy letters for light backgrounds `fiopoin-logo-navy.svg`). Do not add "Intelligence" or any other text next to it. Favicon and social profile icon: `brand/fiopoin-icon.svg` and PNG sizes.
- Brand colors: navy #1B2A4A, amber #E9A23B (happened), blue #0091D2 (happening), green #8CC63F (next / what it means for you).
