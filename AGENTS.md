# Agent Instructions

## Required context

Read `SPEC.md`, `PROJECT.yaml`, and this file before significant work.

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
