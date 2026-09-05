# Trend Threads — Dockerfile

FROM python:3.12-slim

WORKDIR /app

COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY .gitignore Makefile README.md ./

RUN pip install --no-cache-dir pytest

# Cron job runs scrape → draft → deliver
ENTRYPOINT ["python3", "-c", "from scripts.scrape import main as s; import sys; sys.exit(s()) && python3 scripts/draft.py && python3 scripts/deliver.py"]

# Usage:
#   docker run trend-threads   # Runs full pipeline
#   docker run pytest tests/   # Run tests
