# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    
    # pool_pre_ping: before using a connection, send a cheap "SELECT 1"
    # WHY: if the DB restarted, stale connections in the pool would cause errors.
    # Pre-ping detects dead connections and replaces them automatically.
    pool_pre_ping=True,
    
    # echo=True prints all SQL to console — great for debugging, OFF in production
    echo=settings.DEBUG,
)

# SessionLocal is a factory: calling it creates a new DB session
# autocommit=False: we control when to commit (explicit is better than implicit)
# autoflush=False: we control when to flush pending changes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: all your ORM models will inherit from this
# It's how SQLAlchemy knows "this class is a database table"
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.
    
    This is the DEPENDENCY INJECTION pattern — FastAPI's superpower.
    
    How it works:
    1. FastAPI calls get_db() before your route function runs
    2. It creates a fresh DB session
    3. It passes that session into your route via `db: Session = Depends(get_db)`
    4. After your route finishes, the `finally` block closes the session
    
    WHY this pattern matters:
    - Every request gets its own session (thread-safe)
    - Session is always closed, even if an exception occurs
    - You never forget to close connections (memory leak prevention)
    - Easy to swap with a test database in unit tests
    """
    db = SessionLocal()
    try:
        yield db          # yield makes this a generator — FastAPI uses this for lifecycle
    finally:
        db.close()        # ALWAYS runs, even if route threw an exception