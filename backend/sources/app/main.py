import handlers
from dotenv import load_dotenv
from fastapi import FastAPI
from routes import claims, customers, policies

load_dotenv(override=True)
app = FastAPI(title="Motor Claims Agent API", version="1.0.0")
handlers.attach(app)

app.include_router(claims.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")