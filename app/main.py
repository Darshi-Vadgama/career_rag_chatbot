import os
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.services.auth_service import init_db

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB init
    init_db()
    # Warm up Ollama so first user request is instant
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": "qwen2.5:7b",
                "prompt": "hi",
                "stream": False,
                "keep_alive": "60m"
            })
        print("✅ Ollama model warmed up")
    except Exception as e:
        print(f"⚠️ Ollama warmup failed (will be slow on first request): {e}")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)