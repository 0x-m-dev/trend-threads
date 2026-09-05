# Trend Threads — SPEC

## Problem
Posting interesting X threads daily requires finding trending topics, writing
them up, and publishing — manual every day. Automate the first 80%: real
daily trend data → draft threads ready to post.

## Decisions (locked with owner, 2026-09-05)
- **No X API for now.** No auto-posting, no X credentials anywhere.
  Output = draft threads posted to Discord for human review + manual post.
- **LLM = Hermes itself.** No OpenAI/Anthropic keys. The scheduled Hermes
  agent drafts threads with its own active model (`/model router` default:
  cheap, fast). No LLM credentials in repo, ever.
- Salvage the working scraper approach from the `~/trending-threads`
  prototype (Reddit hot, Hacker News, news RSS, Google Trends via keyless
  firecrawl); rewrite generation/posting to the Hermes-native design below.
  Prototype dir is removed after salvage.

## Pipeline (daily, via `hermes cron`)
1. **Scrape** — Reddit r/hot, HN topstories, news RSS (+ Google Trends via
   `npx -y firecrawl-cli@latest`). Save raw JSON to `data/<date>/trends.json`.
2. **Draft** — cron agent picks 1 topic cluster, writes a 5–7 tweet draft
   (hook first, ≤280 chars/tweet, ends with question/CTA) to
   `data/<date>/thread.md`.
3. **Review** — draft posts to Discord for approval. Human posts to X manually.
4. **Log** — trends + drafts + posted/not-posted status stay in `data/`.

## Scope (v1)
- `scripts/scrape.py` — multi-source fetch, JSON dump. Pure stdlib + requests.
- Cron job (daily morning) running the scrape; agent drafts + delivers.
- Discord delivery of drafts; `data/` log layout.
- SPEC.md, PROJECT.yaml, AGENTS.md, README updated every push (hook-gated).

## Non-goals (v1)
- Auto-posting to X, X API credentials, engagement scraping, reply bot,
  multi-account, video/image threads.

## Acceptance
1. `python3 scripts/scrape.py` → `data/<today>/trends.json` with ≥10 topics
   from ≥2 sources, exit 0.
2. One full cron tick → draft thread in `#specs` (or designated review
   channel), under 280 chars/tweet.
3. `bash tools/check_pii.sh --all` clean; README touched; pushed to
   `0x-m-dev/trend-threads` as `0x-m-dev`; `#deploy-log` ship post sent.
4. No secrets, no hardcoded channel IDs (registry via shared helper),
   `studio.py validate` passes.
