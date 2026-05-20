# backend/app/models/customer.py

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class customer(Base):
    """
    SQLAlchemy ORM model = a Python class that maps to a DB table.
    
    WHY ORM instead of raw SQL:
    - Write Python, get SQL for free
    - Database-agnostic (switch from PostgreSQL to MySQL with one config change)
    - Type safety, IDE autocomplete
    - Prevents SQL injection attacks by default
    
    Each attribute below becomes a column in the 'customers' table.
    """
    
    __tablename__ = "customers"
    # SQLAlchemy reads __tablename__ to know which DB table this maps to
    
    # Primary key: unique identifier for every row
    # index=True: creates a B-tree index for fast lookups by ID
    id = Column(Integer, primary_key=True, index=True)
    
    # Customer identifier from your CRM/billing system
    customer_id = Column(String, unique=True, index=True, nullable=False)
    # unique=True: no two customers can share an ID (enforced by DB)
    # index=True: fast search by customer_id (critical — this is how you look up customers)
    
    # Demographic features
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    location = Column(String(100), nullable=True)
    
    # Contract/billing features
    # WHY Float: churn probability is a float (0.0 to 1.0)
    tenure_months = Column(Integer, nullable=True)  # How long they've been a customer
    monthly_charges = Column(Float, nullable=True)
    total_charges = Column(Float, nullable=True)
    contract_type = Column(String(50), nullable=True)  # "Month-to-month", "One year", etc.
    payment_method = Column(String(50), nullable=True)
    
    # Service features
    internet_service = Column(String(50), nullable=True)
    phone_service = Column(Boolean, nullable=True)
    multiple_lines = Column(Boolean, nullable=True)
    online_security = Column(Boolean, nullable=True)
    tech_support = Column(Boolean, nullable=True)
    streaming_tv = Column(Boolean, nullable=True)
    streaming_movies = Column(Boolean, nullable=True)
    
    # Engagement features
    num_support_tickets = Column(Integer, default=0)
    last_login_days_ago = Column(Integer, nullable=True)
    
    # Target variable — what we're predicting
    # nullable=True because new customers haven't churned yet
    churned = Column(Boolean, nullable=True)
    
    # Audit columns — industry standard
    # server_default=func.now(): the DB sets this automatically on INSERT
    # WHY: more reliable than Python setting it (avoids timezone issues)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # onupdate: automatically updates this timestamp whenever the row changes
    
    # Notes field for retention team
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        # Makes debugging easy: print(customer) shows something useful
        return f"<Customer {self.customer_id} | Churned: {self.churned}>"