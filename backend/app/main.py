# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base

# Import all routers (we'll build these next)
from app.routers import predict, analytics, retention, upload, customers

# -----------------------------------------------------------------------
# LIFESPAN: Runs setup code on startup and cleanup code on shutdown
# This is the modern FastAPI pattern (replaces deprecated @app.on_event)
# -----------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Everything BEFORE yield runs at startup.
    Everything AFTER yield runs at shutdown.
    
    WHY this pattern:
    - Load ML models into memory ONCE (not on every request — that'd be 5-second latency)
    - Create DB tables if they don't exist
    - Initialize caches, connect to Redis, etc.
    
    In production: you'd use Alembic migrations instead of create_all().
    create_all() is fine for development.
    """
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create all DB tables defined in our models
    # WHY: SQLAlchemy reads all Base subclasses and generates CREATE TABLE statements
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized")
    
    # Pre-load the ML model into memory
    # We import here (not at top) to avoid circular imports during startup
    from app.services.ml_service import ml_service 
    await ml_service.initialize()
    print("✅ ML models loaded")
    
    yield  # App runs here (handling requests)
    
    # Cleanup on shutdown
    print("🛑 Shutting down gracefully...")

# -----------------------------------------------------------------------
# APPLICATION FACTORY
# Create the FastAPI app — this is the central object everything attaches to
# -----------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    AI-Powered Customer Churn Prediction & Retention Analytics API.
    
    ## Features
    - Churn probability scoring
    - SHAP-based explainability  
    - Retention strategy recommendations
    - Customer behavior analytics
    """,
    # Docs available at /docs (Swagger UI) and /redoc
    # WHY built-in docs: FastAPI generates them from your Pydantic schemas automatically
    # Every schema, validator, and example you wrote becomes interactive documentation
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------
# MIDDLEWARE: Functions that run on EVERY request (before/after route)
# -----------------------------------------------------------------------

# CORS Middleware: allow the React frontend to call this API
# Without this, browsers block cross-origin requests (security feature)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# GZip: compress large responses (analytics data, chart data)
# WHY: reduces bandwidth by 70-90% for JSON responses
# Threshold=1000: only compress responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# -----------------------------------------------------------------------
# ROUTERS: Mount each feature area at its URL prefix
# WHY routers: without them, main.py would have 500+ lines.
# Each router is a mini-app that handles a subset of routes.
# Adding a new feature = add a new router file, one line here.
# -----------------------------------------------------------------------
app.include_router(predict.router,    prefix="/api/v1", tags=["Prediction"])
app.include_router(analytics.router,  prefix="/api/v1", tags=["Analytics"])
app.include_router(retention.router,  prefix="/api/v1", tags=["Retention"])
app.include_router(upload.router,     prefix="/api/v1", tags=["Data Upload"])
app.include_router(customers.router,  prefix="/api/v1", tags=["Customers"])
# WHY /api/v1 prefix: 
# - /api: clear that this is an API (not a web page)
# - /v1: when you make breaking changes, deploy /v2 while /v1 still works
#   Old clients keep working. This is how Stripe, Twilio, GitHub do it.

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint — load balancers ping this to know the service is alive."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "ok"}

#uvicorn app.main:app --reload --port 8000