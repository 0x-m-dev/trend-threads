# Trend Threads

Hermes-managed project. Read `SPEC.md`, `PROJECT.yaml`, and `AGENTS.md` before making significant changes.

## Pipeline (daily cron)

```bash
python3 scripts/scrape.py   # → data/<date>/trends.json (≥10 trends from ≥2 sources)
python3 scripts/draft.py    # → data/<date>/thread.md (5–7 tweet draft)
python3 scripts/deliver.py  # → prints review message to stdout (for Hermes cron agent)
```

## Commands

```bash
make test    # Run tests
make lint    # Python syntax check
make build   # Validate + test
```

## Structure

- `scripts/scrape.py` — Multi-source trend fetcher (HN, RSS feeds, Google Trends)
- `scripts/draft.py` — Cluster trends → 5-7 tweet thread draft
- `scripts/deliver.py` — Format draft as Discord-ready review message
- `scripts/render.py` — Render day's draft + topics to `docs/` (GitHub Pages)
- `tests/test_trend_threads.py` — Tests for all scripts
- `tools/check_pii.sh` — PII/secret gate (pre-commit + pre-push)
- `tools/check_readme_push.sh` — README freshness gate (pre-push)
- `tools/install-hooks.sh` — Install git hooks
- `data/<date>/trends.json` — Raw scraped trends
- `data/<date>/thread.md` — Drafted thread for the day

## Site

Free hosting via GitHub Pages (serves `docs/`): https://0x-m-dev.github.io/trend-threads/
Regenerate: `python3 scripts/render.py [YYYY-MM-DD]`, commit, push. Drafts still
reviewed in #trend-threads before anything is posted to X.

## Pipeline Output

Last verified run: ✅ 14 topics from 2 sources (HN + news RSS; Reddit blocks
bots, Google Trends best-effort).
