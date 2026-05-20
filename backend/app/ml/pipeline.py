# backend/app/ml/pipeline.py
from sklearn.impute import SimpleImputer
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, roc_auc_score,
    confusion_matrix, roc_curve
)
import shap
import joblib
import os
from pathlib import Path

# -----------------------------------------------------------------------
# FEATURE DEFINITIONS — declared at module level (not inside functions)
# WHY: these lists are your "contract" between training and prediction.
# The model is trained on these exact columns.
# At prediction time, you must provide the SAME columns.
# If they diverge, you get silent wrong predictions — a nightmare to debug.
# -----------------------------------------------------------------------

NUMERIC_FEATURES = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "num_support_tickets",
    "age",
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


def build_preprocessor() -> ColumnTransformer:
    """
    ColumnTransformer applies different preprocessing to different column types.
    
    WHY different preprocessing per type:
    
    NUMERIC (tenure_months, charges):
    - StandardScaler: subtract mean, divide by std → all features on same scale
    - WHY scale: Logistic Regression uses gradient descent — unscaled features
      make some features dominate (monthly_charges=79.99 vs online_security=1)
    - Random Forest doesn't need scaling (it uses splits, not distances)
    - But we scale anyway for compatibility with multiple models
    
    CATEGORICAL (contract_type: "Month-to-month", "One year", "Two year"):
    - OneHotEncoder: creates binary columns for each category
    - WHY not LabelEncoder: "Month-to-month"=0, "One year"=1, "Two year"=2 implies
      Two year > One year > Monthly numerically, which is WRONG. OHE avoids this.
    - handle_unknown='ignore': if a new category appears at prediction time,
      don't crash — just treat it as all zeros.
    
    BINARY (True/False features):
    - Already numeric (0/1) — pass through unchanged
    - No scaling needed (already in [0,1] range)
    """
    
    numeric_transformer = Pipeline([
        # Step 1: Impute missing values with median
        # WHY median over mean: median is robust to outliers
        # A customer with charges=0 (cancelled) would skew the mean
        ("imputer", SimpleImputer(strategy="median")),
        
        # Step 2: Scale to zero mean, unit variance
        ("scaler", StandardScaler()),
    ])
    
    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        # most_frequent: fill missing categories with the most common value
        
        ("encoder", OneHotEncoder(
            handle_unknown="ignore",  # Don't crash on new categories
            sparse_output=False,       # Return dense array (easier to work with)
        )),
    ])
    
    binary_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
    ])
    
    # ColumnTransformer applies each transformer to its specified columns
    # and concatenates the results into a single feature matrix
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, NUMERIC_FEATURES),
            ("categorical", categorical_transformer, CATEGORICAL_FEATURES),
            ("binary", binary_transformer, BINARY_FEATURES),
        ],
        remainder="drop",  # Drop any columns not specified above
        # WHY drop: never let unexpected columns sneak into the model
    )
    
    return preprocessor


def build_random_forest_pipeline() -> Pipeline:
    """
    sklearn Pipeline: chains preprocessing + model into one object.
    
    WHY Pipeline matters (a critical concept):
    
    WRONG approach (common beginner mistake):
```python
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)   # Fit on train
    X_test_scaled = scaler.transform(X_test)          # Transform test with train's stats
    model.fit(X_train_scaled, y_train)
```
    
    The problem: if you do cross-validation, you'd leak test data into training
    because you fit the scaler on the full dataset before splitting.
    
    RIGHT approach (Pipeline):
```python
    pipeline = Pipeline([("scaler", StandardScaler()), ("model", RandomForestClassifier())])
    pipeline.fit(X_train, y_train)     # fit_transform scaler on X_train ONLY
    pipeline.predict(X_test)           # Uses scaler fitted on X_train to transform X_test
```
    
    The Pipeline makes cross-validation CORRECT by re-fitting preprocessing
    on each fold's training data.
    """
    
    return Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", RandomForestClassifier(
            n_estimators=200,       # 200 trees — balance between accuracy and speed
            # More trees = better accuracy, diminishing returns after ~300
            
            max_depth=10,           # Limit tree depth — prevents overfitting
            # Overfitting: model memorizes training data, fails on new data
            # Symptom: train accuracy=99%, test accuracy=75%
            
            min_samples_split=20,   # A node must have 20+ samples to split
            # WHY: prevents creating leaves for just 2-3 customers (overfitting)
            
            min_samples_leaf=10,    # Each leaf must have 10+ samples
            
            class_weight="balanced",
            # WHY: churn data is typically imbalanced (~80% not churned, ~20% churned)
            # Without this, the model just predicts "not churned" for everyone
            # and gets 80% accuracy while being USELESS
            # balanced: internally weights minority class (churners) higher
            
            random_state=42,        # Reproducible results
            n_jobs=-1,              # Use all CPU cores for training speed
        )),
    ])


