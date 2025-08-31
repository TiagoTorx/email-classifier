import os
from app.api.schemas import ClassificationResponse

def test_index_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Classificador " in r.text

def test_healthz_ok(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

# text
def test_classify_text_sucess(client, monkeypatch):
    async def fake_classify_with_timeout(_client, _prompt, text, secs = 15):
        return ClassificationResponse(
            category = "produtivo",
            subtype = "orcamento",
            confidence = 0.91,
            summary = "ok",
            reasons = ["r1"],
            suggested_reply = "Responder com proposta"
        )
    monkeypatch.setattr(
        "app.services.gemini.classify_with_timeout",
        fake_classify_with_timeout,
    )

    r = client.post("/classify-text", data={"text": "conteúdo de teste"})
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "produtivo"
    assert "X-Request-ID" in r.headers

def test_classify_text_empty(client):
    r = client.post("/classify-text", data={"text": " "})
    assert r.status_code == 400
    assert "Texto vazio" in r.text

# file
def test_classify_file_supported_mime(client):
    files = {"file": ("img.png", b"\x89PNG", "Image/png")}
    r = client.post("/classify-file", files=files)
    assert r.status_code == 415

def test_classify_file_too_large(client, monkeypatch):
    monkeypatch.setattr(client.app.state.settings, "MAX_UPLOAD_MB", 1, raising=False)
    big = b"x" * (2 * 1024 * 1024)
    files = {"file": ("big.txt", big, "text/plain")}
    r = client.post("/classify-file", files=files)
    assert r.status_code == 413
    assert str(1) in r.text

def test_classify_file_extract_ok(client, monkeypatch):
    async def fake_classify_with_timeout(_client, _prompt, text, secs=15):
        return ClassificationResponse(
            category="produtivo",
            subtype="orcamento",
            confidence=0.9,
            summary="texto do arquivo ok",
            reasons=["extraído com sucesso"],
            suggested_reply="Responder com orçamento"
        )
    monkeypatch.setattr(
        "app.services.gemini.classify_with_timeout",
        fake_classify_with_timeout,
    )

    def fake_extract_text_from_upload(file, data=None):
        return "texto vindo do arquivo", None
    monkeypatch.setattr(
        "app.services.extractor.extract_text_from_upload",
        fake_extract_text_from_upload,
    )

    files = {"file": ("a.txt", b"qualquer", "text/plain")}
    r = client.post("/classify-file", files=files)
    assert r.status_code == 200
    assert r.json()["category"] == "produtivo"

def test_classify_file_extract_fallback_improdutivo(client, monkeypatch):
    def fake_extract_text_from_upload(file, data=None):
        return None, "Não consegui extrair"
    monkeypatch.setattr(
        "app.services.extractor.extract_text_from_upload",
        fake_extract_text_from_upload,
    )

    files = {"file": ("a.pdf", b"%PDF-1.7", "application/pdf")}
    r = client.post("/classify-file", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "improdutivo"
    assert any("Não consegui" in x for x in body["reasons"])