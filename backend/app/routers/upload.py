# backend/app/routers/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
import pandas as pd
import io
import os

router = APIRouter()

# Store training status in memory
training_status = {
    "is_training": False,
    "progress":    0,
    "message":     "No training started",
    "last_result": None,
    "error":       None,
}


@router.post("/upload/dataset")
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    # Read file
    contents = await file.read()

    # Validate it's a valid CSV
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
            detail=f"Dataset too small ({len(df)} rows). Need at least 50 rows."
        )

    print(f"✅ CSV accepted — {len(df)} rows, columns: {list(df.columns)}")

    # Save uploaded file
    os.makedirs("data", exist_ok=True)
    save_path = "data/uploaded_dataset.csv"
    with open(save_path, "wb") as f:
        f.write(contents)

    # Reset training status
    training_status.update({
        "is_training": True,
        "progress":    0,
        "message":     "Dataset uploaded. Starting training...",
        "error":       None,
        "last_result": None,
    })

    # Start training in background
    background_tasks.add_task(retrain_model, save_path, len(df))

    return {
        "message":  "Dataset uploaded! Training started.",
        "filename": file.filename,
        "rows":     len(df),
        "columns":  list(df.columns),
        "status":   "training_started",
    }


@router.get("/upload/status")
async def get_training_status():
    return training_status


@router.get("/upload/dataset/info")
async def get_dataset_info():
    try:
        df = pd.read_csv("data/WA_Fn-UseC_-Telco-Customer-Churn.csv")
        return {
            "filename":   "WA_Fn-UseC_-Telco-Customer-Churn.csv",
            "rows":       len(df),
            "columns":    list(df.columns),
            "churn_rate": f"{(df['Churn'] == 'Yes').mean():.1%}",
        }
    except Exception:
        return {"message": "No dataset loaded"}


async def retrain_model(filepath: str, num_rows: int):
    """Background task that retrains the ML model."""
    try:
        training_status.update({
            "progress": 10,
            "message":  "Loading and cleaning dataset..."
        })

        from app.ml.train import load_kaggle_data, load_custom_data, train_models

        training_status.update({
            "progress": 25,
            "message":  "Preprocessing features..."
        })

        # Try Kaggle format first then custom format
        try:
            df = load_kaggle_data(filepath)
            print("✅ Loaded as Kaggle format")
        except Exception:
            try:
                df = load_custom_data(filepath)
                print("✅ Loaded as custom format")
            except Exception as e:
                raise Exception(f"Could not load dataset: {e}")

        training_status.update({
            "progress": 40,
            "message":  "Training Random Forest model..."
        })

        best_model, metrics = train_models(df)

        training_status.update({
            "progress": 80,
            "message":  "Building SHAP explainer..."
        })

        # Reload ML service with new model
        from app.services.ml_service import ml_service
        await ml_service.initialize()

        training_status.update({
            "is_training": False,
            "progress":    100,
            "message":     "Training complete! New model is ready.",
            "last_result": {
                "rows_trained":        num_rows,
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