def build_logistic_regression_pipeline() -> Pipeline:
    """
    Logistic Regression is the baseline model.
    
    WHY use LR alongside Random Forest:
    1. INTERPRETABILITY: LR coefficients directly show feature impact
    2. SPEED: LR predicts in microseconds; RF in milliseconds
    3. BASELINE: if RF doesn't beat LR, your features aren't informative
    4. CALIBRATION: LR probabilities are naturally well-calibrated
       (0.7 probability really means ~70% of those customers churn)
    5. REGULATORY: some industries (finance, insurance) require interpretable models
    """
    
    return Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", LogisticRegression(
            C=1.0,
            # C = inverse of regularization strength
            # Low C = strong regularization = simpler model (prevents overfitting)
            # High C = weak regularization = more complex model
            # C=1.0 is a sensible default; tune with cross-validation
            
            class_weight="balanced",   # Same as Random Forest — handle imbalance
            max_iter=1000,             # Allow convergence for complex datasets
            random_state=42,
        )),
    ])


class ChurnModelTrainer:
    """
    Encapsulates the full training workflow.
    
    WHY a class vs functions:
    - Functions are simpler but can't easily share state (preprocessor, models, metrics)
    - Class groups related functionality and stores results
    - Easier to test individual steps
    - In production: this becomes a service with dependency injection
    """
    
    def __init__(self, model_save_path: str = "models_saved/"):
        self.model_save_path = Path(model_save_path)
        self.model_save_path.mkdir(exist_ok=True)
        
        # These get populated after training
        self.rf_pipeline = None
        self.lr_pipeline = None
        self.best_model = None
        self.best_model_name = None
        self.feature_names = None
        self.training_metrics = {}
    
    def prepare_data(self, df: pd.DataFrame):
        """
        Prepare the raw dataframe for training.
        
        In production systems, data preparation has several layers:
        1. THIS function: basic column validation and type coercion
        2. Great Expectations / Pandera: schema validation (separate step)
        3. Feature Store: pre-computed features (advanced architecture)
        """
        
        # Validate required columns exist
        missing = set(ALL_FEATURES + [TARGET]) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Select only the columns we need
        df_clean = df[ALL_FEATURES + [TARGET]].copy()
        # .copy() is critical — prevents SettingWithCopyWarning
        # and ensures we're working with an independent DataFrame
        
        # Type coercion — ensure correct types
        # WHY: CSV loading might give you strings where you need booleans
        for col in BINARY_FEATURES:
            if col in df_clean.columns:
                # Handle various representations: True/False, 1/0, "Yes"/"No"
                df_clean[col] = df_clean[col].map(
                    {True: 1, False: 0, 1: 1, 0: 0, "Yes": 1, "No": 0, "yes": 1, "no": 0}
                ).fillna(0)
        
        # Convert target to integer
        df_clean[TARGET] = df_clean[TARGET].astype(int)
        
        X = df_clean[ALL_FEATURES]
        y = df_clean[TARGET]
        
        # Log class balance — important diagnostic
        churn_rate = y.mean()
        print(f"📊 Dataset shape: {X.shape}")
        print(f"📊 Churn rate: {churn_rate:.1%} ({y.sum()} churned / {len(y)} total)")
        
        if churn_rate < 0.05:
            print("⚠️  Warning: Very low churn rate (<5%). Consider SMOTE oversampling.")
        if churn_rate > 0.5:
            print("⚠️  Warning: High churn rate (>50%). Check if this is correct.")
        
        return X, y
    
    def train(self, df: pd.DataFrame) -> dict:
        """
        Full training workflow: data prep → train/test split → fit → evaluate → save.
        """
        
        X, y = self.prepare_data(df)
        
        # Train/test split
        # stratify=y: ensures both train and test have the same churn rate
        # WHY stratify: with 20% churn, random split might give 15% in test by chance
        # That changes your evaluation metrics misleadingly
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,    # 80% train, 20% test — industry standard
            random_state=42,
            stratify=y,
        )
        
        print(f"\n🏋️  Training on {len(X_train)} samples, testing on {len(X_test)} samples")
        
        # Train both models
        print("\n🌲 Training Random Forest...")
        self.rf_pipeline = build_random_forest_pipeline()
        self.rf_pipeline.fit(X_train, y_train)
        
        print("📈 Training Logistic Regression...")
        self.lr_pipeline = build_logistic_regression_pipeline()
        self.lr_pipeline.fit(X_train, y_train)
        
        # Evaluate
        self.training_metrics = self._evaluate_models(X_test, y_test)
        
        # Select best model based on ROC-AUC score
        # WHY ROC-AUC over accuracy:
        # - Accuracy: "I correctly classified 85% of customers"
        # - Problem: if 85% don't churn, always predicting "no churn" = 85% accurate but USELESS
        # - ROC-AUC: measures the model's ability to distinguish churners from non-churners
        # - ROC-AUC=0.5 means random guessing; ROC-AUC=1.0 means perfect
        # - Industry standard for imbalanced classification problems
        rf_auc = self.training_metrics["random_forest"]["roc_auc"]
        lr_auc = self.training_metrics["logistic_regression"]["roc_auc"]
        
        if rf_auc >= lr_auc:
            self.best_model = self.rf_pipeline
            self.best_model_name = "random_forest"
            print(f"\n✅ Random Forest wins: AUC={rf_auc:.3f} vs LR AUC={lr_auc:.3f}")
        else:
            self.best_model = self.lr_pipeline
            self.best_model_name = "logistic_regression"
            print(f"\n✅ Logistic Regression wins: AUC={lr_auc:.3f} vs RF AUC={rf_auc:.3f}")
        
        # Save models
        self._save_models()
        
        # Build SHAP explainer (on a sample for performance)
        self._build_shap_explainer(X_train.sample(min(500, len(X_train))))
        
        return self.training_metrics
    
    def _evaluate_models(self, X_test, y_test) -> dict:
        """
        Comprehensive model evaluation.
        
        Metrics you should always compute for classification:
        
        ACCURACY: (TP + TN) / total — misleading for imbalanced classes
        
        PRECISION: TP / (TP + FP) — "of customers we predicted would churn,
                   what % actually did?" — measures false alarm rate
        
        RECALL (Sensitivity): TP / (TP + FN) — "of customers who actually churned,
                   what % did we catch?" — measures how many churners we miss
        
        F1: harmonic mean of precision and recall — good single metric
        
        ROC-AUC: area under the ROC curve — best metric for imbalanced problems
        
        BUSINESS CONTEXT:
        - High recall, low precision: you flag many customers as at-risk
          (costly: unnecessary retention efforts) but catch most churners
        - Low recall, high precision: you only flag obvious churners
          (efficient: only act on high confidence) but miss subtle churners
        - The right tradeoff depends on your business — retention campaign cost vs
          customer lifetime value
        """
        metrics = {}
        
        for name, pipeline in [
            ("random_forest", self.rf_pipeline),
            ("logistic_regression", self.lr_pipeline),
        ]:
            y_pred = pipeline.predict(X_test)
            y_prob = pipeline.predict_proba(X_test)[:, 1]
            # predict_proba returns [[prob_no_churn, prob_churn], ...]
            # [:, 1] selects the probability of churn (class 1)
            
            report = classification_report(y_test, y_pred, output_dict=True)
            
            metrics[name] = {
                "accuracy": report["accuracy"],
                "precision": report["1"]["precision"],  # For churn class
                "recall": report["1"]["recall"],
                "f1": report["1"]["f1-score"],
                "roc_auc": roc_auc_score(y_test, y_prob),
                "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            }
            
            print(f"\n  {name.upper()} METRICS:")
            print(f"  Accuracy:  {metrics[name]['accuracy']:.3f}")
            print(f"  Precision: {metrics[name]['precision']:.3f}")
            print(f"  Recall:    {metrics[name]['recall']:.3f}")
            print(f"  F1 Score:  {metrics[name]['f1']:.3f}")
            print(f"  ROC-AUC:   {metrics[name]['roc_auc']:.3f}")
        
        return metrics
    
    def _build_shap_explainer(self, X_sample: pd.DataFrame):
        """
        Build a SHAP explainer for the best model.
        
        SHAP (SHapley Additive exPlanations):
        
        The fundamental problem with ML black boxes:
        "The model says Customer A has 87% churn probability — why?"
        
        SHAP answers this by computing each feature's contribution to the prediction.
        
        Example output:
        - tenure_months: -0.34  (reduces churn risk — long-term customers are loyal)
        - num_support_tickets: +0.28  (increases risk — frustrated customer)
        - contract_type=Monthly: +0.22  (increases risk — easy to cancel)
        - online_security=False: +0.15  (increases risk — not embedded in service)
        
        The sum of all SHAP values = deviation from the average prediction
        
        WHY SHAP matters in production:
        1. Customer service teams need to know WHY to take action
        2. Regulatory compliance (GDPR Article 22: right to explanation)
        3. Model debugging: if SHAP shows unexpected patterns, your data may be wrong
        4. Feature importance at population level: what drives churn across all customers?
        """
        
        print("\n⚡ Building SHAP explainer...")
        
        # Transform the sample through the preprocessor
        # SHAP works on transformed features
        preprocessor = self.best_model.named_steps["preprocessor"]
        X_transformed = preprocessor.transform(X_sample)
        
        if self.best_model_name == "random_forest":
            # TreeExplainer: optimized for tree-based models (fast)
            # 100x faster than KernelExplainer for trees
            self.explainer = shap.TreeExplainer(
                self.best_model.named_steps["classifier"]
            )
        else:
            # LinearExplainer: optimized for linear models (even faster)
            self.explainer = shap.LinearExplainer(
                self.best_model.named_steps["classifier"],
                X_transformed,
            )
        
        # Save explainer
        joblib.dump(self.explainer, self.model_save_path / "shap_explainer.pkl")
        print("✅ SHAP explainer built and saved")
    
    def _save_models(self):
        """
        Save trained model pipelines using joblib.
        
        WHY joblib over pickle:
        - Faster serialization for numpy arrays (which pipelines contain)
        - Supports compression: compress=3 reduces file size by 50-80%
        - More reliable for sklearn objects
        
        In production: companies use MLflow or Weights & Biases
        to track model versions, metrics, and artifacts together.
        """
        joblib.dump(
            self.rf_pipeline,
            self.model_save_path / "random_forest.pkl",
            compress=3,
        )
        joblib.dump(
            self.lr_pipeline,
            self.model_save_path / "logistic_regression.pkl",
            compress=3,
        )
        joblib.dump(
            self.best_model,
            self.model_save_path / "best_model.pkl",
            compress=3,
        )
        joblib.dump(
            {"best_model_name": self.best_model_name, "metrics": self.training_metrics},
            self.model_save_path / "metadata.pkl",
        )
        print(f"\n💾 Models saved to {self.model_save_path}")