import json, asyncio
from google import genai
from google.genai import types
from app.api.schemas import ClassificationResponse

def make_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)

def classify_text_with_gemini(client: genai.Client, system_prompt: str, text: str) -> ClassificationResponse:
    req = types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=system_prompt
    )
    res = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=[types.Content(role="user", parts=[types.Part(text=text)])],
        config=req
    )
    data = json.loads(res.text)
    return ClassificationResponse(**data)

async def classify_with_timeout(client: genai.Client, system_prompt: str, text: str, secs: int = 15) -> ClassificationResponse:
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, classify_text_with_gemini, client, system_prompt, text),
        timeout=secs
    )