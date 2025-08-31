# --------- Config ---------
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# --------- Tarefas ---------

# Cria venv e instala tudo (app + dev)
setup: $(VENV)/bin/activate
	$(PIP) install -U pip wheel
	$(PIP) install -e ".[dev]"

# Só instala as deps (se a venv já existir)
install:
	$(PIP) install -e ".[dev]"

# Sobe o servidor em modo dev (reload)
dev:
	$(PY) -m uvicorn main:app --reload --port 8000

# Testes
test:
	$(PY) -m pytest

# Cobertura
cov:
	$(PY) -m pytest --cov=app --cov=main --cov-report=term-missing

# Lint (checagem)
lint:
	$(VENV)/bin/ruff check .

# Format (autoformatação)
format:
	$(VENV)/bin/ruff format .
	$(VENV)/bin/black .

# Limpa caches
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .coverage

# --------- Internals ---------
$(VENV)/bin/activate:
	python -m venv $(VENV)
	@echo "venv criada em $(VENV). Use: source $(VENV)/bin/activate"
