# tests/conftest.py
import os
import pytest
from starlette.testclient import TestClient
from main import create_app
from app.api.schemas import ClassificationResponse

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    app = create_app()

    async def fake_classify(_client, _sys_prompt, text, secs=15):
        return ClassificationResponse(
            category="produtivo",
            subtype="teste",
            confidence=0.99,
            summary=(text or "")[:40],
            reasons=["stubbed"],
            suggested_reply="ok",
        )

    app.state.classify = fake_classify
    return TestClient(app)