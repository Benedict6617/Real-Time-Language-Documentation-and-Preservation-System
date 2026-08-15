"""Kaimira API — FastAPI application entrypoint."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    annotations,
    auth,
    community,
    export,
    languages,
    learning_materials,
    phonemes,
    recordings,
    transcription,
)

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("kaimira")

app = FastAPI(
    title="Kaimira — Language Documentation & Preservation API",
    description=(
        "API for recording, transcribing, analyzing, and archiving endangered "
        "language data, with community annotation and revitalization tooling."
    ),
    version="1.0.0",
    contact={"name": "Kaimira Project"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(languages.router)
app.include_router(recordings.router)
app.include_router(transcription.router)
app.include_router(phonemes.router)
app.include_router(annotations.router)
app.include_router(export.router)
app.include_router(community.router)
app.include_router(learning_materials.router)


@app.get("/health", tags=["meta"])
async def health_check() -> dict:
    return {"status": "ok", "environment": settings.environment}


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "name": "Kaimira Language Documentation & Preservation API",
        "docs": "/docs",
        "health": "/health",
    }
