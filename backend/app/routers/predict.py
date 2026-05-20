from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.prediction import CustomerPredictRequest, PredictionResponse
from app.services.ml_service import ml_service
import traceback

router = APIRouter()

@router.post("/predict")
async def predict_churn(
    request: CustomerPredictRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        result = await ml_service.predict(request, db)
        return result
    except Exception as e:
        # Print full error to terminal
        print("=" * 50)
        print("PREDICTION ERROR:")
        print(traceback.format_exc())
        print("=" * 50)
        raise HTTPException(status_code=500, detail=str(e))