# Holiday greetings (Raj, Nov 25, 2026)

A standing tradition: on every major holiday and occasion in `calendar.json`, all four sister publications (FIOPO Intelligence, Carbon Energy Nexus, Utica Midstream, Water Capital Wire) post a greeting graphic in addition to their normal scheduled posts. All brands may post at the same time.

- `make.py <out_dir> <spec.json>` renders `<brand>-<slug>.png` (1080x1350 feed) and `<brand>-<slug>-story.png` (1080x1920) for each brand in spec.messages. Needs all four repos cloned side by side under HOLIDAY_ROOT (default /home/claude). Motifs: harvest, fireworks, snow, lanterns, crescent, lights, blooms, drops, earth, stars.
- Graphics go to each repo at `social/holidays/<slug>.png` and `<slug>-story.png`, so they are served at https://<site>/social/holidays/<slug>.png.
- Copy: one short message per brand (under about 170 characters), in that brand's voice, warm, respectful and plain. No em or en dashes as punctuation, no politics, no jokes about any faith or culture, no religious imagery beyond the neutral motif. Never name the owner or FIOPO LLC.
- After posting, set "posted": true on that entry in calendar.json.
