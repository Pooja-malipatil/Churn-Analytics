# backend/app/ml/train.py

import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
)
import shap
import joblib
from pathlib import Path

# -----------------------------------------------
# FEATURE DEFINITIONS
# -----------------------------------------------

NUMERIC_FEATURES = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "num_support_tickets",
]

CATEGORICAL_FEATURES = [
    "contract_type",
    "internet_service",
    "payment_method",
]

BINARY_FEATURES = [
    "online_security",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
    "phone_service",
    "multiple_lines",
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES
TARGET = "churned"

MODEL_PATH = Path("models_saved/")
MODEL_PATH.mkdir(exist_ok=True)


def load_kaggle_data(filepath: str) -> pd.DataFrame:
    """
    Loads and cleans the Kaggle Telco dataset.
    
    WHY we need cleaning:
    - Column names use CamelCase → we want snake_case
    - Churn column is "Yes"/"No" → we need 1/0
    - TotalCharges is a string → we need float
    - Binary columns are "Yes"/"No" → we need 1/0
    - Some columns have spaces as values → need to handle
    """
    
    print(f"📂 Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    print(f"   Raw shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    # -----------------------------------------------
    # RENAME COLUMNS to match our system
    # -----------------------------------------------
    df = df.rename(columns={
        "customerID":       "customer_id",
        "tenure":           "tenure_months",
        "MonthlyCharges":   "monthly_charges",
        "TotalCharges":     "total_charges",
        "Contract":         "contract_type",
        "InternetService":  "internet_service",
        "PaymentMethod":    "payment_method",
        "OnlineSecurity":   "online_security",
        "TechSupport":      "tech_support",
        "StreamingTV":      "streaming_tv",
        "StreamingMovies":  "streaming_movies",
        "PhoneService":     "phone_service",
        "MultipleLines":    "multiple_lines",
        "Churn":            "churned",
        "gender":           "gender",
        "SeniorCitizen":    "senior_citizen",
        "Partner":          "partner",
        "Dependents":       "dependents",
    })
    
    # -----------------------------------------------
    # FIX TOTAL CHARGES
    # In the Kaggle dataset TotalCharges is stored as
    # a string and some rows have empty spaces " "
    # We convert to float and fill missing with 0
    # -----------------------------------------------
    df["total_charges"] = pd.to_numeric(
        df["total_charges"], errors="coerce"
    ).fillna(0.0)
    
    # -----------------------------------------------
    # FIX TARGET COLUMN
    # "Yes" → 1, "No" → 0
    # -----------------------------------------------
    df["churned"] = df["churned"].map({"Yes": 1, "No": 0})
    
    # -----------------------------------------------
    # FIX BINARY COLUMNS
    # "Yes" → 1, "No" → 0
    # Some values are "No internet service" or
    # "No phone service" — treat these as 0
    # -----------------------------------------------
    binary_cols = [
        "online_security", "tech_support",
        "streaming_tv", "streaming_movies",
        "phone_service", "multiple_lines",
    ]
    
    for col in binary_cols:
        if col in df.columns:
            df[col] = df[col].map(
                {
                    "Yes": 1, "No": 0,
                    "No internet service": 0,
                    "No phone service": 0,
                    True: 1, False: 0,
                    1: 1, 0: 0,
                }
            ).fillna(0).astype(int)
    
    # -----------------------------------------------
    # ADD MISSING COLUMN
    # Kaggle dataset has no support tickets column
    # We add it as 0 for all customers
    # In real system this would come from CRM data
    # -----------------------------------------------
    if "num_support_tickets" not in df.columns:
        df["num_support_tickets"] = 0
    
    # Drop rows where target is missing
    df = df.dropna(subset=["churned"])
    
    print(f"   Clean shape: {df.shape}")
    print(f"   Churn rate: {df['churned'].mean():.1%}")
    
    return df


def build_preprocessor():
    """Same preprocessor as before."""
    
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    
    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )),
    ])
    
    binary_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
    ])
    
    return ColumnTransformer(
        transformers=[
            ("numeric",      numeric_transformer,      NUMERIC_FEATURES),
            ("categorical",  categorical_transformer,  CATEGORICAL_FEATURES),
            ("binary",       binary_transformer,       BINARY_FEATURES),
        ],
        remainder="drop",
    )


