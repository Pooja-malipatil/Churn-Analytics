# backend/app/routers/analytics.py

from fastapi import APIRouter
import pandas as pd
import numpy as np
import os

router = APIRouter()

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DATA_DIR = os.path.join(BASE_DIR, "data")

print(f"📁 Analytics data directory: {DATA_DIR}")


# -----------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------

def get_column_mapping():
    """Get the active column mapping from upload router."""
    try:
        from app.routers.upload import active_column_mapping
        return active_column_mapping
    except Exception:
        return None


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Automatically detect what each column represents.
    Works for ANY dataset.
    """
    cols       = list(df.columns)
    cols_lower = [c.lower() for c in cols]
    detected   = {}

    def find(keywords: list) -> str:
        for kw in keywords:
            for i, c in enumerate(cols_lower):
                if kw in c:
                    return cols[i]
        return None

    detected["churn"]           = find(["churn", "exited", "exit", "attrition", "left", "cancelled", "target", "label"])
    detected["tenure"]          = find(["tenure", "months", "duration", "age_months", "subscription_months", "customer_age"])
    detected["monthly_charges"] = find(["monthly", "monthlycharge", "monthly_fee", "monthly_bill", "subscription", "price", "fee", "rate", "premium", "salary", "income", "estimated", "revenue"])
    detected["total_charges"]   = find(["total_charge", "totalcharge", "total_bill", "total_paid", "lifetime_value", "ltv", "total_spend", "balance", "account_balance"])
    detected["contract_type"]   = find(["contract", "plan", "subscription_type", "billing_type", "billing_cycle", "tier", "membership", "package", "geography", "location", "region", "country"])
    detected["internet_service"]= find(["internet", "service_type", "connection", "broadband", "network", "access_type"])
    detected["payment_method"]  = find(["payment", "billing_method", "pay_method", "payment_type", "payment_channel"])
    detected["support_tickets"] = find(["ticket", "complaint", "support", "num_complaint", "issues", "calls", "numofproducts", "num_products", "products"])
    detected["age"]             = find(["age", "customer_age", "age_years"])
    detected["gender"]          = find(["gender", "sex"])
    detected["credit_score"]    = find(["credit", "score", "creditscore", "credit_score"])
    detected["is_active"]       = find(["active", "isactive", "is_active", "engaged"])

    print(f"🔍 Detected columns: {detected}")
    return detected


def standardize_df(df: pd.DataFrame, mapping=None) -> pd.DataFrame:
    """Standardize any dataframe to our internal format."""
    detected = detect_columns(df)
    result   = df.copy()

    # CHURN COLUMN
    if mapping and mapping.get("churn_col"):
        churn_col       = mapping["churn_col"]
        churn_yes_value = mapping.get("churn_yes_value", "")
        if churn_col in result.columns:
            result["churned"] = result[churn_col].apply(
                lambda x: 1 if str(x).strip() == str(churn_yes_value).strip() else 0
            )
            print(f"✅ Churn from user mapping: '{churn_col}'='{churn_yes_value}' → {result['churned'].sum()} churned")

    elif "churned" not in result.columns and detected["churn"]:
        col = detected["churn"]
        result["churned"] = pd.to_numeric(
            result[col].map({
                "Yes": 1, "No": 0, "yes": 1, "no": 0,
                "True": 1, "False": 0, True: 1, False: 0,
                1: 1, 0: 0, "1": 1, "0": 0,
                "Attrited Customer": 1, "Existing Customer": 0,
            }),
            errors="coerce"
        ).fillna(0).astype(int)
        print(f"✅ Churn auto-detected from '{col}': {result['churned'].sum()} churned")

    if "churned" in result.columns:
        result["churned"] = pd.to_numeric(
            result["churned"], errors="coerce"
        ).fillna(0).astype(int)

    # NUMERIC COLUMNS
    numeric_map = {
        "tenure_months":       detected["tenure"],
        "monthly_charges":     detected["monthly_charges"],
        "total_charges":       detected["total_charges"],
        "num_support_tickets": detected["support_tickets"],
    }
    for internal_name, source_col in numeric_map.items():
        if source_col and source_col in result.columns:
            result[internal_name] = pd.to_numeric(
                result[source_col], errors="coerce"
            ).fillna(0)
        elif internal_name not in result.columns:
            result[internal_name] = 0

    # CATEGORICAL COLUMNS
    cat_map = {
        "contract_type":    detected["contract_type"],
        "internet_service": detected["internet_service"],
        "payment_method":   detected["payment_method"],
    }
    for internal_name, source_col in cat_map.items():
        if source_col and source_col in result.columns:
            result[internal_name] = result[source_col].fillna("Unknown").astype(str)
        elif internal_name not in result.columns:
            result[internal_name] = "Unknown"

    return result


def get_active_dataset() -> pd.DataFrame:
    """Load the currently active dataset."""
    paths = [
        os.path.join(DATA_DIR, "uploaded_dataset.csv"),
        os.path.join(DATA_DIR, "WA_Fn-UseC_-Telco-Customer-Churn.csv"),
    ]

    mapping = get_column_mapping()

    for path in paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                df = standardize_df(df, mapping)
                print(f"✅ Dataset loaded: {len(df)} rows, churned: {df['churned'].sum() if 'churned' in df.columns else 'N/A'}")
                return df
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
                continue

    raise Exception(f"No dataset found in {DATA_DIR}")


def get_churn_breakdown(df: pd.DataFrame, col: str) -> list:
    """Generic churn breakdown for any column."""
    if col not in df.columns or "churned" not in df.columns:
        return []

    result = []
    for value in df[col].dropna().unique():
        subset     = df[df[col] == value]
        if len(subset) == 0:
            continue
        churned    = int(subset["churned"].sum())
        retained   = len(subset) - churned
        churn_rate = round(churned / len(subset) * 100, 1)
        result.append({
            "name":      str(value),
            "churned":   churned,
            "retained":  retained,
            "churnRate": churn_rate,
            "total":     len(subset),
            "customers": len(subset),
        })

    result.sort(key=lambda x: x["churnRate"], reverse=True)
    return result


def get_best_numeric_col(df: pd.DataFrame, preferred: str) -> str:
    """Returns best numeric column for financial metrics."""
    if preferred in df.columns and df[preferred].sum() > 0:
        return preferred

    skip = [
        "churned", "RowNumber", "rownumber", "id", "ID",
        "tenure_months", "num_support_tickets",
        "online_security", "tech_support", "streaming_tv",
        "streaming_movies", "phone_service", "multiple_lines",
    ]
    numeric_cols = df.select_dtypes(
        include=["float64", "int64"]
    ).columns.tolist()
    numeric_cols = [
        c for c in numeric_cols
        if c not in skip and df[c].sum() > 0 and df[c].mean() > 1
    ]
    return numeric_cols[0] if numeric_cols else None


def get_best_categorical_col(df, preferred, skip_cols=None) -> str:
    """Returns best categorical column."""
    if skip_cols is None:
        skip_cols = []

    if preferred in df.columns and \
       df[preferred].nunique() > 1 and \
       df[preferred].iloc[0] != "Unknown":
        return preferred

    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    base_skip = [
        "churned", "customerID", "customer_id",
        "Surname", "surname", "name", "Name",
    ]
    cat_cols = [
        c for c in cat_cols
        if c not in base_skip + skip_cols
        and df[c].nunique() <= 20
        and df[c].nunique() > 1
    ]
    return cat_cols[0] if cat_cols else None


# -----------------------------------------------
# API ENDPOINTS
# -----------------------------------------------

@router.get("/analytics/summary")
async def get_summary():
    try:
        df = get_active_dataset()

        total      = len(df)
        churned    = int(df["churned"].sum()) if "churned" in df.columns else 0
        retained   = total - churned
        churn_rate = round(churned / total * 100, 1) if total > 0 else 0

        charge_col = get_best_numeric_col(df, "monthly_charges")

        avg_monthly      = 0.0
        churner_monthly  = 0.0
        retained_monthly = 0.0

        if charge_col:
            avg_monthly = round(float(df[charge_col].mean()), 2)
            if churned > 0:
                churner_monthly = round(
                    float(df[df["churned"] == 1][charge_col].mean()), 2
                )
            if retained > 0:
                retained_monthly = round(
                    float(df[df["churned"] == 0][charge_col].mean()), 2
                )

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
            "metric_column":        charge_col,
        }

    except Exception as e:
        print(f"Summary error: {e}")
        return {"error": str(e)}


@router.get("/analytics/churn-by-contract")
async def churn_by_contract():
    try:
        df  = get_active_dataset()
        col = get_best_categorical_col(df, "contract_type")

        if not col:
            return {"data": [], "column_used": None}

        return {
            "data":        get_churn_breakdown(df, col),
            "column_used": col
        }
    except Exception as e:
        print(f"Contract error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-tenure")
async def churn_by_tenure():
    try:
        df         = get_active_dataset()
        tenure_col = get_best_numeric_col(df, "tenure_months")

        if not tenure_col or "churned" not in df.columns:
            return {"data": []}

        df[tenure_col] = pd.to_numeric(
            df[tenure_col], errors="coerce"
        ).fillna(0)

        max_val = df[tenure_col].max()

        if max_val <= 12:
            bins   = [0, 3, 6, 9, 12]
            labels = ["0-3", "4-6", "7-9", "10-12"]
        elif max_val <= 72:
            bins   = [0, 12, 24, 36, 48, 60, float("inf")]
            labels = ["0-12 months", "13-24 months", "25-36 months",
                      "37-48 months", "49-60 months", "60+ months"]
        else:
            step   = max_val / 6
            bins   = [i * step for i in range(7)]
            bins[-1] = float("inf")
            labels = [f"{int(i*step)}-{int((i+1)*step)}" for i in range(6)]

        df["tenure_group"] = pd.cut(
            df[tenure_col], bins=bins, labels=labels, right=True
        )

        result = []
        for label in labels:
            subset = df[df["tenure_group"] == label]
            if len(subset) == 0:
                continue
            churned    = int(subset["churned"].sum())
            churn_rate = round(churned / len(subset) * 100, 1)
            result.append({
                "tenure":    str(label),
                "churnRate": churn_rate,
                "customers": len(subset),
                "churned":   churned,
            })

        return {"data": result, "column_used": tenure_col}

    except Exception as e:
        print(f"Tenure error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-internet")
async def churn_by_internet():
    try:
        df  = get_active_dataset()
        col = get_best_categorical_col(
            df, "internet_service", ["contract_type"]
        )

        if not col:
            return {"data": [], "column_used": None}

        return {
            "data":        get_churn_breakdown(df, col),
            "column_used": col
        }
    except Exception as e:
        print(f"Internet error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-payment")
async def churn_by_payment():
    try:
        df  = get_active_dataset()
        col = get_best_categorical_col(
            df, "payment_method", ["contract_type", "internet_service"]
        )

        if not col:
            return {"data": [], "column_used": None}

        return {
            "data":        get_churn_breakdown(df, col),
            "column_used": col
        }
    except Exception as e:
        print(f"Payment error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-charges")
async def churn_by_charges():
    try:
        df         = get_active_dataset()
        charge_col = get_best_numeric_col(df, "monthly_charges")

        if not charge_col or "churned" not in df.columns:
            return {"data": []}

        df[charge_col] = pd.to_numeric(
            df[charge_col], errors="coerce"
        ).fillna(0)

        max_val = df[charge_col].max()
        step    = max_val / 6 if max_val > 0 else 20

        result = []
        for i in range(6):
            low    = round(i * step, 0)
            high   = round((i + 1) * step, 0)
            subset = df[
                (df[charge_col] >= low) &
                (df[charge_col] < high)
            ]
            if len(subset) == 0:
                continue
            churned    = int(subset["churned"].sum())
            churn_rate = round(churned / len(subset) * 100, 1)
            result.append({
                "range":     f"{int(low)}-{int(high)}",
                "churnRate": churn_rate,
                "customers": len(subset),
            })

        return {"data": result, "column_used": charge_col}

    except Exception as e:
        print(f"Charges error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/service-impact")
async def service_impact():
    try:
        df = get_active_dataset()

        known_services = [
            ("online_security",  "Online Security"),
            ("tech_support",     "Tech Support"),
            ("streaming_tv",     "Streaming TV"),
            ("streaming_movies", "Streaming Movies"),
            ("phone_service",    "Phone Service"),
        ]

        result = []

        # Try known service columns first
        for col, label in known_services:
            if col not in df.columns or "churned" not in df.columns:
                continue

            df[col] = pd.to_numeric(
                df[col].map({
                    "Yes": 1, "No": 0, "yes": 1, "no": 0,
                    "No internet service": 0, "No phone service": 0,
                    True: 1, False: 0, 1: 1, 0: 0,
                }),
                errors="coerce"
            ).fillna(0)

            with_svc    = df[df[col] == 1]
            without_svc = df[df[col] == 0]

            if len(with_svc) == 0 or len(without_svc) == 0:
                continue

            result.append({
                "service":        label,
                "withService":    round(with_svc["churned"].mean() * 100, 1),
                "withoutService": round(without_svc["churned"].mean() * 100, 1),
            })

        # If no known columns, auto-detect binary columns
        if not result:
            skip = ["churned", "RowNumber", "rownumber", "id", "ID"]
            for col in df.columns:
                if col in skip:
                    continue
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) == 2:
                    vals = set(str(v).lower() for v in unique_vals)
                    if vals <= {"0", "1", "yes", "no",
                                "true", "false", "1.0", "0.0"}:
                        df[col] = pd.to_numeric(
                            df[col], errors="coerce"
                        ).fillna(0)
                        with_svc    = df[df[col] == 1]
                        without_svc = df[df[col] == 0]
                        if len(with_svc) == 0 or len(without_svc) == 0:
                            continue
                        result.append({
                            "service":        col.replace("_", " ").title(),
                            "withService":    round(with_svc["churned"].mean() * 100, 1),
                            "withoutService": round(without_svc["churned"].mean() * 100, 1),
                        })
                        if len(result) >= 5:
                            break

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

        NUMERIC_FEATURES     = ["tenure_months", "monthly_charges", "total_charges", "num_support_tickets"]
        CATEGORICAL_FEATURES = ["contract_type", "internet_service", "payment_method"]
        BINARY_FEATURES      = ["online_security", "tech_support", "streaming_tv", "streaming_movies", "phone_service", "multiple_lines"]
        ALL_FEATURES         = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES

        # Add missing columns with defaults
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
                        "Yes": 1, "No": 0, "yes": 1, "no": 0,
                        "No internet service": 0, "No phone service": 0,
                        True: 1, False: 0, 1: 1, 0: 0,
                    }),
                    errors="coerce"
                ).fillna(0)

        X             = df[ALL_FEATURES].fillna(0)
        probabilities = ml_service.model.predict_proba(X)[:, 1]
        df            = df.copy()
        df["churn_probability"] = probabilities

        at_risk = df[df["churn_probability"] >= 0.5].copy()
        at_risk = at_risk.sort_values(
            "churn_probability", ascending=False
        ).head(20)

        # Find best ID column
        id_col = None
        for col in ["customerID", "customer_id", "CustomerId",
                    "id", "ID", "RowNumber"]:
            if col in at_risk.columns:
                id_col = col
                break

        result = []
        for idx, row in at_risk.iterrows():
            prob = float(row["churn_probability"])
            risk = (
                "Critical" if prob >= 0.75 else
                "High"     if prob >= 0.50 else
                "Medium"
            )
            customer_id = str(row[id_col]) if id_col else f"CUST_{idx}"

            result.append({
                "id":               customer_id,
                "churnProbability": round(prob, 3),
                "riskCategory":     risk,
                "tenure":           int(row.get("tenure_months", 0)),
                "monthlyCharges":   round(float(row.get("monthly_charges", 0)), 2),
                "contract":         str(row.get("contract_type", "Unknown")),
                "internetService":  str(row.get("internet_service", "Unknown")),
            })

        return {"data": result, "total": len(result)}

    except Exception as e:
        print(f"At-risk error: {e}")
        return {"data": [], "error": str(e)}


@router.get("/analytics/model-features")
async def get_model_features():
    """
    Returns the exact features the model uses for prediction
    mapped to the active dataset's actual column names.
    """
    try:
        df       = get_active_dataset()
        detected = detect_columns(df)

        def get_unique_values(col):
            if col and col in df.columns:
                vals = df[col].dropna().unique().tolist()
                return [str(v) for v in vals[:20]]
            return []

        def get_stats(col):
            if col and col in df.columns:
                numeric = pd.to_numeric(df[col], errors="coerce")
                return {
                    "min":  round(float(numeric.min()), 2),
                    "max":  round(float(numeric.max()), 2),
                    "mean": round(float(numeric.mean()), 2),
                }
            return {"min": 0, "max": 100, "mean": 0}

        features = [
            {
                "model_name":  "tenure_months",
                "label":       "Tenure",
                "description": "How long the customer has been with you",
                "type":        "numeric",
                "dataset_col": detected.get("tenure") or "tenure_months",
                "stats":       get_stats(detected.get("tenure")),
                "required":    True,
            },
            {
                "model_name":  "monthly_charges",
                "label":       "Monthly Charges",
                "description": "What the customer pays per month",
                "type":        "numeric",
                "dataset_col": detected.get("monthly_charges") or "monthly_charges",
                "stats":       get_stats(detected.get("monthly_charges")),
                "required":    True,
            },
            {
                "model_name":  "total_charges",
                "label":       "Total Charges",
                "description": "Total amount paid by customer",
                "type":        "numeric",
                "dataset_col": detected.get("total_charges") or "total_charges",
                "stats":       get_stats(detected.get("total_charges")),
                "required":    True,
            },
            {
                "model_name":  "num_support_tickets",
                "label":       "Support Tickets",
                "description": "Number of complaints or support requests",
                "type":        "numeric",
                "dataset_col": detected.get("support_tickets") or "num_support_tickets",
                "stats":       get_stats(detected.get("support_tickets")),
                "required":    False,
            },
            {
                "model_name":  "contract_type",
                "label":       "Contract / Plan Type",
                "description": "Type of contract or subscription",
                "type":        "categorical",
                "dataset_col": detected.get("contract_type") or "contract_type",
                "values":      get_unique_values(detected.get("contract_type")),
                "required":    True,
            },
            {
                "model_name":  "internet_service",
                "label":       "Service Type",
                "description": "Type of service the customer uses",
                "type":        "categorical",
                "dataset_col": detected.get("internet_service") or "internet_service",
                "values":      get_unique_values(detected.get("internet_service")),
                "required":    False,
            },
            {
                "model_name":  "payment_method",
                "label":       "Payment Method",
                "description": "How the customer pays",
                "type":        "categorical",
                "dataset_col": detected.get("payment_method") or "payment_method",
                "values":      get_unique_values(detected.get("payment_method")),
                "required":    False,
            },
            {
                "model_name":  "online_security",
                "label":       "Has Security / Protection",
                "description": "Customer has security service",
                "type":        "binary",
                "dataset_col": "online_security",
                "required":    False,
            },
            {
                "model_name":  "tech_support",
                "label":       "Has Tech Support",
                "description": "Customer has support service",
                "type":        "binary",
                "dataset_col": "tech_support",
                "required":    False,
            },
            {
                "model_name":  "streaming_tv",
                "label":       "Has Streaming TV",
                "description": "Customer uses streaming TV",
                "type":        "binary",
                "dataset_col": "streaming_tv",
                "required":    False,
            },
            {
                "model_name":  "streaming_movies",
                "label":       "Has Streaming Movies",
                "description": "Customer uses streaming movies",
                "type":        "binary",
                "dataset_col": "streaming_movies",
                "required":    False,
            },
            {
                "model_name":  "phone_service",
                "label":       "Has Phone Service",
                "description": "Customer has phone service",
                "type":        "binary",
                "dataset_col": "phone_service",
                "required":    False,
            },
            {
                "model_name":  "multiple_lines",
                "label":       "Has Multiple Lines",
                "description": "Customer has multiple lines",
                "type":        "binary",
                "dataset_col": "multiple_lines",
                "required":    False,
            },
        ]

        return {
            "features":   features,
            "total_rows": len(df),
            "churn_rate": round(
                df["churned"].mean() * 100, 1
            ) if "churned" in df.columns else 0,
        }

    except Exception as e:
        print(f"Model features error: {e}")
        return {"error": str(e), "features": []}