from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.fault import Fault

def body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}

def attach(app: FastAPI) -> None:
    @app.exception_handler(Fault)
    async def on_fault(_: Request, exc: Fault) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def on_invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"] if p not in ("body", "query"))
        message = f"{where}: {first['msg']}" if where else first["msg"]
        return JSONResponse(status_code=400, content=body("invalid_request", message))