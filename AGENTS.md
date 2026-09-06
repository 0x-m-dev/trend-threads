# Agent Instructions

## Required context

Read `SPEC.md`, `PROJECT.yaml`, `PROJECT_STATE.md`, and this file before
significant work. At the end of meaningful work, update `PROJECT_STATE.md`
with verified state, decisions, next actions, blockers, and timestamp. Keep it
factual and under 100 lines so fresh chats can resume without replaying history.

## Definition of done

- Changes satisfy the relevant SPEC acceptance criteria.
- `make fmt`, `make lint`, `make test`, and `make build` pass.
- No secrets are committed.
- Migrations are reviewed before deployment.
- Production changes require explicit approval.

## Forbidden

- Never commit `.env` or production credentials.
- Never drop production data or deploy blindly.
- Never bypass failing validation without documenting why.
