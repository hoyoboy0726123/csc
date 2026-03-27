import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database.connection import engine
from backend.database.init_db import init_db
from backend.routers import auth, upload, prd, code, fix
from backend.utils.config import settings
from backend.utils.exceptions import V2CException, v2c_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Voice-to-Code Pipeline",
    description="從語音構思到可執行代碼的自動化流水線",
    version="v1.0-MVP",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(V2CException, v2c_exception_handler)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(prd.router, prefix="/api/v1/prd", tags=["prd"])
app.include_router(code.router, prefix="/api/v1/code", tags=["code"])
app.include_router(fix.router, prefix="/api/v1/fix", tags=["fix"])

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return {"message": "Voice-to-Code Pipeline API v1.0-MVP"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)