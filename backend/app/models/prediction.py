# backend/app/models/prediction.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id                  = Column(Integer, primary_key=True, index=True)
    customer_id         = Column(String, index=True)
    churn_probability   = Column(Float, nullable=False)
    risk_category       = Column(String(20), nullable=False)
    model_version       = Column(String(50), default="v1.0")
    feature_importances = Column(JSON, nullable=True)
    shap_values         = Column(JSON, nullable=True)
    input_features      = Column(JSON, nullable=True)
    predicted_at        = Column(DateTime(timezone=True), server_default=func.now())