# main.py
import os, json, time, uuid, asyncio

import logging

from io import BytesIO
from typing import Tuple, Optional

from fastapi import FastAPI, UploadFile, File, Form, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader

from prompts import system_prompt

# ------------------ Config ------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Defina GEMINI_API_KEY no .env")

# ----------- Limits and timeouts ------------
MAX_CHARS = 10_000
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
REQUEST_TIMEOUT_S = int(os.getenv("REQUEST_TIMEOUT_S", "20"))

# ------------------ CORS ------------------
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
# ------------------ Tipos permitidos ------------------
ALLOWED_MIME = {"text/plain", "application/pdf"}
ALLOWED_EXT  = {".txt", ".pdf"}

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="Email/Doc Classifier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or [],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["authorization", "content-type"],
)

templates = Jinja2Templates(directory="templates")

# ------------------ Logging ------------------
logger = logging.getLogger("app")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.setLevel(logging.INFO)
logger.addHandler(handler)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.rid = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.rid
    return response

@app.middleware("http")
async def timeout_mw(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_S)
    except asyncio.TimeoutError:
        return JSONResponse({"detail": "Request timeout"}, status_code=504)

# evita 404 no log
@app.get("/favicon.ico", include_in_schema = False)
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}

# ------------------ Models ------------------
class ClassificationResponse(BaseModel):
    category: str
    subtype: str
    confidence: float
    summary: str
    reasons: list[str]
    suggested_reply: str

# ------------------ Utils ------------------
def _truncate(s: str, limit: int) -> str:
    return s if len(s) <= limit else s[:limit] + f"[...truncated at {limit} chars]"

def extract_text_from_upload(file: UploadFile, data: Optional[bytes] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Retorna (texto, aviso). Se 'data' for fornecido, usa-o (evita reler do UploadFile).
    """
    name = (file.filename or "").lower()
    ext = os.path.splitext(name)[1]

    if data is None:
        data = file.file.read()
    if not data:
        return None, "Arquivo vazio."

    if ext == ".pdf" or file.content_type == "application/pdf":
        try:
            reader = PdfReader(BytesIO(data))
            remaining = MAX_CHARS
            parts: list[str] = []
            for page in reader.pages:
                if remaining <= 0:
                    break
                text = page.extract_text() or ""
                if not text.strip():
                    # pode ser scaneado/imagem
                    continue
                if len(text) > remaining:
                    parts.append(text[:remaining])
                    remaining = 0
                    break
                parts.append(text)
                remaining -= len(text)
            content = "".join(parts).strip()
            if not content:
                return None, "Não foi possível extrair texto. O PDF pode ser scaneado (imagem)."
            if remaining <= 0:
                content += f'[...File "{name}" truncated at {MAX_CHARS} characters]'
            return content, None
        except Exception as e:
            return None, f"Erro ao ler PDF: {e}"

    # Trata como texto (txt, csv, md, etc.)
    try:
        text = data.decode("utf-8", errors="ignore")
        return _truncate(text, MAX_CHARS), None
    except Exception as e:
        return None, f"Erro ao ler texto: {e}"

def classify_text_with_gemini(text: str) -> ClassificationResponse:
    """
    Garante retorno 100% JSON usando response_mime_type.
    """
    req = types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=system_prompt
    )
    res = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=[types.Content(role="user", parts=[types.Part(text=text)])],
        config=req
    )
    # A API devolve .text como JSON puro quando usamos response_mime_type
    data = json.loads(res.text)
    return ClassificationResponse(**data)

async def classify_with_timeout(text: str, secs: int = 15) -> ClassificationResponse:
    """Executa a chamada síncrona à IA em threadpool e aplica timeout."""
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, classify_text_with_gemini, text),
        timeout=secs,
    )

def log_classification(request: Request, source: str, input_bytes: int, res: ClassificationResponse, note: Optional[str] = None) -> None:
    logger.info(json.dumps({
        "ts": int(time.time()),
        "rid": getattr(request.state, "rid", None),
        "source": source,
        "input_bytes": input_bytes,
        "category": res.category,
        "subtype": res.subtype,
        "confidence": round(res.confidence, 3),
        "truncated": ("truncated" in " ".join(res.reasons).lower()),
        "note": note,
    }))

# ------------------ Routes ------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "max_upload_mb": MAX_UPLOAD_MB}
    )

@app.post("/classify-text", response_model=ClassificationResponse)
async def classify_text_endpoint(request: Request, text: str = Form(...)):
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail= "Texto vazio.")
        text = _truncate(text, MAX_CHARS)
        result = await classify_with_timeout(text, secs=15)
        log_classification(request, "text", len(text.encode("utf-8")), result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao classificar: {e}")

@app.post("/classify-file", response_model=ClassificationResponse)
async def classify_file_endpoint(request: Request, file: UploadFile = File(...)):
    data: bytes = b""
    try:
        ext = os.path.splitext((file.filename or "").lower())[1]
        if (file.content_type not in ALLOWED_MIME) or (ext not in ALLOWED_EXT):
            raise HTTPException(status_code=415, detail="Tipo não suportado. Envie .txt ou .pdf")

        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Arquivo vazio.")
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"Arquivo excede {MAX_UPLOAD_MB} MB")

        text, note = extract_text_from_upload(file, data=data)
        if not text:
            # Trata PDF scaneado ou erro de leitura como improdutivo com dica de reenvio
            fallback = ClassificationResponse(
                category="improdutivo",
                subtype="outro",
                confidence=0.4,
                summary="Arquivo não legível automaticamente",
                reasons=["Falha de extração de texto", note or "Formato não suportado"],
                suggested_reply="Não consegui ler o arquivo enviado. Poderia reenviar como PDF pesquisável ou colar o texto no corpo da mensagem?"
            )
            log_classification(request, "file", len(data), fallback, note)
            return fallback

        result = await classify_with_timeout(text, secs = 15)
        if note:
            result.reasons = result.reasons + [note]
        log_classification(request, "file", len(data), result, note)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao classificar arquivo: {e}")
