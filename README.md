# Trend Threads

Hermes-managed project. Read `SPEC.md`, `PROJECT.yaml`, `PROJECT_STATE.md`, and
`AGENTS.md` before making significant changes. Keep `PROJECT_STATE.md` current
so a fresh chat can resume without replaying old conversations.

## Pipeline (daily cron)

```bash
python3 scripts/scrape.py   # → data/<date>/trends.json (≥10 trends from ≥2 sources)
python3 scripts/draft.py    # → data/<date>/icumi.md + icumi.json (summaries + mock X post)
python3 scripts/deliver.py  # → prints ICUMI review message to stdout (for Hermes cron agent)
python3 scripts/render.py   # → docs/<date>/index.html (GitHub Pages, includes tweet mock)
```

## Commands

```bash
make test    # Run tests
make lint    # Python syntax check
make build   # Validate + test
```

## Structure

- `scripts/scrape.py` — Multi-source trend fetcher (HN, Reddit, RSS, Google Trends) + X tweet lookup via firecrawl
- `scripts/summarize.py` — Fetches each article, extracts a 1–2 sentence recap, builds copy-ready mock X posts
- `scripts/draft.py` — Picks top topic as ICUMI highlight, writes summaries + mock post + X refs
- `scripts/deliver.py` — Formats ICUMI post as Discord-ready review message (includes mock post)
- `scripts/render.py` — Renders ICUMI JSON to styled HTML docs (GitHub Pages, tweet-card mock)
- `tests/test_trend_threads.py` — Tests for all scripts
- `tools/check_pii.sh` — PII/secret gate (pre-commit + pre-push)
- `tools/check_readme_push.sh` — README freshness gate (pre-push)
- `tools/install-hooks.sh` — Install git hooks
- `data/<date>/trends.json` — Raw scraped trends
- `data/<date>/icumi.md` — ICUMI post for the day
- `data/<date>/icumi.json` — Structured ICUMI data (highlight, related, X refs)

## ICUMI Format

Each day produces a single "In Case You Missed It" post with:
- **🔥 Highlight** — top-scoring trend with points and source link
- **📌 Also trending** — 4 diverse related topics with HN points and URLs
- **🐦 Mock post** — shitpost headliner for the day's stack, then each story as a self-contained take + source link (plus a 280-char hook)
- **🧠 Article summaries** — 1–2 sentence recap per source link
- **🐦 On X** — top X tweet links per topic (via firecrawl search)
- Archive link to full history

## Site

Deployed via GitHub Actions on every push to main (`.github/workflows/pages.yml`).
Free hosting via GitHub Pages (serves `docs/`): https://0x-m-dev.github.io/trend-threads/
Regenerate: `python3 scripts/render.py [YYYY-MM-DD]`, commit, push. Drafts still
reviewed in #trend-threads before anything is posted to X.

## Pipeline Output

Last verified run: ✅ Sep 6 mock rewritten as shitpost headliner + per-story take/link (1312 chars, 5 source URLs)
