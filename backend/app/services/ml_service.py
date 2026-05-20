# backend/app/services/ml_service.py

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

MODEL_PATH = Path("models_saved/")

NUMERIC_FEATURES     = ["tenure_months", "monthly_charges", "total_charges", "num_support_tickets"]
CATEGORICAL_FEATURES = ["contract_type", "internet_service", "payment_method"]
BINARY_FEATURES      = ["online_security", "tech_support", "streaming_tv", "streaming_movies", "phone_service", "multiple_lines"]
ALL_FEATURES         = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES


def get_risk_category(probability: float) -> str:
    if probability >= 0.75:
        return "Critical"
    elif probability >= 0.50:
        return "High"
    elif probability >= 0.25:
        return "Medium"
    else:
        return "Low"


def get_retention_strategies(probability: float, features: dict) -> list:
    strategies = []

    if probability < 0.25:
        return ["Customer is low risk. Send a satisfaction survey."]

    if features.get("contract_type") == "Month-to-month":
        strategies.append("Offer 20% discount to upgrade to annual contract.")

    if features.get("monthly_charges", 0) > 70:
        strategies.append("Offer a loyalty discount of 15% on monthly bill.")

    if features.get("num_support_tickets", 0) > 3:
        strategies.append("Escalate to senior support — customer shows frustration.")

    if not features.get("online_security", False):
        strategies.append("Offer free 3-month trial of Online Security package.")

    if not features.get("tech_support", False):
        strategies.append("Offer free 3-month trial of Tech Support package.")

    if probability >= 0.75:
        strategies.append("Assign dedicated account manager immediately.")
        strategies.append("Schedule a customer success call within 24 hours.")

    if not strategies:
        strategies.append("Send personalized re-engagement email campaign.")

    return strategies


class MLService:

    def __init__(self):
        self.model     = None
        self.explainer = None
        self.metadata  = None
        self.is_ready  = False

    async def initialize(self):
        try:
            self.model     = joblib.load(MODEL_PATH / "best_model.pkl")
            self.explainer = joblib.load(MODEL_PATH / "shap_explainer.pkl")
            self.metadata  = joblib.load(MODEL_PATH / "metadata.pkl")
            self.is_ready  = True
            print(f"✅ ML Service ready — best model: {self.metadata['best_model_name']}")
        except FileNotFoundError:
            print("⚠️  No trained model found. Run training first.")
            self.is_ready = False

    async def predict(self, request, db) -> dict:
        if not self.is_ready:
            raise ValueError("Model not loaded. Please train the model first.")

        # Build input dataframe
        input_data = {
            "tenure_months":       request.tenure_months,
            "monthly_charges":     request.monthly_charges,
            "total_charges":       request.total_charges,
            "num_support_tickets": request.num_support_tickets,
            "contract_type":       request.contract_type,
            "internet_service":    getattr(request, "internet_service", "DSL"),
            "payment_method":      getattr(request, "payment_method", "Electronic check"),
            "online_security":     int(request.online_security),
            "tech_support":        int(request.tech_support),
            "streaming_tv":        int(getattr(request, "streaming_tv", False)),
            "streaming_movies":    int(getattr(request, "streaming_movies", False)),
            "phone_service":       int(getattr(request, "phone_service", True)),
            "multiple_lines":      int(getattr(request, "multiple_lines", False)),
        }

        input_df = pd.DataFrame([input_data])

        # Get churn probability
        churn_probability = float(
            self.model.predict_proba(input_df)[0][1]
        )

        # Get SHAP values
        try:
            preprocessor  = self.model.named_steps["preprocessor"]
            classifier    = self.model.named_steps["classifier"]
            X_transformed = preprocessor.transform(input_df)
            feature_names = self._get_feature_names()
            raw_shap      = self.explainer.shap_values(X_transformed)

            # Handle all SHAP output formats
            if isinstance(raw_shap, list):
                sv = np.array(raw_shap[1][0])
            elif hasattr(raw_shap, 'values'):
                vals = raw_shap.values
                if vals.ndim == 3:
                    sv = vals[0, :, 1]
                elif vals.ndim == 2:
                    sv = vals[0]
                else:
                    sv = vals
            else:
                sv = np.array(raw_shap)
                if sv.ndim == 2:
                    sv = sv[0]

            sv      = np.array(sv).flatten()
            min_len = min(len(feature_names), len(sv))
            feature_names = feature_names[:min_len]
            sv      = sv[:min_len]

            shap_pairs = sorted(
                zip(feature_names, sv),
                key=lambda x: abs(x[1]),
                reverse=True
            )

            top_risk_factors = [
                {
                    "feature": name.replace("_", " "),
                    "impact":  round(float(val), 4)
                }
                for name, val in shap_pairs[:5]
            ]

        except Exception as e:
            print(f"SHAP error: {e}")
            try:
                classifier    = self.model.named_steps["classifier"]
                feature_names = self._get_feature_names()
                importances   = classifier.feature_importances_
                pairs = sorted(
                    zip(feature_names, importances),
                    key=lambda x: x[1],
                    reverse=True
                )
                top_risk_factors = [
                    {
                        "feature": name.replace("_", " "),
                        "impact":  round(float(val), 4)
                    }
                    for name, val in pairs[:5]
                ]
            except Exception as e2:
                print(f"Fallback error: {e2}")
                top_risk_factors = [
                    {"feature": "tenure months",       "impact": 0.0},
                    {"feature": "monthly charges",     "impact": 0.0},
                    {"feature": "contract type",       "impact": 0.0},
                    {"feature": "num support tickets", "impact": 0.0},
                    {"feature": "online security",     "impact": 0.0},
                ]

        # Build response
        risk        = get_risk_category(churn_probability)
        top_feature = top_risk_factors[0]["feature"] if top_risk_factors else "unknown"
        explanation = (
            f"Customer has a {churn_probability:.1%} probability of churning. "
            f"Risk level: {risk}. "
            f"Top factor: {top_feature}."
        )
        strategies = get_retention_strategies(churn_probability, input_data)

        return {
            "customer_id":          request.customer_id,
            "churn_probability":    round(churn_probability, 4),
            "risk_category":        risk,
            "top_risk_factors":     top_risk_factors,
            "explanation":          explanation,
            "retention_strategies": strategies,
            "model_version":        "v1.0",
            "prediction_id":        0,
        }

    async def log_prediction(self, customer_id, result, db):
        try:
            from app.models.prediction import PredictionLog
            log = PredictionLog(
                customer_id         = customer_id,
                churn_probability   = result["churn_probability"],
                risk_category       = result["risk_category"],
                feature_importances = result["top_risk_factors"],
                shap_values         = result["top_risk_factors"],
            )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"Logging error: {e}")

    def _get_feature_names(self) -> list:
        try:
            preprocessor = self.model.named_steps["preprocessor"]
            cat_encoder  = preprocessor.named_transformers_["categorical"].named_steps["encoder"]
            cat_names    = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
            return NUMERIC_FEATURES + cat_names + BINARY_FEATURES
        except Exception:
            return ALL_FEATURES


ml_service = MLService()