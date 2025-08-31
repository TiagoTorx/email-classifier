# Email Classifier (FastAPI + Gemini)

Classificador simples de emails/documentos (produtivo x improdutivo) com UI mínima (Jinja + JS) e backend em FastAPI usando **Google Gemini**.

## O que o app faz
- Cola **texto** ou envia **.txt/.pdf** (PDF pesquisável).
- Extrai texto (`pypdf`), limita tamanho e chama o **Gemini** com um *prompt* de sistema.
- Exibe: **categoria** (produtivo/improdutivo), **subtipo**, **confiança**, **motivos**, **resposta sugerida** e o **JSON bruto**.
- UI simples, com **pré-visualização** do texto e **preview de PDF** embutido.

## Stack
- **Backend**: FastAPI + Uvicorn/Gunicorn
- **AI**: `google-genai` (Gemini 2.0 Flash)
- **Templates**: Jinja + JS/Fetch
- **PDF**: `pypdf`
- **Config**: `pydantic-settings`
- **Tests**: `pytest`
- **Deploy**: Docker + Cloud Run

## Rodando localmente (setup rápido)

Requisitos: **Python 3.10+**, `git`, `make` (opcional).

```bash
# 1) clone
git clone https://github.com/<seu-usuario>/email-classifier.git
cd email-classifier

# 2) venv + deps
make setup
# (ou manualmente)
# python -m venv .venv && source .venv/bin/activate
# pip install -U pip wheel
# pip install -r requirements.txt -r requirements-dev.txt

# 3) .env
cp .env.example .env  # se existir; senão crie
# edite e defina:
# GEMINI_API_KEY="sua-chave"
# ALLOWED_ORIGINS_RAW="http://localhost:8000,http://127.0.0.1:8000"
# MAX_UPLOAD_MB=5
# REQUEST_TIMEOUT_S=20

# 4) subir
make dev
# abra http://127.0.0.1:8000
```
## Variáveis de ambiente principais
```
GEMINI_API_KEY (obrigatória)
ALLOWED_ORIGINS_RAW (lista separada por vírgula; ex: http://localhost:8000,http://127.0.0.1:8000)
MAX_UPLOAD_MB (padrão 5)
REQUEST_TIMEOUT_S (padrão 20)
```
## Testes
```
make test
# ou: .venv/bin/pytest -q
```

## Docker (opcional)
```
docker build -t email-classifier:local .
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=seu_token \
  -e ALLOWED_ORIGINS_RAW="http://localhost:8080" \
  email-classifier:local
# abra http://localhost:8080
```

## Observações

- PDFs escaneados (imagem) podem não ter texto extraível; o app retorna um fallback explicando.

- Se você viu ModuleNotFoundError: No module named 'app', quase sempre é: (1) rodou fora da raiz do projeto, (2) não ativou a venv, (3) misturou versões de Python. Execute os comandos na raiz e ative a venv.


- Para CORS, garanta que o ALLOWED_ORIGINS_RAW contém o host de onde você acessa.
