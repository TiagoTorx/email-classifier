from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Set

class Settings(BaseSettings):
    GEMINI_API_KEY: str

    MAX_CHARS: int = 10_000
    MAX_UPLOAD_MB: int = 5
    REQUEST_TIMEOUT_S: int = 20

    ALLOWED_ORIGINS_RAW: str = ""

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS_RAW.split(",") if o.strip()]

    ALLOWED_MIME: set[str] = {"text/plain", "application/pdf"}
    ALLOWED_EXT: set[str] = {".txt", ".pdf"}

    @property
    def MAX_UPLOAD_BYTES(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    model_config = SettingsConfigDict(env_file = ".env", case_sensitive = True)

settings = Settings()