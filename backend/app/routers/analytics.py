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
    Works for ANY dataset by analyzing column names and data types.
    Returns a dict mapping our internal names to actual column names.
    """
    cols       = list(df.columns)
    cols_lower = [c.lower() for c in cols]
    detected   = {}

    def find(keywords: list) -> str:
        """Find first column matching any keyword."""
        for kw in keywords:
            for i, c in enumerate(cols_lower):
                if kw in c:
                    return cols[i]
        return None

    # CHURN — most important
    detected["churn"] = find([
        "churn", "exited", "exit", "attrition",
        "left", "cancelled", "churned", "is_churn",
        "target", "label"
    ])

    # TENURE — how long customer has been with company
    detected["tenure"] = find([
        "tenure", "months", "duration", "age_months",
        "subscription_months", "customer_age", "years"
    ])

    # MONTHLY CHARGES — what customer pays per month
    detected["monthly_charges"] = find([
        "monthly", "monthly_charge", "monthlycharge",
        "monthly_fee", "monthly_bill", "subscription",
        "price", "fee", "rate", "premium"
    ])

    # TOTAL CHARGES — total paid overall
    detected["total_charges"] = find([
        "total_charge", "totalcharge", "total_bill",
        "total_paid", "lifetime_value", "ltv",
        "total_spend", "cumulative"
    ])

    # SALARY/ESTIMATED INCOME — if no charges found
    if not detected["monthly_charges"]:
        detected["monthly_charges"] = find([
            "salary", "income", "estimated",
            "revenue", "amount", "value"
        ])

    # BALANCE — financial datasets
    if not detected["total_charges"]:
        detected["total_charges"] = find([
            "balance", "account_balance",
            "total_balance", "net_worth"
        ])

    # CONTRACT / PLAN TYPE
    detected["contract_type"] = find([
        "contract", "plan", "subscription_type",
        "billing_type", "billing_cycle", "tier",
        "membership", "package"
    ])

    # GEOGRAPHY / LOCATION — often in bank datasets
    if not detected["contract_type"]:
        detected["contract_type"] = find([
            "geography", "location", "region",
            "country", "state", "city", "zone"
        ])

    # INTERNET / SERVICE TYPE
    detected["internet_service"] = find([
        "internet", "service_type", "connection",
        "broadband", "network", "access_type"
    ])

    # PAYMENT METHOD
    detected["payment_method"] = find([
        "payment", "billing_method", "pay_method",
        "payment_type", "payment_channel"
    ])

    # SUPPORT TICKETS / COMPLAINTS
    detected["support_tickets"] = find([
        "ticket", "complaint", "support",
        "num_complaint", "issues", "calls",
        "numofproducts", "num_products", "products"
    ])

    # AGE
    detected["age"] = find(["age", "customer_age", "age_years"])

    # GENDER
    detected["gender"] = find(["gender", "sex"])

    # CREDIT SCORE
    detected["credit_score"] = find([
        "credit", "score", "creditscore", "credit_score"
    ])

    # ACTIVE MEMBER / ENGAGEMENT
    detected["is_active"] = find([
        "active", "isactive", "is_active",
        "engaged", "engagement"
    ])

    print(f"🔍 Auto-detected columns: {detected}")
    return detected


def standardize_df(df: pd.DataFrame, mapping=None) -> pd.DataFrame:
    """
    Standardize any dataframe to our internal format.
    Uses user mapping first, then auto-detection.
    """
    detected = detect_columns(df)
    result   = df.copy()

    # -----------------------------------------------
    # CHURN COLUMN
    # -----------------------------------------------
    if mapping and mapping.get("churn_col"):
        # User explicitly told us the churn column
        churn_col       = mapping["churn_col"]
        churn_yes_value = mapping.get("churn_yes_value", "")

        if churn_col in result.columns:
            result["churned"] = result[churn_col].apply(
                lambda x: 1 if str(x).strip() == str(churn_yes_value).strip()
                else 0
            )
            print(f"✅ Churn from user mapping: "
                  f"'{churn_col}' = '{churn_yes_value}' "
                  f"→ {result['churned'].sum()} churned")

    elif "churned" not in result.columns and detected["churn"]:
        # Auto-detect churn column
        col = detected["churn"]
        result["churned"] = pd.to_numeric(
            result[col].map({
                "Yes": 1, "No": 0, "yes": 1, "no": 0,
                "True": 1, "False": 0, True: 1, False: 0,
                1: 1, 0: 0, "1": 1, "0": 0,
                "Attrited Customer": 1,
                "Existing Customer": 0,
            }),
            errors="coerce"
        ).fillna(0).astype(int)
        print(f"✅ Churn auto-detected from '{col}': "
              f"{result['churned'].sum()} churned")

    # Fix churned type
    if "churned" in result.columns:
        result["churned"] = pd.to_numeric(
            result["churned"], errors="coerce"
        ).fillna(0).astype(int)

    # -----------------------------------------------
    # NUMERIC COLUMNS
    # -----------------------------------------------
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

    # -----------------------------------------------
    # CATEGORICAL COLUMNS
    # -----------------------------------------------
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
                print(f"✅ Dataset loaded: {len(df)} rows, "
                      f"churned: {df['churned'].sum()}")
                return df
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

    raise Exception(f"No dataset found in {DATA_DIR}")


def get_churn_breakdown(df: pd.DataFrame, col: str) -> list:
    """
    Generic function to get churn breakdown for any column.
    Works for contract type, geography, gender, any categorical column.
    """
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
    """
    Returns preferred column if it exists and has meaningful data,
    otherwise finds the best numeric column.
    """
    if preferred in df.columns and df[preferred].sum() > 0:
        return preferred

    # Find numeric columns with meaningful values
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


@router.get("/analytics/summary")
async def get_summary():
    try:
        df = get_active_dataset()

        total      = len(df)
        churned    = int(df["churned"].sum()) if "churned" in df.columns else 0
        retained   = total - churned
        churn_rate = round(churned / total * 100, 1) if total > 0 else 0

        # Find best column for financial metrics
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
    """
    Works for ANY categorical column.
    Uses contract_type if available, otherwise
    uses best available categorical column.
    """
    try:
        df = get_active_dataset()

        # Try contract_type first, then any categorical column
        col = None
        if "contract_type" in df.columns and \
           df["contract_type"].nunique() > 1 and \
           df["contract_type"].iloc[0] != "Unknown":
            col = "contract_type"
        else:
            # Find best categorical column
            cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
            skip     = [
                "churned", "customerID", "customer_id",
                "Surname", "surname", "name", "Name",
                "internet_service", "payment_method",
            ]
            cat_cols = [
                c for c in cat_cols
                if c not in skip and df[c].nunique() <= 20
                and df[c].nunique() > 1
            ]
            col = cat_cols[0] if cat_cols else None

        if not col:
            return {"data": [], "column_used": None}

        data = get_churn_breakdown(df, col)
        return {"data": data, "column_used": col}

    except Exception as e:
        print(f"Contract error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-tenure")
async def churn_by_tenure():
    """Works for any numeric tenure-like column."""
    try:
        df = get_active_dataset()

        tenure_col = get_best_numeric_col(df, "tenure_months")

        if not tenure_col or "churned" not in df.columns:
            return {"data": []}

        df[tenure_col] = pd.to_numeric(
            df[tenure_col], errors="coerce"
        ).fillna(0)

        max_val = df[tenure_col].max()

        # Create dynamic bins based on data range
        if max_val <= 12:
            bins   = [0, 3, 6, 9, 12]
            labels = ["0-3", "4-6", "7-9", "10-12"]
        elif max_val <= 72:
            bins   = [0, 12, 24, 36, 48, 60, float("inf")]
            labels = [
                "0-12 months", "13-24 months", "25-36 months",
                "37-48 months", "49-60 months", "60+ months"
            ]
        else:
            step   = max_val / 6
            bins   = [i * step for i in range(7)]
            bins[-1] = float("inf")
            labels = [
                f"{int(i*step)}-{int((i+1)*step)}"
                for i in range(6)
            ]

        df["tenure_group"] = pd.cut(
            df[tenure_col],
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
    """
    Works for any categorical column.
    Uses internet_service if available,
    otherwise uses next best categorical column.
    """
    try:
        df = get_active_dataset()

        col = None
        if "internet_service" in df.columns and \
           df["internet_service"].nunique() > 1 and \
           df["internet_service"].iloc[0] != "Unknown":
            col = "internet_service"
        else:
            cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
            skip     = [
                "churned", "customerID", "customer_id",
                "Surname", "surname", "name", "Name",
                "contract_type", "payment_method",
            ]
            cat_cols = [
                c for c in cat_cols
                if c not in skip and df[c].nunique() <= 20
                and df[c].nunique() > 1
            ]
            col = cat_cols[1] if len(cat_cols) > 1 else (
                cat_cols[0] if cat_cols else None
            )

        if not col:
            return {"data": [], "column_used": None}

        data = get_churn_breakdown(df, col)
        return {"data": data, "column_used": col}

    except Exception as e:
        print(f"Internet error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-payment")
async def churn_by_payment():
    """
    Works for any categorical column.
    Uses payment_method if available,
    otherwise uses next best categorical column.
    """
    try:
        df = get_active_dataset()

        col = None
        if "payment_method" in df.columns and \
           df["payment_method"].nunique() > 1 and \
           df["payment_method"].iloc[0] != "Unknown":
            col = "payment_method"
        else:
            cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
            skip     = [
                "churned", "customerID", "customer_id",
                "Surname", "surname", "name", "Name",
                "contract_type", "internet_service",
            ]
            cat_cols = [
                c for c in cat_cols
                if c not in skip and df[c].nunique() <= 20
                and df[c].nunique() > 1
            ]
            col = cat_cols[2] if len(cat_cols) > 2 else (
                cat_cols[0] if cat_cols else None
            )

        if not col:
            return {"data": [], "column_used": None}

        data = get_churn_breakdown(df, col)
        return {"data": data, "column_used": col}

    except Exception as e:
        print(f"Payment error: {e}")
        return {"error": str(e), "data": []}


@router.get("/analytics/churn-by-charges")
async def churn_by_charges():
    """Works for any numeric column representing charges/value."""
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
    """
    Works for any binary columns.
    Uses known service columns if available,
    otherwise finds binary columns automatically.
    """
    try:
        df = get_active_dataset()

        # Known service columns
        known = [
            ("online_security",  "Online Security"),
            ("tech_support",     "Tech Support"),
            ("streaming_tv",     "Streaming TV"),
            ("streaming_movies", "Streaming Movies"),
            ("phone_service",    "Phone Service"),
        ]

        # Find binary columns (0/1 or Yes/No)
        binary_cols = []
        for col in df.columns:
            if col in ["churned", "RowNumber", "rownumber"]:
                continue
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) == 2:
                vals = set(str(v).lower() for v in unique_vals)
                if vals <= {"0", "1", "yes", "no",
                            "true", "false", "1.0", "0.0"}:
                    binary_cols.append(col)

        result = []

        # First try known service columns
        for col, label in known:
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

        # If no known columns found, use auto-detected binary columns
        if not result:
            for col in binary_cols[:5]:
                df[col] = pd.to_numeric(
                    df[col], errors="coerce"
                ).fillna(0)

                with_svc    = df[df[col] == 1]
                without_svc = df[df[col] == 0]

                if len(with_svc) == 0 or len(without_svc) == 0:
                    continue

                result.append({
                    "service": col.replace("_", " ").title(),
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
    """Get top at-risk customers using ML model."""
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
        ALL_FEATURES = (
            NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES
        )

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

            customer_id = (
                str(row[id_col]) if id_col else f"CUST_{idx}"
            )

            # Find best display values
            contract = str(row.get("contract_type", "Unknown"))
            internet = str(row.get("internet_service", "Unknown"))
            monthly  = round(float(row.get("monthly_charges", 0)), 2)
            tenure   = int(row.get("tenure_months", 0))

            result.append({
                "id":               customer_id,
                "churnProbability": round(prob, 3),
                "riskCategory":     risk,
                "tenure":           tenure,
                "monthlyCharges":   monthly,
                "contract":         contract,
                "internetService":  internet,
            })

        return {"data": result, "total": len(result)}

    except Exception as e:
        print(f"At-risk error: {e}")
        return {"data": [], "error": str(e)}