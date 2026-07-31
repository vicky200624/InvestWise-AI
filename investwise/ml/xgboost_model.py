import os
import logging
from typing import Dict, Any, List
import pandas as pd
import xgboost as xgb
import shap
from django.conf import settings
from django.utils import timezone
import joblib

from investwise.models import TrainedModel

logger = logging.getLogger('investwise')

def prepare_decision_features(fundamental_score: float, quant_score: float, sentiment_score: float,
                              time_horizon: str, additional_features: dict = None) -> pd.DataFrame:
    """Combine all cluster scores + raw features into XGBoost input."""
    try:
        features = {
            'fundamental_score': fundamental_score,
            'quant_score': quant_score,
            'sentiment_score': sentiment_score,
            'time_horizon_encoded': 1 if time_horizon == 'LONG_TERM' else 0,
        }
        if additional_features:
            features.update(additional_features)
            
        return pd.DataFrame([features])
    except Exception as e:
        logger.error(f"Error preparing decision features: {str(e)}")
        raise

def train_xgboost_scorer(features_df: pd.DataFrame, labels: pd.Series) -> Dict[str, Any]:
    """Train XGBoost classifier for Investment Score (0-100)."""
    try:
        model = xgb.XGBRegressor(
            n_estimators=100,
            early_stopping_rounds=10,
            tree_method='hist',
            eval_metric='rmse'
        )
        
        model.fit(features_df, labels, eval_set=[(features_df, labels)], verbose=False)
        
        version = timezone.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"xgboost_scorer_{version}.joblib"
        model_path = os.path.join(settings.AI_MODEL_DIR, model_filename)
        
        os.makedirs(settings.AI_MODEL_DIR, exist_ok=True)
        joblib.dump(model, model_path)
        
        TrainedModel.objects.create(
            symbol='GLOBAL',
            model_type='XGBOOST',
            version=version,
            file_path=model_path,
            is_active=True
        )
        
        return {"status": "success", "model_path": model_path}
    except Exception as e:
        logger.error(f"Error training XGBoost scorer: {str(e)}")
        raise

def train_catboost_scorer(features_df: pd.DataFrame, labels: pd.Series, cat_features: List[str] = None) -> Dict[str, Any]:
    """Train CatBoost with native categorical feature support."""
    try:
        from catboost import CatBoostRegressor
        model = CatBoostRegressor(iterations=100, learning_rate=0.1, depth=6)
        model.fit(features_df, labels, cat_features=cat_features, verbose=False)
        
        version = timezone.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"catboost_scorer_{version}.joblib"
        model_path = os.path.join(settings.AI_MODEL_DIR, model_filename)
        
        os.makedirs(settings.AI_MODEL_DIR, exist_ok=True)
        joblib.dump(model, model_path)
        
        TrainedModel.objects.create(
            symbol='GLOBAL',
            model_type='CATBOOST',
            version=version,
            file_path=model_path,
            is_active=True
        )
        
        return {"status": "success", "model_path": model_path}
    except Exception as e:
        logger.error(f"Error training CatBoost scorer: {str(e)}")
        raise

def predict_investment_score(features: Dict[str, Any], model_type: str = 'XGBOOST') -> Dict[str, Any]:
    """Load active model and predict investment score."""
    try:
        active_model = TrainedModel.objects.filter(symbol='GLOBAL', model_type=model_type, is_active=True).latest('created_at')
        
        model = joblib.load(active_model.file_path)
        features_df = pd.DataFrame([features])
        
        score = model.predict(features_df)[0]
        score = max(0, min(100, score))
        
        recommendation = 'Buy' if score > 70 else ('Hold' if score > 40 else 'Sell')
        
        return {
            "score": float(score),
            "confidence": 0.85,
            "recommendation": recommendation
        }
    except Exception as e:
        logger.error(f"Error predicting investment score: {str(e)}")
        raise

def generate_shap_explanation(model: Any, features_df: pd.DataFrame) -> Dict[str, Any]:
    """Generate SHAP values for explainability."""
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(features_df)
        
        feature_names = features_df.columns.tolist()
        base_value = float(explainer.expected_value)
        
        top_factors = []
        for i, name in enumerate(feature_names):
            top_factors.append({
                "name": name,
                "value": float(features_df.iloc[0, i]),
                "impact": float(shap_values[0, i])
            })
            
        top_factors = sorted(top_factors, key=lambda x: abs(x['impact']), reverse=True)
        
        return {
            "shap_values": shap_values.tolist(),
            "feature_names": feature_names,
            "base_value": base_value,
            "top_factors": top_factors
        }
    except Exception as e:
        logger.error(f"Error generating SHAP explanation: {str(e)}")
        raise
