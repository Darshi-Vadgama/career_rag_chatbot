# app/main.py
# FULL UPDATED MAIN WITH LOGGING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.routes import router
from app.utils.logger import logger

# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

logger.info("Environment Loaded")


# =====================================================
# APP
# =====================================================
app = FastAPI(
    title="Career AI API",
    version="1.0.0",
    description="RAG + Mistral Career Guidance Backend"
)

logger.info("FastAPI App Created")


# =====================================================
# CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS Enabled")


# =====================================================
# ROUTES
# =====================================================
app.include_router(router)

logger.info("Routes Registered")


# =====================================================
# STARTUP
# =====================================================
@app.on_event("startup")
async def startup_event():
    logger.info("Career AI Backend Started Successfully")


# =====================================================
# SHUTDOWN
# =====================================================
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Career AI Backend Stopped")