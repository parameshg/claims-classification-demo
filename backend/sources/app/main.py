from fastapi import FastAPI
from app import handlers
from app.routes import claims

app = FastAPI(title="Motor Claims Agent API", version="1.0.0")

handlers.attach(app)

app.include_router(claims.router, prefix="/api/v1")