from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.core.middleware import add_request_id_middleware, add_timeout_middleware
from app.core.logging import setup_logging
from app.api.routes import router
from app.services.gemini import make_client, classify_with_timeout as _classify_with_timeout

def create_app() -> FastAPI:
    app = FastAPI(title="Email/Doc Classifier")

    app.state.settings = settings
    app.state.logger = setup_logging()
    app.state.gemini_client = make_client(settings.GEMINI_API_KEY)

    app.state.classify = _classify_with_timeout

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["authorization", "content-type"],
    )

    add_request_id_middleware(app)
    add_timeout_middleware(app, settings.REQUEST_TIMEOUT_S)

    app.include_router(router)

    return app

app = create_app()