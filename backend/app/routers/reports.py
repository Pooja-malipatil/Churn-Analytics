# backend/app/routers/reports.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()


class CustomerPredictionReport(BaseModel):
    customer_id:          str
    churn_probability:    float
    risk_category:        str
    top_risk_factors:     List[Dict[str, Any]]
    explanation:          str
    retention_strategies: List[str]
    model_version:        str = "v1.0"
    prediction_id:        int = 0


@router.get("/reports/analytics")
async def download_analytics_report():
    """Generate and download full analytics PDF report."""
    try:
        from app.services.pdf_service import generate_analytics_report
        from app.routers.analytics import (
            get_summary, churn_by_contract,
            churn_by_tenure, churn_by_internet,
            churn_by_payment
        )

        summary_res  = await get_summary()
        contract_res = await churn_by_contract()
        tenure_res   = await churn_by_tenure()
        internet_res = await churn_by_internet()
        payment_res  = await churn_by_payment()

        if "error" in summary_res:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot generate report: {summary_res['error']}"
            )

        analytics_data = {
            "contract": contract_res.get("data", []),
            "tenure":   tenure_res.get("data",   []),
            "internet": internet_res.get("data",  []),
            "payment":  payment_res.get("data",   []),
        }

        pdf_bytes = generate_analytics_report(summary_res, analytics_data)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    'attachment; filename="ChurnAI_Analytics_Report.pdf"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Analytics report error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@router.post("/reports/customer")
async def download_customer_report(prediction: CustomerPredictionReport):
    """Generate and download a customer prediction PDF report."""
    try:
        from app.services.pdf_service import generate_customer_report

        pdf_bytes   = generate_customer_report(prediction.dict())
        customer_id = prediction.customer_id.replace("/", "_")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="ChurnAI_Customer_{customer_id}.pdf"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )

    except Exception as e:
        print(f"Customer report error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )