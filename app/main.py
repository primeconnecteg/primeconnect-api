import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.limiter import limiter
from app.api.v1.router import api_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# =============================================================================
# 1. LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# 2. APPLICATION LIFESPAN
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager that defines the startup and shutdown lifecycle of the FastAPI app.
    Everything before 'yield' runs exactly once when the server boots.
    Everything after 'yield' runs exactly once when the server shuts down.
    """
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    
    # Startup: Verify Database Connection
    try:
        # engine.begin() attempts a physical connection to the database
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(f"Successfully connected to the database ({engine.url.get_backend_name()}).")
    except Exception as e:
        logger.critical(f"Failed to connect to the database: {e}")
        # We do not crash the app here, but Kubernetes would see health checks fail.
        
    yield
    
    # Shutdown: Clean up resources
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    await engine.dispose()
    logger.info("Database connection pool successfully closed.")

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
    """Handles deliberate HTTP exceptions (like 401 Unauthorized or 404 Not Found)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation failures (e.g. missing fields, bad email format)."""
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
    Catch-all for completely unexpected server errors (e.g. database disconnects mid-query, divide by zero).
    We log the full stack trace securely to the server, but return a generic 500 error to the client.
    This strictly prevents leaking database schemas or internal variables to potential hackers.
    """
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."}
    )

# =============================================================================
# 6. GLOBAL ENDPOINTS (Health & Root)
# =============================================================================
@app.get("/", tags=["Health"])
async def root():
    """Minimal root endpoint to confirm the API is routing traffic."""
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker / Kubernetes liveness probes."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION
    }

# =============================================================================
# 7. ROUTER REGISTRATION
# =============================================================================
# Attach the massive API router tree (which contains /auth, /admin, and /contact)
# to the root FastAPI application under the /api/v1 prefix.
app.include_router(api_router, prefix=settings.API_V1_STR)
