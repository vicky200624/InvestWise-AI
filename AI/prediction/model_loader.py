"""
Model Versioning and Loading for InvestWise AI.
Replaces the Django TrainedModel logic.
"""
import os
import glob
import logging

logger = logging.getLogger('investwise.ai.model_loader')

def get_model_dir(model_dir: str = "/home/vicky/Documents/investai/AI/models") -> str:
    os.makedirs(model_dir, exist_ok=True)
    return model_dir

def get_latest_model_path(model_type: str, model_dir: str = "/home/vicky/Documents/investai/AI/models") -> str:
    """
    Find the latest model file in the models directory for a given type.
    Naming convention: {model_type}_{version}.joblib or similar
    """
    pattern = os.path.join(get_model_dir(model_dir), f"{model_type.lower()}_*.joblib")
    files = glob.glob(pattern)
    if not files:
        pattern_pt = os.path.join(get_model_dir(model_dir), f"{model_type.lower()}_*.pt")
        files = glob.glob(pattern_pt)
        if not files:
            raise FileNotFoundError(f"No active model found for {model_type}")
    
    # Sort by modification time or version string
    latest_file = max(files, key=os.path.getmtime)
    return latest_file
