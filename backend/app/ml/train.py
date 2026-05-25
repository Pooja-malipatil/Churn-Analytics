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
from sklearn.metrics import classification_report, roc_auc_score
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
TARGET       = "churned"

MODEL_PATH = Path("models_saved/")
MODEL_PATH.mkdir(exist_ok=True)


def load_kaggle_data(filepath: str) -> pd.DataFrame:
    """
    Loads and cleans the Kaggle Telco dataset.
    """
    print(f"📂 Loading data from {filepath}...")
    df = pd.read_csv(filepath)

    print(f"   Raw shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")

    # Rename columns
    df = df.rename(columns={
        "customerID":      "customer_id",
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
        "gender":          "gender",
        "SeniorCitizen":   "senior_citizen",
        "Partner":         "partner",
        "Dependents":      "dependents",
    })

    # Fix total charges
    df["total_charges"] = pd.to_numeric(
        df["total_charges"], errors="coerce"
    ).fillna(0.0)

    # Fix target column
    df["churned"] = df["churned"].map({"Yes": 1, "No": 0})

    # Fix binary columns
    binary_cols = [
        "online_security", "tech_support",
        "streaming_tv", "streaming_movies",
        "phone_service", "multiple_lines",
    ]
    for col in binary_cols:
        if col in df.columns:
            df[col] = df[col].map({
                "Yes": 1, "No": 0,
                "No internet service": 0,
                "No phone service": 0,
                True: 1, False: 0,
                1: 1, 0: 0,
            }).fillna(0).astype(int)

    # Add missing column
    if "num_support_tickets" not in df.columns:
        df["num_support_tickets"] = 0

    # Drop rows where target is missing
    df = df.dropna(subset=["churned"])

    print(f"   Clean shape: {df.shape}")
    print(f"   Churn rate: {df['churned'].mean():.1%}")

    return df


def load_custom_data(filepath: str) -> pd.DataFrame:
    """
    Loads a custom format CSV.
    Tries to map whatever columns exist to our feature set.
    Missing columns are filled with default values.
    """
    print(f"📂 Loading custom data from {filepath}...")
    df = pd.read_csv(filepath)

    print(f"   Raw shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")

    # Try common column name variations
    column_mapping = {}

    # Tenure variations
    for col in ["tenure", "Tenure", "tenure_months", "months", "age_months"]:
        if col in df.columns:
            column_mapping[col] = "tenure_months"
            break

    # Monthly charges variations
    for col in ["MonthlyCharges", "monthly_charges", "monthly_charge",
                "charges", "bill", "monthly_bill"]:
        if col in df.columns:
            column_mapping[col] = "monthly_charges"
            break

    # Total charges variations
    for col in ["TotalCharges", "total_charges", "total_charge",
                "total_bill", "lifetime_value"]:
        if col in df.columns:
            column_mapping[col] = "total_charges"
            break

    # Contract type variations
    for col in ["Contract", "contract_type", "contract",
                "plan", "subscription_type"]:
        if col in df.columns:
            column_mapping[col] = "contract_type"
            break

    # Internet service variations
    for col in ["InternetService", "internet_service", "internet",
                "service_type"]:
        if col in df.columns:
            column_mapping[col] = "internet_service"
            break

    # Payment method variations
    for col in ["PaymentMethod", "payment_method", "payment",
                "billing_method"]:
        if col in df.columns:
            column_mapping[col] = "payment_method"
            break

    # Churn variations
    for col in ["Churn", "churned", "churn", "is_churned",
                "left", "cancelled"]:
        if col in df.columns:
            column_mapping[col] = "churned"
            break

    # Rename columns
    df = df.rename(columns=column_mapping)

    # Fix total charges
    if "total_charges" in df.columns:
        df["total_charges"] = pd.to_numeric(
            df["total_charges"], errors="coerce"
        ).fillna(0.0)

    # Fix churn column
    if "churned" in df.columns:
        df["churned"] = df["churned"].map({
            "Yes": 1, "No": 0, "yes": 1, "no": 0,
            "True": 1, "False": 0,
            True: 1, False: 0,
            1: 1, 0: 0
        }).fillna(0).astype(int)

    # Add missing columns with defaults
    defaults = {
        "tenure_months":       0,
        "monthly_charges":     0.0,
        "total_charges":       0.0,
        "contract_type":       "Month-to-month",
        "internet_service":    "DSL",
        "payment_method":      "Electronic check",
        "online_security":     0,
        "tech_support":        0,
        "streaming_tv":        0,
        "streaming_movies":    0,
        "phone_service":       1,
        "multiple_lines":      0,
        "num_support_tickets": 0,
        "churned":             0,
    }

    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val
            print(f"   ⚠️  Missing '{col}' — using default: {default_val}")

    # Fix binary columns
    binary_cols = [
        "online_security", "tech_support", "streaming_tv",
        "streaming_movies", "phone_service", "multiple_lines",
    ]
    for col in binary_cols:
        if col in df.columns:
            df[col] = df[col].map({
                "Yes": 1, "No": 0, "yes": 1, "no": 0,
                "No internet service": 0,
                "No phone service": 0,
                True: 1, False: 0, 1: 1, 0: 0
            }).fillna(0).astype(int)

    # Drop rows where target is missing
    df = df.dropna(subset=["churned"])

    print(f"   Clean shape: {df.shape}")
    print(f"   Churn rate: {df['churned'].mean():.1%}")

    return df


