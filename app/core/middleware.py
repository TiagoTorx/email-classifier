import uuid, asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def add_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.rid = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.rid
        return response

def add_timeout_middleware(app: FastAPI, timeout_seconds: int) -> None:
    @app.middleware("http")
    async def timeout_mw(request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return JSONResponse({"detail": "Request timeout"}, status_code=504)


