# backend/app/routers/analytics.py

from fastapi import APIRouter
import pandas as pd
import numpy as np
import os

router = APIRouter()

# Get absolute path to backend/data/ folder
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR  = os.path.join(BASE_DIR, "data")

print(f"📁 Analytics data directory: {DATA_DIR}")


def get_active_dataset() -> pd.DataFrame:
    """
    Load the currently active dataset.
    Always uses absolute paths.
    """
    paths = [
        os.path.join(DATA_DIR, "uploaded_dataset.csv"),
        os.path.join(DATA_DIR, "WA_Fn-UseC_-Telco-Customer-Churn.csv"),
    ]

    for path in paths:
        print(f"🔍 Checking: {path} → {os.path.exists(path)}")
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                df = standardize_columns(df)
                print(f"✅ Loaded: {path} ({len(df)} rows)")
                return df
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
                continue

    raise Exception(f"No dataset found in {DATA_DIR}")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to internal format."""

    rename_map = {
        "tenure":          "tenure_months",
        "MonthlyCharges":  "monthly_charges",
        "TotalCharges":    "total_charges",
        "Contract":        "contract_type",
        "InternetService": "internet_service",
        "PaymentMethod":   "payment_method",
        "OnlineSecurity":  "online_security",
        "TechSupport":     "tech_support",
        "StreamingTV":     "streaming_tv",
        "StreamingMovies": "streaming_movies",
        "PhoneService":    "phone_service",
        "MultipleLines":   "multiple_lines",
        "Churn":           "churned",
        "SeniorCitizen":   "senior_citizen",
    }

    df = df.rename(columns=rename_map)

    # Fix churned column
    if "churned" in df.columns:
        if df["churned"].dtype == object:
            df["churned"] = df["churned"].map({
                "Yes": 1, "No": 0,
                "yes": 1, "no": 0,
                "True": 1, "False": 0,
                "1": 1, "0": 0,
                True: 1, False: 0,
                1: 1, 0: 0,
            }).fillna(0).astype(int)
        else:
            df["churned"] = pd.to_numeric(
                df["churned"], errors="coerce"
            ).fillna(0).astype(int)

    # Fix total charges
    if "total_charges" in df.columns:
        df["total_charges"] = pd.to_numeric(
            df["total_charges"], errors="coerce"
        ).fillna(0)

    # Fix monthly charges
    if "monthly_charges" in df.columns:
        df["monthly_charges"] = pd.to_numeric(
            df["monthly_charges"], errors="coerce"
        ).fillna(0)

    return df


@router.get("/analytics/summary")
async def get_summary():
    try:
        df = get_active_dataset()

        total      = len(df)
        churned    = int(df["churned"].sum()) if "churned" in df.columns else 0
        retained   = total - churned
        churn_rate = round(churned / total * 100, 1) if total > 0 else 0

        avg_monthly      = 0.0
        churner_monthly  = 0.0
        retained_monthly = 0.0

        if "monthly_charges" in df.columns:
            avg_monthly      = round(float(df["monthly_charges"].mean()), 2)
            churner_monthly  = round(
                float(df[df["churned"] == 1]["monthly_charges"].mean()), 2
            ) if churned > 0 else 0.0
            retained_monthly = round(
                float(df[df["churned"] == 0]["monthly_charges"].mean()), 2
            ) if retained > 0 else 0.0

        revenue_at_risk = round(churner_monthly * churned, 2)

        return {
            "total_customers":      total,
            "churned_customers":    churned,
            "retained_customers":   retained,
            "churn_rate":           churn_rate,
            "avg_monthly_charges":  avg_monthly,
            "churner_avg_monthly":  churner_monthly,
            "retained_avg_monthly": retained_monthly,
            "revenue_at_risk":      revenue_at_risk,
        }

    except Exception as e:
        print(f"Summary error: {e}")
        return {"error": str(e)}


@router.get("/analytics/churn-by-contract")
async def churn_by_contract():
    try:
        df = get_active_dataset()

        if "contract_type" not in df.columns or "churned" not in df.columns:
            return {"data": []}

        result = []
        for contract in df["contract_type"].dropna().unique():
            subset    = df[df["contract_type"] == contract]
            churned   = int(subset["churned"].sum())
            retained  = len(subset) - churned
            churn_rate = round(churned / len(subset) * 100, 1)
            result.append({
                "name":      str(contract),
                "churned":   churned,
                "retained":  retained,
                "churnRate": churn_rate,
                "total":     len(subset),
            })

        result.sort(key=lambda x: x["churnRate"], reverse=True)
        return {"data": result}

    except Exception as e:
        print(f"Contract error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-tenure")
async def churn_by_tenure():
    try:
        df = get_active_dataset()

        if "tenure_months" not in df.columns or "churned" not in df.columns:
            return {"data": []}

        df["tenure_months"] = pd.to_numeric(
            df["tenure_months"], errors="coerce"
        ).fillna(0)

        bins   = [0, 12, 24, 36, 48, 60, float("inf")]
        labels = [
            "0-12 months",  "13-24 months",
            "25-36 months", "37-48 months",
            "49-60 months", "60+ months"
        ]

        df["tenure_group"] = pd.cut(
            df["tenure_months"],
            bins=bins, labels=labels, right=True
        )

        result = []
        for label in labels:
            subset = df[df["tenure_group"] == label]
            if len(subset) == 0:
                continue
            churned    = int(subset["churned"].sum())
            churn_rate = round(churned / len(subset) * 100, 1)
            result.append({
                "tenure":    label,
                "churnRate": churn_rate,
                "customers": len(subset),
                "churned":   churned,
            })

        return {"data": result}

    except Exception as e:
        print(f"Tenure error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-internet")
async def churn_by_internet():
    try:
        df = get_active_dataset()

        if "internet_service" not in df.columns or "churned" not in df.columns:
            return {"data": []}

        result = []
        for service in df["internet_service"].dropna().unique():
            subset     = df[df["internet_service"] == service]
            churned    = int(subset["churned"].sum())
            churn_rate = round(churned / len(subset) * 100, 1)
            result.append({
                "name":      str(service),
                "churnRate": churn_rate,
                "customers": len(subset),
            })

        result.sort(key=lambda x: x["churnRate"], reverse=True)
        return {"data": result}

    except Exception as e:
        print(f"Internet error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-payment")
async def churn_by_payment():
    try:
        df = get_active_dataset()

        if "payment_method" not in df.columns or "churned" not in df.columns:
            return {"data": []}

        result = []
        for method in df["payment_method"].dropna().unique():
            subset     = df[df["payment_method"] == method]
            churned    = int(subset["churned"].sum())
            churn_rate = round(churned / len(subset) * 100, 1)
            result.append({
                "name":      str(method),
                "churnRate": churn_rate,
                "customers": len(subset),
            })

        result.sort(key=lambda x: x["churnRate"], reverse=True)
        return {"data": result}

    except Exception as e:
        print(f"Payment error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-charges")
async def churn_by_charges():
    try:
        df = get_active_dataset()

        if "monthly_charges" not in df.columns or "churned" not in df.columns:
            return {"data": []}

        df["monthly_charges"] = pd.to_numeric(
            df["monthly_charges"], errors="coerce"
        ).fillna(0)

        max_charge = df["monthly_charges"].max()
        step       = max_charge / 6 if max_charge > 0 else 20

        result = []
        for i in range(6):
            low    = round(i * step, 0)
            high   = round((i + 1) * step, 0)
            subset = df[
                (df["monthly_charges"] >= low) &
                (df["monthly_charges"] < high)
            ]
            if len(subset) == 0:
                continue
            churned    = int(subset["churned"].sum())
            churn_rate = round(churned / len(subset) * 100, 1)
            result.append({
                "range":     f"${int(low)}-${int(high)}",
                "churnRate": churn_rate,
                "customers": len(subset),
            })

        return {"data": result}

    except Exception as e:
        print(f"Charges error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/service-impact")
async def service_impact():
    try:
        df = get_active_dataset()

        services = [
            ("online_security",  "Online Security"),
            ("tech_support",     "Tech Support"),
            ("streaming_tv",     "Streaming TV"),
            ("streaming_movies", "Streaming Movies"),
        ]

        result = []
        for col, label in services:
            if col not in df.columns or "churned" not in df.columns:
                continue

            df[col] = pd.to_numeric(
                df[col].map({
                    "Yes": 1, "No": 0,
                    "yes": 1, "no": 0,
                    "No internet service": 0,
                    "No phone service": 0,
                    True: 1, False: 0,
                    1: 1, 0: 0,
                }),
                errors="coerce"
            ).fillna(0)

            with_svc    = df[df[col] == 1]
            without_svc = df[df[col] == 0]

            if len(with_svc) == 0 or len(without_svc) == 0:
                continue

            result.append({
                "service":        label,
                "withService":    round(
                    with_svc["churned"].mean() * 100, 1
                ),
                "withoutService": round(
                    without_svc["churned"].mean() * 100, 1
                ),
            })

        return {"data": result}

    except Exception as e:
        print(f"Service error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/at-risk-customers")
async def get_at_risk_customers():
    try:
        df = get_active_dataset()

        from app.services.ml_service import ml_service

        if not ml_service.is_ready:
            return {"data": [], "error": "ML model not loaded"}

        NUMERIC_FEATURES     = [
            "tenure_months", "monthly_charges",
            "total_charges", "num_support_tickets"
        ]
        CATEGORICAL_FEATURES = [
            "contract_type", "internet_service", "payment_method"
        ]
        BINARY_FEATURES      = [
            "online_security", "tech_support", "streaming_tv",
            "streaming_movies", "phone_service", "multiple_lines"
        ]
        ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES

        # Add missing columns
        defaults = {
            "num_support_tickets": 0,
            "contract_type":       "Month-to-month",
            "internet_service":    "DSL",
            "payment_method":      "Electronic check",
            "online_security":     0,
            "tech_support":        0,
            "streaming_tv":        0,
            "streaming_movies":    0,
            "phone_service":       1,
            "multiple_lines":      0,
            "total_charges":       0,
        }
        for col, val in defaults.items():
            if col not in df.columns:
                df[col] = val

        # Fix binary columns
        for col in BINARY_FEATURES:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].map({
                        "Yes": 1, "No": 0,
                        "yes": 1, "no": 0,
                        "No internet service": 0,
                        "No phone service": 0,
                        True: 1, False: 0,
                        1: 1, 0: 0,
                    }),
                    errors="coerce"
                ).fillna(0)

        X             = df[ALL_FEATURES].fillna(0)
        probabilities = ml_service.model.predict_proba(X)[:, 1]
        df            = df.copy()
        df["churn_probability"] = probabilities

        # Get top 20 at-risk
        at_risk = df[df["churn_probability"] >= 0.5].copy()
        at_risk = at_risk.sort_values(
            "churn_probability", ascending=False
        ).head(20)

        result = []
        for idx, row in at_risk.iterrows():
            prob = float(row["churn_probability"])
            risk = (
                "Critical" if prob >= 0.75 else
                "High"     if prob >= 0.50 else
                "Medium"
            )

            customer_id = (
                str(row.get("customerID", ""))  or
                str(row.get("customer_id", "")) or
                str(row.get("id", ""))          or
                f"CUST_{idx}"
            )

            result.append({
                "id":               customer_id,
                "churnProbability": round(prob, 3),
                "riskCategory":     risk,
                "tenure":           int(row.get("tenure_months", 0)),
                "monthlyCharges":   round(
                    float(row.get("monthly_charges", 0)), 2
                ),
                "contract":         str(row.get("contract_type", "Unknown")),
                "internetService":  str(row.get("internet_service", "Unknown")),
            })

        return {"data": result, "total": len(result)}

    except Exception as e:
        print(f"At-risk error: {e}")
        return {"data": [], "error": str(e)}