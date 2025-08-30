from pydantic import BaseSettings, Field
from typing import List, Set

class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")

    MAX_CHARS: int = 10_000
    MAX_UPLOAD_MB: int = 5
    REQUEST_TIMEOUT_S: int = 20

    ALLOWED_ORIGINS_RAW: str = ""

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [o.strip() for o in silf.ALLOWED_ORIGINS_RAW.split(",") if o.strip()]

    ALLOWED_MIME: Set(str) = {"text/plain", "application/pdf"}
    ALLOWERD_EXT: Set(str) = {".txt", ".pdf"}

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()