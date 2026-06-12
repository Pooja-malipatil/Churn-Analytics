# backend/app/schemas/prediction.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class CustomerPredictRequest(BaseModel):
    customer_id:         str
    tenure_months:       float = Field(default=0)
    monthly_charges:     float = Field(default=0)
    total_charges:       float = Field(default=0)
    num_support_tickets: int   = Field(default=0)
    contract_type:       str   = Field(default="Month-to-month")
    internet_service:    str   = Field(default="DSL")
    payment_method:      str   = Field(default="Electronic check")
    online_security:     bool  = False
    tech_support:        bool  = False
    streaming_tv:        bool  = False
    streaming_movies:    bool  = False
    phone_service:       bool  = True
    multiple_lines:      bool  = False
    age:                 Optional[int] = None

class PredictionResponse(BaseModel):
    customer_id:          str
    churn_probability:    float
    risk_category:        str
    top_risk_factors:     List[Dict]
    explanation:          str
    retention_strategies: List[str]
    model_version:        str
    prediction_id:        int

    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    customer_id:          str
    churn_probability:    float
    risk_category:        str
    top_risk_factors:     List[Dict]
    explanation:          str
    retention_strategies: List[str]
    model_version:        str
    prediction_id:        int

    class Config:
        from_attributes = True