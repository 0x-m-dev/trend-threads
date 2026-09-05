.PHONY: dev fmt lint test build migrate deploy

dev:
	@echo "Trend Threads — run scripts/scrape.py → scripts/draft.py → scripts/deliver.py"
fmt:
	@echo "No formatter — Python stdlib only"
lint:
	@python3 -m py_compile scripts/*.py
test:
	@python3 -m pytest tests/ -v
build:
	@echo "Build: no compilation, just validate"
	@python3 -m py_compile scripts/*.py
	@python3 -m pytest tests/ -v
migrate:
	@echo "No migrations — stdlib only"
deploy:
	@echo "Deployment is gated; use Hermes /preview or /ship"
