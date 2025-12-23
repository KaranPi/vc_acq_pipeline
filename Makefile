.PHONY: help venv install install-scraping install-nlp install-reporting lint test run-dry freeze clean

VENV_DIR ?= .venv

ifeq ($(OS),Windows_NT)
	VENV_BIN := $(VENV_DIR)/Scripts
else
	VENV_BIN := $(VENV_DIR)/bin
endif

PIP := $(VENV_BIN)/pip
PY := $(VENV_BIN)/python


help:
	@echo "Targets:"
	@echo "  make venv              Create venv"
	@echo "  make install           Install base + dev deps"
	@echo "  make install-scraping  Install scraping extras"
	@echo "  make install-nlp       Install NLP extras"
	@echo "  make install-reporting Install reporting extras"
	@echo "  make lint              Run ruff"
	@echo "  make test              Run pytest"
	@echo "  make run-dry           Run CLI in dry mode"
	@echo "  make freeze            Generate pinned lockfile (pip-tools)"
	@echo "  make clean             Remove caches"

venv:
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements/base.txt -r requirements/dev.txt

install-scraping: venv
	$(PIP) install -r requirements/scraping.txt
	@echo "Installing Playwright browsers (required once)..."
	$(PY) -m playwright install

install-nlp: venv
	$(PIP) install -r requirements/nlp.txt

install-reporting: venv
	$(PIP) install -r requirements/reporting.txt

lint: venv
	$(PY) -m ruff check src tests

test: venv
	$(PY) -m pytest -q

run-dry: venv
	$(PY) -m acq_pipeline run --dry

freeze: venv
	@echo "Generating requirements.lock.txt from base+extras (edit as needed)..."
	$(PY) -m piptools compile \
		--output-file requirements.lock.txt \
		requirements/base.txt \
		requirements/scraping.txt \
		requirements/nlp.txt \
		requirements/reporting.txt \
		requirements/dev.txt

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__