def train_models(df: pd.DataFrame):
    """Full training workflow."""
    
    X = df[ALL_FEATURES]
    y = df[TARGET]
    
    # -----------------------------------------------
    # TRAIN TEST SPLIT
    # -----------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    
    print(f"\n📊 Train: {len(X_train)} | Test: {len(X_test)}")
    
    # -----------------------------------------------
    # TRAIN RANDOM FOREST
    # -----------------------------------------------
    print("\n🌲 Training Random Forest...")
    
    rf_pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])
    rf_pipeline.fit(X_train, y_train)
    
    # -----------------------------------------------
    # TRAIN LOGISTIC REGRESSION
    # -----------------------------------------------
    print("📈 Training Logistic Regression...")
    
    lr_pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )),
    ])
    lr_pipeline.fit(X_train, y_train)
    
    # -----------------------------------------------
    # EVALUATE
    # -----------------------------------------------
    print("\n📋 EVALUATION RESULTS:")
    print("=" * 50)
    
    metrics = {}
    
    for name, pipeline in [
        ("Random Forest",       rf_pipeline),
        ("Logistic Regression", lr_pipeline),
    ]:
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        report = classification_report(
            y_test, y_pred, output_dict=True
        )
        auc = roc_auc_score(y_test, y_prob)
        
        print(f"\n  {name}:")
        print(f"  Accuracy:  {report['accuracy']:.3f}")
        print(f"  Precision: {report['1']['precision']:.3f}")
        print(f"  Recall:    {report['1']['recall']:.3f}")
        print(f"  F1:        {report['1']['f1-score']:.3f}")
        print(f"  ROC-AUC:   {auc:.3f}")
        
        metrics[name] = {
            "accuracy":  report["accuracy"],
            "roc_auc":   auc,
            "precision": report["1"]["precision"],
            "recall":    report["1"]["recall"],
            "f1":        report["1"]["f1-score"],
        }
    
    # -----------------------------------------------
    # PICK BEST MODEL
    # -----------------------------------------------
    rf_auc  = metrics["Random Forest"]["roc_auc"]
    lr_auc  = metrics["Logistic Regression"]["roc_auc"]
    
    if rf_auc >= lr_auc:
        best_model = rf_pipeline
        best_name  = "random_forest"
        print(f"\n✅ Best model: Random Forest (AUC={rf_auc:.3f})")
    else:
        best_model = lr_pipeline
        best_name  = "logistic_regression"
        print(f"\n✅ Best model: Logistic Regression (AUC={lr_auc:.3f})")
    
    # -----------------------------------------------
    # BUILD SHAP EXPLAINER
    # -----------------------------------------------
    print("\n⚡ Building SHAP explainer...")
    
    preprocessor = best_model.named_steps["preprocessor"]
    classifier   = best_model.named_steps["classifier"]
    
    X_sample     = X_train.sample(min(300, len(X_train)), random_state=42)
    X_transformed = preprocessor.transform(X_sample)
    
    if best_name == "random_forest":
        explainer = shap.TreeExplainer(classifier)
    else:
        explainer = shap.LinearExplainer(classifier, X_transformed)
    
    print("✅ SHAP explainer ready")
    
    # -----------------------------------------------
    # SAVE EVERYTHING
    # -----------------------------------------------
    print("\n💾 Saving models...")
    
    joblib.dump(rf_pipeline,  MODEL_PATH / "random_forest.pkl",       compress=3)
    joblib.dump(lr_pipeline,  MODEL_PATH / "logistic_regression.pkl",  compress=3)
    joblib.dump(best_model,   MODEL_PATH / "best_model.pkl",           compress=3)
    joblib.dump(explainer,    MODEL_PATH / "shap_explainer.pkl",       compress=3)
    joblib.dump({
        "best_model_name":      best_name,
        "metrics":              metrics,
        "all_features":         ALL_FEATURES,
        "numeric_features":     NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "binary_features":      BINARY_FEATURES,
    }, MODEL_PATH / "metadata.pkl")
    
    print(f"✅ All models saved to {MODEL_PATH}")
    return best_model, metrics


if __name__ == "__main__":
    print("🚀 Starting training pipeline...\n")
    
    df = load_kaggle_data(
        "data/WA_Fn-UseC_-Telco-Customer-Churn.csv"
    )
    
    best_model, metrics = train_models(df)
    
    print("\n🎉 Training complete!")