def build_preprocessor():
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
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
            ("numeric",     numeric_transformer,     NUMERIC_FEATURES),
            ("categorical", categorical_transformer, CATEGORICAL_FEATURES),
            ("binary",      binary_transformer,      BINARY_FEATURES),
        ],
        remainder="drop",
    )


def train_models(df: pd.DataFrame):
    """Full training workflow."""

    X = df[ALL_FEATURES]
    y = df[TARGET]

    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    print(f"\n📊 Train: {len(X_train)} | Test: {len(X_test)}")

    # Train Random Forest
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

    # Train Logistic Regression
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

    # Evaluate
    print("\n📋 EVALUATION RESULTS:")
    print("=" * 50)

    metrics = {}

    for name, pipeline in [
        ("Random Forest",       rf_pipeline),
        ("Logistic Regression", lr_pipeline),
    ]:
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        report = classification_report(y_test, y_pred, output_dict=True)
        auc    = roc_auc_score(y_test, y_prob)

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

    # Pick best model
    rf_auc = metrics["Random Forest"]["roc_auc"]
    lr_auc = metrics["Logistic Regression"]["roc_auc"]

    if rf_auc >= lr_auc:
        best_model = rf_pipeline
        best_name  = "random_forest"
        print(f"\n✅ Best model: Random Forest (AUC={rf_auc:.3f})")
    else:
        best_model = lr_pipeline
        best_name  = "logistic_regression"
        print(f"\n✅ Best model: Logistic Regression (AUC={lr_auc:.3f})")

    # Build SHAP explainer
    print("\n⚡ Building SHAP explainer...")

    preprocessor  = best_model.named_steps["preprocessor"]
    classifier    = best_model.named_steps["classifier"]
    X_sample      = X_train.sample(min(300, len(X_train)), random_state=42)
    X_transformed = preprocessor.transform(X_sample)

    if best_name == "random_forest":
        explainer = shap.TreeExplainer(classifier)
    else:
        explainer = shap.LinearExplainer(classifier, X_transformed)

    print("✅ SHAP explainer ready")

    # Save everything
    print("\n💾 Saving models...")

    joblib.dump(rf_pipeline,  MODEL_PATH / "random_forest.pkl",        compress=3)
    joblib.dump(lr_pipeline,  MODEL_PATH / "logistic_regression.pkl",   compress=3)
    joblib.dump(best_model,   MODEL_PATH / "best_model.pkl",            compress=3)
    joblib.dump(explainer,    MODEL_PATH / "shap_explainer.pkl",        compress=3)
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