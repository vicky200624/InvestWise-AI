import os
import logging
import joblib
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import xgboost as xgb
from AI.prediction.model_loader import get_model_dir

logger = logging.getLogger('investwise.ai.train_xgboost')

def train_xgboost_scorer(features_df: pd.DataFrame, labels: pd.Series, model_dir: str = "/home/vicky/Documents/investai/AI/models") -> Dict[str, Any]:
    """Train XGBoost classifier for Investment Score (0-100)."""
    try:
        model = xgb.XGBRegressor(
            n_estimators=100,
            early_stopping_rounds=10,
            tree_method='hist',
            eval_metric='rmse'
        )
        
        # In a real setup, you'd split into train/eval sets.
        model.fit(features_df, labels, eval_set=[(features_df, labels)], verbose=False)
        
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"xgboost_{version}.joblib"
        model_path = os.path.join(get_model_dir(model_dir), model_filename)
        
        joblib.dump(model, model_path)
        
        return {"status": "success", "model_path": model_path, "version": version}
    except Exception as e:
        logger.error(f"Error training XGBoost scorer: {str(e)}")
        raise

def train_catboost_scorer(features_df: pd.DataFrame, labels: pd.Series, cat_features: List[str] = None, model_dir: str = "/home/vicky/Documents/investai/AI/models") -> Dict[str, Any]:
    """Train CatBoost with native categorical feature support."""
    try:
        from catboost import CatBoostRegressor
        model = CatBoostRegressor(iterations=100, learning_rate=0.1, depth=6)
        model.fit(features_df, labels, cat_features=cat_features, verbose=False)
        
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"catboost_{version}.joblib"
        model_path = os.path.join(get_model_dir(model_dir), model_filename)
        
        joblib.dump(model, model_path)
        
        return {"status": "success", "model_path": model_path, "version": version}
    except Exception as e:
        logger.error(f"Error training CatBoost scorer: {str(e)}")
        raise
