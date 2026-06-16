# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import engine, Base

# Import all models so SQLAlchemy creates all tables
from app.models import customer, prediction
from app.models import user as user_model

from app.routers import predict, analytics, retention, upload, customers, auth, reports

# Create all DB tables
Base.metadata.create_all(bind=engine)
print("✅ Database tables initialized")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Customer Churn Prediction & Retention Analytics API.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://churn-analytics-wo2v-oue4lvob0-pmalipatil239-2834s-projects.vercel.app",
        "https://churn-analytics-wo2v.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(predict.router,    prefix="/api/v1", tags=["Prediction"])
app.include_router(analytics.router,  prefix="/api/v1", tags=["Analytics"])
app.include_router(retention.router,  prefix="/api/v1", tags=["Retention"])
app.include_router(upload.router,     prefix="/api/v1", tags=["Data Upload"])
app.include_router(customers.router,  prefix="/api/v1", tags=["Customers"])
app.include_router(auth.router,       prefix="/api/v1", tags=["Authentication"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])


@app.on_event("startup")
async def startup_event():
    """Load ML models on startup."""
    from app.services.ml_service import ml_service
    await ml_service.initialize()
    print("✅ ML models loaded")


@app.get("/", tags=["Health"])
def root():
    return {
        "status":  "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# uvicorn app.main:app --reload --port 8000c