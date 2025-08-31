FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# Instala deps do projeto
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o app
COPY . .

# Cloud Run injeta $PORT; mantenha default 8080
ENV PORT=8080
# Envia logs do gunicorn para stdout/stderr (Cloud Logging)
ENV GUNICORN_CMD_ARGS="--access-logfile - --error-logfile -"

# Use sh -c para expandir ${PORT} e ${WEB_CONCURRENCY} (opcional)
# WEB_CONCURRENCY controla quantos workers (default 2)
CMD ["sh", "-c", "exec gunicorn -k uvicorn.workers.UvicornWorker -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-8080} main:app"]
