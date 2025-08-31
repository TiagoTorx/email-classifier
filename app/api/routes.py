import os
import app.services.extractor as extractor
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from app.api.schemas import ClassificationResponse
from app.core.settings import settings
from app.core.logging import log_classification
from prompts import system_prompt

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "max_upload_mb": settings.MAX_UPLOAD_MB,
            "max_chars": settings.MAX_CHARS,
        },
    )

@router.get("/favicon.ico", include_in_schema = False)
def favicon():
    return Response(status_code=204)

@router.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}

@router.post("/classify-text", response_model=ClassificationResponse)
async def classify_text_endpoint(request: Request, text: str = Form(...)):
        if not text.strip():
            raise HTTPException(status_code=400, detail= "Texto vazio.")
        text = text if len(text) <= settings.MAX_CHARS else text [:settings.MAX_CHARS] + f"[...truncated at {settings.MAX_CHARS} chars]"
        result = await request.app.state.classify(request.app.state.gemini_client, system_prompt, text, secs=15)
        log_classification(request.app.state.logger,request , "text", len(text.encode("utf-8")), result)
        return result

@router.post("/classify-file", response_model=ClassificationResponse)
async def classify_file_endpoint(request: Request, file: UploadFile = File(...)):
    ext = os.path.splitext((file.filename or "").lower())[1]
    if (file.content_type not in settings.ALLOWED_MIME) or (ext not in settings.ALLOWED_EXT):
        raise HTTPException(status_code=415, detail="Tipo não suportado. Envie .txt ou .pdf")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Arquivo excede {settings.MAX_UPLOAD_MB} MB")

    text, note = extractor.extract_text_from_upload(file, data=data)
    if not text:
        fallback = ClassificationResponse(
            category="improdutivo",
            subtype="outro",
            confidence=0.4,
            summary="Arquivo não legível automaticamente",
            reasons=["Falha de extração de texto", note or "Formato não suportado"],
            suggested_reply="Não consegui ler o arquivo enviado. Poderia reenviar como PDF pesquisável ou colar o texto no corpo da mensagem?"
        )
        log_classification(request.app.state.logger, request, "file", len(data), fallback, note)
        return fallback

    result = await request.app.state.classify(request.app.state.gemini_client, system_prompt, text, secs=15)
    if note:
        result.reasons = result.reasons + [note]
    log_classification(request.app.state.logger, request, "file", len(data), result, note)
    return result