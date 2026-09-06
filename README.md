# Trend Threads

Hermes-managed project. Read `SPEC.md`, `PROJECT.yaml`, `PROJECT_STATE.md`, and
`AGENTS.md` before making significant changes. Keep `PROJECT_STATE.md` current
so a fresh chat can resume without replaying old conversations.

## Pipeline (daily cron)

```bash
python3 scripts/scrape.py   # → data/<date>/trends.json (≥10 trends from ≥2 sources)
python3 scripts/draft.py    # → data/<date>/icumi.md + icumi.json (single ICUMI post with X refs)
python3 scripts/deliver.py  # → prints ICUMI review message to stdout (for Hermes cron agent)
python3 scripts/render.py   # → docs/<date>/index.html (GitHub Pages)
```

## Commands

```bash
make test    # Run tests
make lint    # Python syntax check
make build   # Validate + test
```

## Structure

- `scripts/scrape.py` — Multi-source trend fetcher (HN, Reddit, RSS, Google Trends) + X tweet lookup via firecrawl
- `scripts/draft.py` — Picks top topic as ICUMI highlight, cross-refs X tweets, writes single-sweet post
- `scripts/deliver.py` — Formats ICUMI post as Discord-ready review message
- `scripts/render.py` — Renders ICUMI JSON to styled HTML docs (GitHub Pages)
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
- **🐦 On X** — top X tweet links per topic (via firecrawl search)
- Archive link to full history

## Site

Deployed via GitHub Actions on every push to main (`.github/workflows/pages.yml`).
Free hosting via GitHub Pages (serves `docs/`): https://0x-m-dev.github.io/trend-threads/
Regenerate: `python3 scripts/render.py [YYYY-MM-DD]`, commit, push. Drafts still
reviewed in #trend-threads before anything is posted to X.

## Pipeline Output

Last verified run: ✅ ICUMI post drafted with X cross-refs (QBittorrent 1042 pts highlight, 3 topics with X tweet links)
