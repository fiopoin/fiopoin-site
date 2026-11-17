# fiopoin.com: FIOPO Intelligence

Static site on GitHub Pages (repo fiopoin/fiopoin-site, branch main, custom domain fiopoin.com via GoDaddy DNS).

## How the site is built
- One JSON file per edition in `content/YYYY-MM-DD.json`. The newest file becomes the homepage.
- `python3 tools/build.py` renders `templates/page.html.j2` into `index.html`, writes `archive/<date>.html`, `archive/index.html`, `feed.xml`, and the social graphics `social/<date>.png` (1080x1350 feed post), `social/<date>-story.png` (1080x1920 story or reel cover), `social/latest.png` and the caption `social/<date>.txt`.
- Never hand edit `index.html`, `archive/` or `feed.xml`. Edit content JSON or the template, then rebuild.
- Requires `jinja2` and `Pillow` (`pip install --break-system-packages jinja2 pillow` if missing). Fonts are bundled in `tools/fonts`.

## Content JSON schema (copy the latest file and replace every field)
date, date_long, edition, hero{headline, dek, chain[5]{label,value,text}, caption}, tape[6]{label,value,note,dir: up|down|flat}, stories[4]{id, topic, headline, stake{level: hi|md|lo, text}, happened, happening, could{odds[]{label,pct}, text, note}, you[], watch, sources[]{name,url}}, culture[2]{topic, headline, happened, happening, could, you[], sources[]}, calc{gas_now, gas_year_ago, gas_note}, social{kicker, headline, points[3], caption}, social_slots{midday{kicker, headline, points[3], watch, caption}, evening{kicker, headline, points[3], watch, caption}}.
Three social posts a day, each with different content: morning = `social` (the hero ripple), midday = `social_slots.midday` (the "money" story, kicker "Midday: your money"), evening = `social_slots.evening` (the "world" story or the biggest culture story, kicker "Evening: the world and your wallet"). The build writes `social/<date>-midday.png`, `social/<date>-evening.png`, their .txt captions, and `social/today.json`, the posting manifest the scheduled social task reads.
Story ids "money" and "world" must exist (the nav links to them).

## Editorial rules
- Every fact is sourced, dated and linked. Never invent numbers. If a figure cannot be confirmed, leave it out.
- Odds and outlooks are FIOPO judgment and must be labeled in `could.note` ("FIOPO read. Judgment, not fact."). Market odds are labeled as market odds.
- No em dashes or en dashes used as punctuation. Plain, direct, human prose. No hype.
- Stay politically neutral: report positions and facts, no endorsements.
- Every story ends with concrete "what it means for you" actions. General information only, never personalized investment advice.
- Social headline under 60 characters; points under 40 characters each; caption under 600 characters with 4 to 6 hashtags. The same limits apply to each social_slots entry.

## Publishing
Commit as user "fiopoin" and push to main. GitHub Pages deploys within about a minute.

## Verify the live site after every update (mandatory)
In the cloud sandbox the shell and Playwright cannot reach fiopoin.com (proxy 403), WebFetch refuses URLs with a cache-busting query, and WebFetch cannot read PNGs. So verify this way:
1. Deploy: about 90 seconds after pushing, call the GitHub MCP `actions_list` (method `list_workflow_runs`, owner fiopoin, repo fiopoin-site). The newest "pages build and deployment" run must match the pushed SHA with conclusion "success". Retry every 60 seconds if still running.
2. Page: WebFetch exactly `https://fiopoin.com` (no query string) and confirm today's hero headline and date line, the FIOPO Intelligence header and the footer ("FIOPO Intelligence. Intelligence for prosperity."). If it still shows yesterday, wait 60 seconds and retry.
3. Images: WebFetch `https://fiopoin.com/social/today.json` and confirm today's date and the morning, midday and evening slots. The PNGs themselves are covered by the successful deploy of the commit that contains them.
4. Layout: check desktop and mobile renders of the local `index.html` with Playwright before pushing (the chain animates in on scroll, so a faded last step in a screenshot is expected).
5. Only report the update as done after 1 to 3 pass. If one fails, fix it, republish and check again.

## Brand
- Primary identity at the top of every page and social graphic: FIOPO Intelligence only (no tagline at the top). Header lockup = `brand/fiopo-white.svg` + "Intelligence" (Inter SemiBold, ripple underline). The tagline "Intelligence for prosperity" appears only in the page title and footer.
- "fiopoin" means FIOPO Intelligence (FIOPO + IN). The fiopoin wordmark (`brand/fiopoin-logo-white.svg`, `brand/fiopoin-logo-navy.svg`) is the secondary mark: footer, signup section, bottom corner of social graphics, favicon (`brand/fiopoin-icon.svg`). Always keep the full name FIOPO Intelligence in titles and metadata.
- Brand colors: navy #1B2A4A, amber #E9A23B (happened), blue #0091D2 (happening), green #8CC63F (next / what it means for you).
