# Project State

## Objective
Publish a concise, sourced daily ICYMI post from real trending topics.

## Current state
- Registered as an active Hermes Studio project.
- Daily cron `0be930b365c6` (8:00 AM PDT) includes article summaries + shitpost mock (headliner, take + link per story) and delivers to `#trend-threads`.
- The daily cron is pinned to `xai-oauth / grok-4.6`; no fallback providers are configured, so rate limits fail closed rather than switching to Qwen.
- Project workspace: Discord `#trend-threads` and the Trend Threads Desktop Project.
- Preview: https://0x-m-dev.github.io/trend-threads/
- Repository: https://github.com/0x-m-dev/trend-threads
- Oct 5 mock: Denmark CPR dump 8.8M (305), RobCo $1B unicorn (231), Cloudflare Web Search API (165), GrapheneOS may skip Pixel 11 (135), Huawei/Qualcomm patent deal (107).

## Decisions
- Keep research and generation in the project workspace, not `#command-center`.
- Ship one useful post rather than a long generic thread.
- Preserve source URLs and verify claims before delivery.
- Mock post shape: one headliner for the day's stack, then each story as a self-contained take with its source link. Voice is shitpost, not LLM recap.

## Next actions
1. Review the Oct 5 mock for voice and whether each take stands without the article.
2. Improve extractive summaries only when a real output is too thin or wrong (PDF fetch still dumps binary).
3. Reddit scrape still 403s; HN + news RSS were enough for the >=10 / >=2 source bar.

## Blockers
- Reddit hot returns HTTP 403. Pipeline still met scrape acceptance via HN + news RSS.

## Last verified
2026-10-05 08:00 PDT
