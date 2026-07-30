import logging
import traceback
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

# =============================================================================
# 1. LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")

logger.info("Initializing FastAPI Backend Application...")

try:
    logger.info("Loading settings...")
    from app.core.config import settings
    
    logger.info("Loading SMTP configuration...")
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.warning("SMTP configuration is incomplete. Email notifications may fail until SMTP environment variables are set.")
    else:
        logger.info(f"SMTP configured successfully for {settings.SMTP_HOST}:{settings.SMTP_PORT} (TLS: {settings.SMTP_USE_TLS}, Sender: '{settings.SMTP_FROM_EMAIL}')")

    logger.info("Connecting to database...")
    from app.core.database import engine
    
    logger.info("Loading limiter...")
    from app.core.limiter import limiter
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    
    logger.info("Loading API routers...")
    from app.api.v1.router import api_router
    logger.info("All modules loaded successfully.")
    
except Exception as e:
    logger.critical(f"FATAL: Application import failed during startup: {e}")
    logger.critical(traceback.format_exc())
    raise

# =============================================================================
# 2. APPLICATION LIFESPAN
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for startup and shutdown procedures.
    Ensures non-blocking verification of database connectivity on startup.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} (v{settings.VERSION})...")
    logger.info("Verifying database connectivity...")
    
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(f"Database connected successfully ({engine.url.get_backend_name()}).")
    except Exception as e:
        logger.error(f"Database connection warning on startup: {e}")
        logger.error(traceback.format_exc())
        logger.warning("Application will continue running to serve public endpoints and docs.")
        
    yield
    
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    try:
        await engine.dispose()
        logger.info("Database connection pool closed successfully.")
    except Exception as e:
        logger.error(f"Error disposing database engine: {e}")

# =============================================================================
# 3. FASTAPI INITIALIZATION
# =============================================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for the PrimeConnect company website.",
    version=settings.VERSION,
    contact={
        "name": "PrimeConnect Admin",
        "email": settings.CEO_EMAIL,
    },
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc" # ReDoc endpoint
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =============================================================================
# 4. CORS MIDDLEWARE
# =============================================================================
logger.info(f"Configuring CORS middleware with origins: {settings.BACKEND_CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 5. GLOBAL EXCEPTION HANDLERS
# =============================================================================
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles HTTP exceptions (e.g. 401, 404, 403)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation failures (e.g. missing fields, bad payload formats)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request payload",
            "errors": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unhandled server exceptions. Logs complete traceback to server logs.
    """
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."}
    )

# =============================================================================
# 6. GLOBAL ENDPOINTS (Health & Root)
# =============================================================================
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint returning basic metadata."""
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Vercel / Docker liveness probes."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION
    }

# =============================================================================
# 7. ROUTER REGISTRATION
# =============================================================================
logger.info(f"Registering API routes under prefix '{settings.API_V1_STR}'...")
app.include_router(api_router, prefix=settings.API_V1_STR)

if settings.API_V1_STR.startswith("/api"):
    v1_fallback = settings.API_V1_STR[4:]
    logger.info(f"Registering fallback API routes under prefix '{v1_fallback}'...")
    app.include_router(api_router, prefix=v1_fallback)

logger.info("Application started successfully.")
