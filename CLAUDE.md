# fiopoin.com: FIOPO Intelligence

Static site on GitHub Pages (repo fiopoin/fiopoin-site, branch main, custom domain fiopoin.com via GoDaddy DNS).

## How the site is built
- One JSON file per edition in `content/YYYY-MM-DD.json`. The newest file becomes the homepage.
- `python3 tools/build.py` renders `templates/page.html.j2` into `index.html`, writes `archive/<date>.html`, `archive/index.html`, `feed.xml`, and the social graphics `social/<date>.png` (1080x1350 feed post), `social/<date>-story.png` (1080x1920 story or reel cover), `social/latest.png` and the caption `social/<date>.txt`. It also writes the search and AI discovery files: `sitemap.xml`, `robots.txt` (welcomes all search engines and AI crawlers) and `llms.txt`, plus per-page canonical URLs, descriptions and schema.org JSON-LD (NewsMediaOrganization and NewsArticle). Never hand edit these; never block crawlers.
- Never hand edit `index.html`, `archive/`, `feed.xml`, `sitemap.xml`, `robots.txt` or `llms.txt`. Edit content JSON or the template, then rebuild.
- Requires `jinja2` and `Pillow` (`pip install --break-system-packages jinja2 pillow` if missing). Fonts are bundled in `tools/fonts`.

## Content JSON schema (copy the latest file and replace every field)
date, date_long, edition, hero{headline, dek, chain[5]{label,value,text}, caption}, tape[6]{label,value,note,dir: up|down|flat}, stories[4]{id, topic, headline, stake{level: hi|md|lo, text}, happened, happening, could{odds[]{label,pct}, text, note}, you[], watch, sources[]{name,url}}, culture[2]{topic, headline, happened, happening, could, you[], sources[]}, calc{gas_now, gas_year_ago, gas_note}, social{kicker, headline, points[3], caption}, social_slots{midday{kicker, headline, points[3], watch, caption}, evening{kicker, headline, points[3], watch, caption}}.
New sections (added November 17, 2026; every field required, nothing left empty or as a placeholder):
yesterday{label, items[5 to 6]{label,text}, sources[]}, regions[6]{region, covers, headline, text, you, sources[]} in this order: China and East Asia; India and South Asia; Europe; Middle East; Africa; South America (North America is covered by the main stories), sports[3]{topic, headline, text, you, sources[]} (at least one non-US sport such as cricket or football), entertainment[2]{same} (at least one non-US film, music or streaming story), trending{label "Trending online", items[2 to 3]{where, text}, sources[]} (only what is actually trending on YouTube, TikTok or X with news, money or entertainment relevance; omit the whole field if nothing fits, never force it), innovation[3]{topic, headline, text, you, sources[]} (at least one outside AI), travel[3]{tag, headline, text, you, image?{src, alt, credit, license, license_url, source_url}, sources[]} (tags: "Hidden treasure", "Famous, done smarter", "Travel money"), picks[2]{kind: Read|Watch, title, by, where, text, sources[]}, events{global[]{when, what, where, url}, industry_title, industry[]{when, what, where, url}, industry_note, sources[]} (every event gets its date, venue or city when published, and a link to the official event page or website; say "venue not yet listed" rather than guessing), highlights{week{label, items[3]{date, text, source, url}}, month{same}, year{same}} (extraordinary accomplishments and milestones: space, science, sport, medicine, engineering; refresh "week" every Monday, "month" at least weekly, "year" when something bigger happens).
The old `culture` field is only for editions before November 17, 2026. The scorecard in "Yesterday in 60 seconds" is computed by build.py from past FIOPO-labeled odds; record outcomes in `content/scorecard.json` as {"YYYY-MM-DD|odds label": "hit"|"miss"} once a call's 30 day window closes.
Travel and picks may carry over from the previous edition for up to 7 days if still accurate; refresh travel on Saturdays and picks on Fridays. Events: drop past dates every day and keep the Produced Water Society 2027 track current from producedwatersociety.com/annual-events/.
Finding stories: prefer what is getting the most traction (most-read and trending lists, YouTube and TikTok trending, Google Trends) when choosing among equally solid stories, but every item still needs a dated, linked, reliable source.

## Images and video (copyright and safety)
- Only public domain or openly licensed images: US federal government works (NPS, NASA, NOAA, CDC) or Wikimedia Commons files with a verified license (CC0, CC BY, CC BY-SA). Verify the license on the file page before use. Always fill credit, license and source_url; the template prints the attribution.
- Never use book covers, movie posters, news agency photos, stock photos, or any photo of a public figure.
- Images load from upload.wikimedia.org only (the content security policy allows only that outside host). Build the Commons thumbnail URL as https://upload.wikimedia.org/wikipedia/commons/thumb/{md5[0]}/{md5[0:2]}/{File_name}/{960 or 1280}px-{File_name} where md5 is of the underscored file name; never request a width larger than the original. A broken image hides itself.
- Videos are linked, never embedded.

Three social posts a day, each with different content: morning = `social` (the hero ripple), midday = `social_slots.midday` (the "money" story, kicker "Midday: your money"), evening = `social_slots.evening` (the "world" story or the biggest sports or entertainment story, kicker "Evening: the world and your wallet"). The build writes `social/<date>-midday.png`, `social/<date>-evening.png`, tall 1080x1920 story versions (`social/<date>-midday-story.png`, `social/<date>-evening-story.png`, and `social/<date>-story.png` for the morning), their .txt captions, and `social/today.json`, the posting manifest the scheduled social task reads.
Story ids "money" and "world" must exist (the nav links to them).

## Site settings, analytics and privacy
- `site.json` holds `ga_id` (Google Analytics 4 measurement ID), `google_site_verification` and `bing_site_verification`. When `ga_id` is set, the build adds the GA tag (via `assets/ga.js`, since the content security policy blocks inline scripts), widens the CSP for Google Analytics only, and switches `privacy.html` to its analytics wording. Never add other third-party scripts.
- `privacy.html` is generated by build.py and linked from every footer.

## Search and AI discovery
- The page description, social previews and `llms.txt` use the first paragraph of `social.caption`, so make that paragraph a factual, specific summary of the edition (under 300 characters works best).
- Keep the hero headline under 110 characters (the NewsArticle limit).

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

## Search engines (Raj, Nov 19, 2026)
- After every published edition is verified live, notify search engines with IndexNow: WebFetch https://api.indexnow.org/indexnow?url=https://fiopoin.com/&key=3babc945b5366a7ff2e53db9c4674569 and then the same with url=https://fiopoin.com/archive/<date>.html. The key file `3babc945b5366a7ff2e53db9c4674569.txt` at the site root must stay in place (do not delete or rename it; its value is site.json indexnow_key). A 200 or 202 reply means accepted; a failure here never blocks publishing.
- Google Search Console and Bing Webmaster Tools verification codes go in site.json (google_site_verification, bing_site_verification); the template prints them.
- The homepage title leads with the brand name; archive pages lead with the headline. Footers link the sister sites (FIOPO Intelligence, Carbon Energy Nexus, Utica Midstream).


- `about.html` is generated by build.py: who publishes fiopoin (FIOPO LLC, founded 2017), the brand name explanation and a not-affiliated note. Page titles always include "fiopoin" so brand searches match. Organization schema carries alternateName, legalName and founder.
