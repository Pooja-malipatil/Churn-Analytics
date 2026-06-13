# backend/app/routers/customers.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Optional
from app.database import get_db
from app.models.prediction import PredictionLog

router = APIRouter()


@router.get("/customers/predictions")
async def get_all_predictions(
    page:     int   = Query(default=1,  ge=1),
    limit:    int   = Query(default=10, ge=1, le=100),
    risk:     Optional[str] = Query(default=None),
    search:   Optional[str] = Query(default=None),
    db:       Session = Depends(get_db),
):
    """
    Get all predictions with pagination, filtering and search.
    """
    query = db.query(PredictionLog)

    # Filter by risk category
    if risk and risk != "All":
        query = query.filter(
            PredictionLog.risk_category == risk
        )

    # Search by customer ID
    if search:
        query = query.filter(
            PredictionLog.customer_id.ilike(f"%{search}%")
        )

    # Total count
    total = query.count()

    # Paginate and sort by latest first
    predictions = (
        query
        .order_by(desc(PredictionLog.predicted_at))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "predictions": [
            {
                "id":                p.id,
                "customer_id":       p.customer_id,
                "churn_probability": p.churn_probability,
                "risk_category":     p.risk_category,
                "model_version":     p.model_version,
                "predicted_at":      p.predicted_at.isoformat()
                                     if p.predicted_at else None,
                "feature_importances": p.feature_importances,
            }
            for p in predictions
        ],
        "total":      total,
        "page":       page,
        "limit":      limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.get("/customers/predictions/{customer_id}")
async def get_customer_predictions(
    customer_id: str,
    db:          Session = Depends(get_db),
):
    """Get all predictions for a specific customer."""
    predictions = (
        db.query(PredictionLog)
        .filter(PredictionLog.customer_id == customer_id)
        .order_by(desc(PredictionLog.predicted_at))
        .all()
    )

    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for customer {customer_id}"
        )

    return {
        "customer_id": customer_id,
        "total":       len(predictions),
        "predictions": [
            {
                "id":                p.id,
                "churn_probability": p.churn_probability,
                "risk_category":     p.risk_category,
                "model_version":     p.model_version,
                "predicted_at":      p.predicted_at.isoformat()
                                     if p.predicted_at else None,
                "feature_importances": p.feature_importances,
            }
            for p in predictions
        ],
        "latest_risk":        predictions[0].risk_category,
        "latest_probability": predictions[0].churn_probability,
        "trend": "increasing" if len(predictions) > 1 and
                  predictions[0].churn_probability >
                  predictions[1].churn_probability
                  else "decreasing" if len(predictions) > 1
                  else "stable",
    }


@router.get("/customers/stats")
async def get_prediction_stats(db: Session = Depends(get_db)):
    """Get overall prediction statistics from database."""
    total = db.query(PredictionLog).count()

    if total == 0:
        return {
            "total_predictions": 0,
            "critical":  0,
            "high":      0,
            "medium":    0,
            "low":       0,
            "avg_probability": 0,
        }

    critical = db.query(PredictionLog).filter(
        PredictionLog.risk_category == "Critical"
    ).count()
    high     = db.query(PredictionLog).filter(
        PredictionLog.risk_category == "High"
    ).count()
    medium   = db.query(PredictionLog).filter(
        PredictionLog.risk_category == "Medium"
    ).count()
    low      = db.query(PredictionLog).filter(
        PredictionLog.risk_category == "Low"
    ).count()

    all_probs = db.query(PredictionLog.churn_probability).all()
    avg_prob  = sum(p[0] for p in all_probs) / len(all_probs)

    return {
        "total_predictions": total,
        "critical":          critical,
        "high":              high,
        "medium":            medium,
        "low":               low,
        "avg_probability":   round(avg_prob * 100, 1),
    }


@router.delete("/customers/predictions/{prediction_id}")
async def delete_prediction(
    prediction_id: int,
    db:            Session = Depends(get_db),
):
    """Delete a specific prediction."""
    prediction = db.query(PredictionLog).filter(
        PredictionLog.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found"
        )

    db.delete(prediction)
    db.commit()
    return {"message": "Prediction deleted successfully"}