"""
FastAPI application entry point.
CORS, routers, lifespan, global error handling.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models.session import session_store
from services.file_service import cleanup_old_files
from routers.files import router as files_router
from routers.copilot import router as copilot_router
from routers.agent import router as agent_router


# ── Lifespan ─────────────────────────────────────────────────

async def _periodic_cleanup():
    """Run cleanup every hour."""
    while True:
        try:
            files_cleaned = cleanup_old_files()
            sessions_cleaned = session_store.cleanup_expired()
            if files_cleaned or sessions_cleaned:
                print(f"Cleanup: {files_cleaned} files, {sessions_cleaned} sessions removed")
        except Exception:
            pass
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"DataSci AI Platform starting...")
    print(f"Upload dir: {settings.upload_path}")
    print(f"LLM: {settings.llm_model_name} @ {settings.llm_base_url}")

    # Initial cleanup
    cleanup_old_files()

    # Start background cleanup task
    cleanup_task = asyncio.create_task(_periodic_cleanup())

    yield

    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("DataSci AI Platform shutting down.")


# ── App ──────────────────────────────────────────────────────

app = FastAPI(
    title="DataSci AI Platform",
    description="AI-powered data science platform with Sheets Copilot and Agent Chat",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(files_router)
app.include_router(copilot_router)
app.include_router(agent_router)


# ── Global Error Handler ─────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return plain English errors."""
    # Log the real error server-side
    print(f"ERROR [{request.method} {request.url.path}]: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={"message": "Something went wrong. Please try again."},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


# ── Health Check ─────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "model": settings.llm_model_name}
