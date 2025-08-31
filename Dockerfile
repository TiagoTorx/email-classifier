FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# Dependências do sistema (opcional; o pypdf não costuma exigir libs nativas)
# RUN apt-get update -y && apt-get install -y --no-install-recommends \
#   && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Cloud Run usa $PORT; deixe default 8080
ENV PORT=8080

# Gunicorn com UvicornWorker (2 workers é um bom começo)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8080", "main:app"]
