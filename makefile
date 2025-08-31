PYTHON ?= python3
VENV := .venv
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
PYTEST := $(VENV)/bin/pytest

help:
	@echo "make setup     -> cria venv e instala deps"
	@echo "make dev       -> roda o servidor em reload (http://127.0.0.1:8000)"
	@echo "make test      -> executa pytest"
	@echo "make clean     -> remove caches"
	@echo "make clean-venv-> remove .venv"

setup:
	$(PYTHON) -m venv $(VENV)
	@echo "venv criada em $(VENV). Use: source $(VENV)/bin/activate"
	$(PIP) install -U pip wheel
	$(PIP) install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi

dev:
	$(UVICORN) main:app --reload --port 8000

test:
	$(PYTEST) -q

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ */__pycache__ .coverage

clean-venv:
	rm -rf $(VENV)
