import os
from io import BytesIO
from typing import Optional, Tuple
from pypdf import PdfReader
from fastapi import UploadFile
from app.core.settings import settings

def _truncate(s: str, limit: int) -> str:
    return s if len(s) <= limit else s[:limit] + f"[...truncated at {limit} chars]"

def extract_text_from_upload(file: UploadFile, data: Optional[bytes] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Retorna (texto, aviso). Usa settings.MAX_CHARS internamente.
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
            remaining = settings.MAX_CHARS
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
                content += f'[...File "{name}" truncated at {settings.MAX_CHARS} characters]'
            return content, None
        except Exception as e:
            return None, f"Erro ao ler PDF: {e}"

    # Trata como texto (txt, csv, md, etc.)
    try:
        text = data.decode("utf-8", errors="ignore")
        if len(text) > settings.MAX_CHARS:
            text = text[:settings.MAX_CHARS] + f"[...truncated at {settings.MAX_CHARS} chars]"
        return text, None
    except Exception as e:
        return None, f"Erro ao ler texto: {e}"