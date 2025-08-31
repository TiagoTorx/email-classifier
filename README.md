# Email Classifier (FastAPI + Gemini)

Classificador simples de emails/documentos (produtivo x improdutivo) com UI mínima (Jinja + JS) e backend em FastAPI usando **Google Gemini**.

## Requisitos

- Python 3.10+ (recomendado 3.13)
- `git`, `make` (opcional, mas facilita)

## Setup rápido

```bash
# 1) clone
git clone <seu-repo> email-classifier
cd email-classifier

# 2) crie .venv e instale deps
make setup

# 3) crie o .env
cp .env.example .env  # se existir; senão crie manualmente
# edite .env e defina pelo menos:
# GEMINI_API_KEY="sua-chave"
# ALLOWED_ORIGINS_RAW="http://localhost:8000, http://127.0.0.1:8000"

# 4) rode em modo dev
make dev
# abra http://127.0.0.1:8000
