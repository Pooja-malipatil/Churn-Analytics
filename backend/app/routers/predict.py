# backend/app/routers/predict.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.schemas.prediction import CustomerPredictRequest
from app.services.ml_service import ml_service
import traceback

router = APIRouter()


def log_prediction_sync(customer_id: str, result: dict):
    """
    Synchronous background task for logging.
    Creates its own DB session.
    WHY: Background tasks run after response is sent.
    The request's db session may be closed by then.
    So we create a fresh session here.
    """
    db = SessionLocal()
    try:
        from app.models.prediction import PredictionLog
        log = PredictionLog(
            customer_id         = customer_id,
            churn_probability   = result["churn_probability"],
            risk_category       = result["risk_category"],
            model_version       = result.get("model_version", "v1.0"),
            feature_importances = result.get("top_risk_factors", []),
            shap_values         = result.get("top_risk_factors", []),
            input_features      = {},
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        print(f"✅ Prediction logged for {customer_id} — ID: {log.id}")
    except Exception as e:
        print(f"❌ Logging error: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/predict")
async def predict_churn(
    request:          CustomerPredictRequest,
    background_tasks: BackgroundTasks,
    db:               Session = Depends(get_db),
):
    try:
        result = await ml_service.predict(request, db)

        # Log in background with its own DB session
        background_tasks.add_task(
            log_prediction_sync,
            customer_id = request.customer_id,
            result      = result,
        )

        return result

    except Exception as e:
        print("=" * 50)
        print("PREDICTION ERROR:")
        print(traceback.format_exc())
        print("=" * 50)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
async def predict_batch(
    requests: list[CustomerPredictRequest],
    db:       Session = Depends(get_db),
):
    if len(requests) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Batch size limited to 1000."
        )

    results = []
    for req in requests:
        result = await ml_service.predict(req, db)
        results.append(result)

    return {"predictions": results, "count": len(results)}


@router.get("/predict/history/{customer_id}")
async def get_prediction_history(
    customer_id: str,
    limit:       int = 10,
    db:          Session = Depends(get_db),
):
    from app.models.prediction import PredictionLog

    history = (
        db.query(PredictionLog)
        .filter(PredictionLog.customer_id == customer_id)
        .order_by(PredictionLog.predicted_at.desc())
        .limit(limit)
        .all()
    )

    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for {customer_id}"
        )

    return history