# backend/app/schemas/prediction.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from enum import Enum

# Pydantic schemas are the INTERFACE CONTRACT between frontend and backend.
# They define exactly what data can come IN (requests) and go OUT (responses).
# 
# WHY separate schemas from ORM models:
# - ORM models = database shape
# - Schemas = API shape
# - They're often different! (e.g., never expose password hashes in responses)
# - Pydantic auto-validates types and generates OpenAPI documentation

class ContractType(str, Enum):
    """
    Using Enum for contract types has huge benefits:
    1. Validation: "Montly-to-montly" (typo) is rejected immediately
    2. Documentation: Swagger UI shows the valid options
    3. IDE autocomplete when building the frontend
    """
    MONTH_TO_MONTH = "Month-to-month"
    ONE_YEAR = "One year"
    TWO_YEAR = "Two year"

class RiskCategory(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class CustomerPredictRequest(BaseModel):
    """
    Validates the prediction request from the frontend.
    If ANY field fails validation, FastAPI returns a 422 error
    with detailed information about WHICH field failed and WHY.
    
    This prevents garbage data from ever reaching your ML model.
    """
    
    customer_id: str = Field(..., description="Unique customer identifier")
    # Field(...) means required. Field("default") means optional with default.
    
    tenure_months: int = Field(..., ge=0, le=600, description="Months as customer")
    # ge=0: must be >= 0 (no negative tenure)
    # le=600: must be <= 600 (50 years max — catches obvious data errors)
    
    monthly_charges: float = Field(..., ge=0, le=10000, description="Monthly bill in USD")
    
    total_charges: float = Field(..., ge=0)
    
    contract_type: ContractType = Field(..., description="Contract duration type")
    
    # Optional fields with defaults
    num_support_tickets: int = Field(default=0, ge=0, le=100)
    
    online_security: bool = Field(default=False)
    tech_support: bool = Field(default=False)
    
    internet_service: Optional[str] = Field(default=None)
    
    age: Optional[int] = Field(default=None, ge=18, le=120)
    
    @validator('total_charges')
    def total_must_exceed_monthly(cls, v, values):
        """
        Custom validator: total charges should generally exceed monthly charges
        (unless they've been a customer less than 1 month).
        
        WHY custom validators: some business rules can't be expressed as simple
        field constraints. This is where you add domain-specific logic.
        """
        if 'monthly_charges' in values and v < values['monthly_charges'] * 0.9:
            # Allow 10% tolerance for discounts, rounding, etc.
            pass  # Could raise ValueError here in a stricter system
        return v
    
    class Config:
        # Allows the schema to be used as OpenAPI example
        json_schema_extra = {
            "example": {
                "customer_id": "CUST_001",
                "tenure_months": 24,
                "monthly_charges": 79.99,
                "total_charges": 1919.76,
                "contract_type": "Month-to-month",
                "num_support_tickets": 3,
                "online_security": False,
                "tech_support": False,
            }
        }

class PredictionResponse(BaseModel):
    """
    What the API sends BACK to the frontend after prediction.
    """
    customer_id: str
    churn_probability: float = Field(..., ge=0.0, le=1.0)
    risk_category: RiskCategory
    
    # Top factors driving this prediction (for the UI)
    top_risk_factors: List[Dict[str, float]]
    # Example: [{"feature": "tenure_months", "impact": -0.34}, ...]
    # Negative impact = reduces churn risk, Positive = increases it
    
    # Human-readable explanation
    explanation: str
    
    # Retention recommendations from the intelligence engine
    retention_strategies: List[str]
    
    # Model metadata (useful for debugging in production)
    model_version: str
    prediction_id: int  # The logged PredictionLog.id
    
    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy model objects