import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

from src.helpers.db import get_db, engine, Base
from src.routes.auth_routes import router as auth_router
from src.routes.document_routes import router as document_router
from src.routes.chat_routes import router as chat_router
from src.routes.citation_routes import router as citation_router
from src.helpers.config import Settings
from src.helpers.logging_config import get_logger, sanitize_headers, generate_request_id

# Import models to register them with Base.metadata
from src.models.db_scheams.user import User  # noqa: F401
from src.models.db_scheams.document import Document  # noqa: F401
from src.models.db_scheams.DocumentChunk import DocumentChunk  # noqa: F401
from src.models.db_scheams.Chat import Chat  # noqa: F401
from src.models.db_scheams.Message import Message  # noqa: F401

logger = get_logger("app")


# ── Request / Response Logging Middleware ────────────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming request and its response with timing info.

    Sensitive headers (Authorization, Cookie, etc.) are automatically
    redacted by `sanitize_headers`.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = generate_request_id()
        start_time = time.perf_counter()

        # Safe header snapshot
        safe_headers = sanitize_headers(dict(request.headers))

        logger.info(
            "REQ %s | %s %s | client=%s | headers=%s",
            request_id,
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
            safe_headers,
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "REQ %s | %s %s | UNHANDLED EXCEPTION after %.1f ms",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        log_fn = logger.info if response.status_code < 400 else logger.warning
        log_fn(
            "RES %s | %s %s | status=%s | %.1f ms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    logger.info("Application starting — creating database tables …")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready — application is up")
    yield
    logger.info("Application shutting down")


# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Authentication System API",
    description="A simple FastAPI server with PostgreSQL connection",
    version="1.0.0",
    lifespan=lifespan,
)

# Request logging middleware (added BEFORE CORS so it wraps everything)
app.add_middleware(RequestLoggingMiddleware)

# CORS
origins = Settings().CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Authorization, Content-Type, etc.
)


# Include routers
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(citation_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Authentication System API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check if the server and database are running correctly.
    """
    try:
        # Execute a simple query to verify database connectivity
        await db.execute(text("SELECT 1"))
        logger.info("Health check passed — database connected")
        return {
            "status": "online",
            "database": "connected",
            "message": "System is healthy",
        }
    except Exception as e:
        logger.error("Health check FAILED — database error: %s", str(e))
        return {
            "status": "online",
            "database": f"error: {str(e)}",
            "message": "Database connection failed",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
