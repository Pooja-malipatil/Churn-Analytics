# backend/app/routers/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
import io
import os

router = APIRouter()

active_column_mapping = {
    "churn_col":       None,
    "churn_yes_value": None,
    "dataset_path":    None,
}
training_status = {
    "is_training":       False,
    "progress":          0,
    "message":           "No training started",
    "last_result":       None,
    "error":             None,
    "dataset_info":      None,
    "uploaded_filename": None,
}

# Store uploaded file info for column mapping
uploaded_file_info = {
    "filepath":    None,
    "filename":    None,
    "columns":     [],
    "sample_data": {},
    "num_rows":    0,
}


class ColumnMapping(BaseModel):
    """
    User only tells us the churn column.
    Everything else is auto-detected.
    """
    churn_col:       str
    churn_yes_value: str

@router.post("/upload/dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Step 1: Upload CSV and return column info for mapping.
    Does NOT train yet — waits for user to map columns.
    """

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    # Read file
    contents = await file.read()

    # Validate CSV
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV file — could not parse"
        )

    # Validate minimum rows
    if len(df) < 50:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset too small ({len(df)} rows). Need at least 50."
        )

    # Save file
    os.makedirs("data", exist_ok=True)
    current_file = os.path.abspath(__file__)
    backend_dir  = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    save_path    = os.path.join(backend_dir, "data", "uploaded_dataset.csv")
    os.makedirs(os.path.join(backend_dir, "data"), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(contents)

    # Get unique values for each column (for dropdown options)
    sample_values = {}
    for col in df.columns:
        unique_vals = df[col].dropna().unique()[:10].tolist()
        # Convert numpy types to Python types
        sample_values[col] = [str(v) for v in unique_vals]

    # Store file info
    uploaded_file_info.update({
        "filepath":    save_path,
        "filename":    file.filename,
        "columns":     list(df.columns),
        "sample_data": sample_values,
        "num_rows":    len(df),
    })

    print(f"✅ CSV uploaded — {len(df)} rows, {len(df.columns)} columns")

    return {
        "message":      "File uploaded! Please map your columns.",
        "filename":     file.filename,
        "num_rows":     len(df),
        "num_columns":  len(df.columns),
        "columns":      list(df.columns),
        "sample_values": sample_values,
        "status":       "awaiting_mapping",
    }


@router.post("/upload/train")
async def start_training(
    mapping: ColumnMapping,
    background_tasks: BackgroundTasks,
):
    """
    Step 2: User submits column mapping → start training.
    """

    if not uploaded_file_info["filepath"]:
        raise HTTPException(
            status_code=400,
            detail="No file uploaded. Please upload a CSV first."
        )

    # Validate churn column exists
    df = pd.read_csv(uploaded_file_info["filepath"])
    if mapping.churn_col not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Column '{mapping.churn_col}' not found in dataset"
        )

    # Reset training status
    training_status.update({
        "is_training":       True,
        "progress":          0,
        "message":           "Starting training...",
        "error":             None,
        "last_result":       None,
        "dataset_info":      None,
        "uploaded_filename": uploaded_file_info["filename"],
    })

    # Start training in background
    background_tasks.add_task(
        retrain_model,
        uploaded_file_info["filepath"],
        uploaded_file_info["num_rows"],
        mapping,
    )

    return {
        "message": "Training started!",
        "status":  "training_started",
    }


@router.get("/upload/status")
async def get_training_status():
    return training_status


@router.get("/upload/dataset/info")
@router.get("/upload/dataset/info")
async def get_dataset_info():
    import os
    current_file = os.path.abspath(__file__)
    backend_dir  = os.path.dirname(
                     os.path.dirname(
                       os.path.dirname(current_file)
                     )
                   )

    paths_to_check = [
        (
            os.path.join(backend_dir, "data", "uploaded_dataset.csv"),
            "uploaded_dataset.csv"
        ),
        (
            os.path.join(backend_dir, "data", "WA_Fn-UseC_-Telco-Customer-Churn.csv"),
            "WA_Fn-UseC_-Telco-Customer-Churn.csv"
        ),
    ]

    for filepath, filename in paths_to_check:
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)

                churn_col  = None
                churn_rate = "Unknown"

                for col in ["Churn", "churned", "churn", "is_churned"]:
                    if col in df.columns:
                        churn_col = col
                        break

                if churn_col:
                    if df[churn_col].dtype == object:
                        churn_rate = f"{(df[churn_col] == 'Yes').mean():.1%}"
                    else:
                        churn_rate = f"{df[churn_col].mean():.1%}"

                return {
                    "filename":       filename,
                    "rows":           len(df),
                    "columns":        list(df.columns),
                    "num_columns":    len(df.columns),
                    "churn_rate":     churn_rate,
                    "missing_values": int(df.isnull().sum().sum()),
                    "file_size_kb":   round(
                        os.path.getsize(filepath) / 1024, 1
                    ),
                }
            except Exception as e:
                continue

    return {"message": "No dataset found"}


def apply_column_mapping(df: pd.DataFrame, mapping: ColumnMapping) -> pd.DataFrame:
    """
    User provides churn column.
    Machine auto-detects everything else.
    """
    result = pd.DataFrame()

    # -----------------------------------------------
    # CHURN — from user selection
    # -----------------------------------------------
    result["churned"] = df[mapping.churn_col].apply(
        lambda x: 1 if str(x).strip() == str(mapping.churn_yes_value).strip()
        else 0
    )

    # -----------------------------------------------
    # AUTO DETECT ALL OTHER COLUMNS
    # -----------------------------------------------
    cols = list(df.columns)

    def find_col(candidates):
        """Find first matching column from candidates list."""
        for c in candidates:
            if c in cols:
                return c
        return None

    def to_numeric_col(col_name, default=0):
        if col_name and col_name in df.columns:
            return pd.to_numeric(
                df[col_name], errors="coerce"
            ).fillna(default)
        return default

    def to_binary_col(col_name, default=0):
        if col_name and col_name in df.columns:
            return df[col_name].apply(
                lambda x: 1 if str(x).lower() in
                ["yes", "1", "true", "y"] else 0
            )
        return default

    def to_string_col(col_name, default="Unknown"):
        if col_name and col_name in df.columns:
            return df[col_name].fillna(default).astype(str)
        return default

    # TENURE
    tenure_col = find_col([
        "tenure", "Tenure", "tenure_months",
        "months", "duration", "age_months",
        "customer_age", "subscription_months"
    ])
    result["tenure_months"] = to_numeric_col(tenure_col, 0)

    # MONTHLY CHARGES
    monthly_col = find_col([
        "MonthlyCharges", "monthly_charges", "monthly_charge",
        "charges", "bill", "monthly_bill", "monthly_fee",
        "subscription_fee", "price", "amount"
    ])
    result["monthly_charges"] = to_numeric_col(monthly_col, 0.0)

    # TOTAL CHARGES
    total_col = find_col([
        "TotalCharges", "total_charges", "total_charge",
        "total_bill", "lifetime_value", "total_spent",
        "total_revenue", "ltv"
    ])
    result["total_charges"] = to_numeric_col(total_col, 0.0)

    # If total charges is 0 but we have monthly and tenure
    # calculate it automatically
    zero_total = result["total_charges"] == 0
    if zero_total.any():
        result.loc[zero_total, "total_charges"] = (
            result.loc[zero_total, "monthly_charges"] *
            result.loc[zero_total, "tenure_months"]
        )

    # CONTRACT TYPE
    contract_col = find_col([
        "Contract", "contract_type", "contract",
        "plan", "subscription_type", "plan_type",
        "billing_type", "billing_cycle"
    ])
    result["contract_type"] = to_string_col(
        contract_col, "Month-to-month"
    )

    # INTERNET SERVICE
    internet_col = find_col([
        "InternetService", "internet_service", "internet",
        "service_type", "connection_type", "internet_type"
    ])
    result["internet_service"] = to_string_col(internet_col, "DSL")

    # PAYMENT METHOD
    payment_col = find_col([
        "PaymentMethod", "payment_method", "payment",
        "billing_method", "payment_type"
    ])
    result["payment_method"] = to_string_col(
        payment_col, "Electronic check"
    )

    # ONLINE SECURITY
    security_col = find_col([
        "OnlineSecurity", "online_security",
        "security", "online_sec"
    ])
    result["online_security"] = to_binary_col(security_col, 0)

    # TECH SUPPORT
    support_col = find_col([
        "TechSupport", "tech_support",
        "technical_support", "support"
    ])
    result["tech_support"] = to_binary_col(support_col, 0)

    # STREAMING TV
    tv_col = find_col([
        "StreamingTV", "streaming_tv",
        "tv", "television", "stream_tv"
    ])
    result["streaming_tv"] = to_binary_col(tv_col, 0)

    # STREAMING MOVIES
    movies_col = find_col([
        "StreamingMovies", "streaming_movies",
        "movies", "stream_movies", "vod"
    ])
    result["streaming_movies"] = to_binary_col(movies_col, 0)

    # PHONE SERVICE
    phone_col = find_col([
        "PhoneService", "phone_service",
        "phone", "telephone", "voice"
    ])
    result["phone_service"] = to_binary_col(phone_col, 1)

    # MULTIPLE LINES
    lines_col = find_col([
        "MultipleLines", "multiple_lines",
        "multi_lines", "lines"
    ])
    result["multiple_lines"] = to_binary_col(lines_col, 0)

    # SUPPORT TICKETS
    tickets_col = find_col([
        "num_support_tickets", "support_tickets",
        "tickets", "complaints", "num_complaints"
    ])
    result["num_support_tickets"] = to_numeric_col(tickets_col, 0)

    # Log what was auto-detected
    print(f"✅ Auto-detected columns:")
    print(f"   tenure:          {tenure_col}")
    print(f"   monthly_charges: {monthly_col}")
    print(f"   total_charges:   {total_col}")
    print(f"   contract:        {contract_col}")
    print(f"   internet:        {internet_col}")
    print(f"   payment:         {payment_col}")
    print(f"   online_security: {security_col}")
    print(f"   tech_support:    {support_col}")

    return result

async def retrain_model(filepath, num_rows, mapping):
    # Save mapping globally for analytics to use
    active_column_mapping["churn_col"]       = mapping.churn_col
    active_column_mapping["churn_yes_value"] = mapping.churn_yes_value
    active_column_mapping["dataset_path"]    = filepath
    # ... rest of function
async def retrain_model(
    filepath: str,
    num_rows:  int,
    mapping:   ColumnMapping,
):
    """Background task — applies mapping then trains model."""
    try:
        training_status.update({
            "progress": 10,
            "message":  "Loading dataset..."
        })

        df_raw = pd.read_csv(filepath)

        training_status.update({
            "progress": 20,
            "message":  "Applying column mapping..."
        })

        # Apply user's column mapping
        df = apply_column_mapping(df_raw, mapping)

        # Analyze dataset
        churn_rate       = df["churned"].mean()
        churned_count    = int(df["churned"].sum())
        retained_count   = int((df["churned"] == 0).sum())
        missing_values   = int(df.isnull().sum().sum())

        training_status.update({
            "progress": 25,
            "message":  "Analyzing dataset...",
            "dataset_info": {
                "total_rows":     len(df),
                "total_columns":  len(df.columns),
                "columns":        list(df.columns),
                "churn_rate":     f"{churn_rate:.1%}",
                "churned_count":  churned_count,
                "retained_count": retained_count,
                "missing_values": missing_values,
            }
        })

        # Validate classes
        if df["churned"].nunique() < 2:
            raise Exception(
                f"After mapping, dataset has only ONE class. "
                f"Found {churned_count} churned and {retained_count} retained. "
                f"Please check your churn column and 'churned value' selection."
            )

        if churned_count < 10:
            raise Exception(
                f"Too few churned customers ({churned_count}). "
                f"Need at least 10. Check your column mapping."
            )

        training_status.update({
            "progress": 40,
            "message":  "Training Random Forest..."
        })

        from app.ml.train import train_models
        best_model, metrics = train_models(df)

        training_status.update({
            "progress": 80,
            "message":  "Building SHAP explainer..."
        })

        from app.services.ml_service import ml_service
        await ml_service.initialize()

        training_status.update({
            "is_training": False,
            "progress":    100,
            "message":     "Training complete! New model is ready.",
            "last_result": {
                "rows_trained":        num_rows,
                "churn_rate":          f"{churn_rate:.1%}",
                "churned_customers":   churned_count,
                "retained_customers":  retained_count,
                "random_forest":       metrics.get("Random Forest", {}),
                "logistic_regression": metrics.get("Logistic Regression", {}),
            },
            "error": None,
        })

        print("✅ Model retrained successfully!")

    except Exception as e:
        training_status.update({
            "is_training": False,
            "progress":    0,
            "message":     "Training failed!",
            "error":       str(e),
        })
        print(f"❌ Training error: {e}")