import logging
from typing import Dict, Any
import pandas as pd
import shap

logger = logging.getLogger('investwise.ai.explainer')

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
