# backend/app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String, unique=True, index=True, nullable=False)
    username   = Column(String, unique=True, index=True, nullable=False)
    full_name  = Column(String, nullable=True)
    
    # WHY hash passwords:
    # NEVER store plain text passwords
    # If database is breached, passwords are safe
    # bcrypt is the industry standard hashing algorithm
    hashed_password = Column(String, nullable=False)
    
    is_active  = Column(Boolean, default=True)
    is_admin   = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"