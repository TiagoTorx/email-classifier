from pydantic import BaseModel

class ClassificationResponse(BaseModel):
    category: str
    subtype: str
    confidence: float
    summary: str
    reasons: list[str]
    suggested_reply: str