# Implementation Plan

## Phase 1: ✅ Complete (2026-09-05)
- [x] Bootstrap project structure (scripts/, tests/, tools/)
- [x] `scripts/scrape.py` — Multi-source fetch (HN, BBC, TechCrunch, The Verge, Google Trends)
- [x] `scripts/draft.py` — Trend clustering + 5-7 tweet thread drafting
- [x] `scripts/deliver.py` — Discord-ready review message output
- [x] `tests/test_trend_threads.py` — 8 tests, all passing
- [x] Git hooks installed (pre-commit: PII + syntax; pre-push: PII + README)
- [x] Makefile, README, PROJECT.yaml aligned with Python/stdlib architecture
- [x] Pipeline verified end-to-end (scrape → draft → deliver)
- [x] Pushed to `0x-m-dev/trend-threads`

## Phase 2: Next
- [ ] Set up daily cron job via `hermes cron` (morning execution)
- [ ] Connect `deliver.py` output to `#specs` Discord channel
- [ ] Add Google Trends API key support (when available)
- [ ] Expand RSS sources (add more tech/news feeds)

## Phase 3: Future
- [ ] Thread rating system (human feedback on drafted threads)
- [ ] Topic history tracking across days
- [ ] Auto-skip low-quality topics (spam, clickbait detection)
- [ ] Multi-thread generation (pick top 2 clusters instead of 1)
