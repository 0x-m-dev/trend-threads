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
- `tests/test_trend_threads.py` — Tests for all scripts
- `tools/check_pii.sh` — PII/secret gate (pre-commit + pre-push)
- `tools/check_readme_push.sh` — README freshness gate (pre-push)
- `tools/install-hooks.sh` — Install git hooks
- `data/<date>/trends.json` — Raw scraped trends
- `data/<date>/thread.md` — Drafted thread for the day

## Pipeline Output

Today's run: ✅ 85 trends from 4 sources (HN, BBC, The Verge, TechCrunch)
