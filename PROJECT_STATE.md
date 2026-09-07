# Project State

## Objective
Publish a concise, sourced daily ICYMI post from real trending topics.

## Current state
- Registered as an active Hermes Studio project.
- Daily cron `0be930b365c6` (8:00 AM PDT) now includes article summaries + shitpost mock (headliner, take + link per story) and delivers to `#trend-threads`.
- The daily cron is pinned to `xai-oauth / grok-4.6`; no fallback providers are configured, so rate limits fail closed rather than switching to Qwen.
- Project workspace: Discord `#trend-threads` and the Trend Threads Desktop Project.
- Preview: https://0x-m-dev.github.io/trend-threads/
- Repository: https://github.com/0x-m-dev/trend-threads
- Sep 6 mock post is a shitpost headliner plus per-story take + link.

## Decisions
- Keep research and generation in the project workspace, not `#command-center`.
- Ship one useful post rather than a long generic thread.
- Preserve source URLs and verify claims before delivery.
- Mock post shape: one headliner for the day's stack, then each story as a self-contained take with its source link. Voice is shitpost, not LLM recap.

## Next actions
1. Review the Sep 6 mock for voice and whether each take stands without the article.
2. Improve extractive summaries only when a real output is too thin or wrong.

## Blockers
- The next run should be observed after the xAI rate-limit window; do not run it manually merely to clear the previous drift error.

## Last verified
2026-09-07 10:24 PDT
