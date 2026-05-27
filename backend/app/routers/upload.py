# backend/app/routers/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
import io
import os

router = APIRouter()

# Store training status in memory
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
    User tells us which column maps to what.
    All fields optional — user only maps what exists.
    """
    churn_col:           str
    churn_yes_value:     str
    tenure_col:          Optional[str] = None
    monthly_charges_col: Optional[str] = None
    total_charges_col:   Optional[str] = None
    contract_col:        Optional[str] = None
    internet_col:        Optional[str] = None
    payment_col:         Optional[str] = None
    online_security_col: Optional[str] = None
    tech_support_col:    Optional[str] = None


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
    Apply user's column mapping to create standardized dataframe.
    """

    result = pd.DataFrame()

    # CHURN column — required
    result["churned"] = df[mapping.churn_col].apply(
        lambda x: 1 if str(x).strip() == str(mapping.churn_yes_value).strip()
        else 0
    )

    # TENURE
    if mapping.tenure_col and mapping.tenure_col in df.columns:
        result["tenure_months"] = pd.to_numeric(
            df[mapping.tenure_col], errors="coerce"
        ).fillna(0)
    else:
        result["tenure_months"] = 0

    # MONTHLY CHARGES
    if mapping.monthly_charges_col and mapping.monthly_charges_col in df.columns:
        result["monthly_charges"] = pd.to_numeric(
            df[mapping.monthly_charges_col], errors="coerce"
        ).fillna(0)
    else:
        result["monthly_charges"] = 0.0

    # TOTAL CHARGES
    if mapping.total_charges_col and mapping.total_charges_col in df.columns:
        result["total_charges"] = pd.to_numeric(
            df[mapping.total_charges_col], errors="coerce"
        ).fillna(0)
    else:
        result["total_charges"] = result["monthly_charges"] * result["tenure_months"]

    # CONTRACT TYPE
    if mapping.contract_col and mapping.contract_col in df.columns:
        result["contract_type"] = df[mapping.contract_col].fillna("Month-to-month")
    else:
        result["contract_type"] = "Month-to-month"

    # INTERNET SERVICE
    if mapping.internet_col and mapping.internet_col in df.columns:
        result["internet_service"] = df[mapping.internet_col].fillna("DSL")
    else:
        result["internet_service"] = "DSL"

    # PAYMENT METHOD
    if mapping.payment_col and mapping.payment_col in df.columns:
        result["payment_method"] = df[mapping.payment_col].fillna("Electronic check")
    else:
        result["payment_method"] = "Electronic check"

    # ONLINE SECURITY
    if mapping.online_security_col and mapping.online_security_col in df.columns:
        result["online_security"] = df[mapping.online_security_col].apply(
            lambda x: 1 if str(x).lower() in ["yes", "1", "true"] else 0
        )
    else:
        result["online_security"] = 0

    # TECH SUPPORT
    if mapping.tech_support_col and mapping.tech_support_col in df.columns:
        result["tech_support"] = df[mapping.tech_support_col].apply(
            lambda x: 1 if str(x).lower() in ["yes", "1", "true"] else 0
        )
    else:
        result["tech_support"] = 0

    # Add remaining required columns with defaults
    defaults = {
        "streaming_tv":        0,
        "streaming_movies":    0,
        "phone_service":       1,
        "multiple_lines":      0,
        "num_support_tickets": 0,
    }
    for col, val in defaults.items():
        result[col] = val

    return result


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