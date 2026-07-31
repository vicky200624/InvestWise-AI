"""
Model version control and metadata registry for AI investment models.
Standalone module with zero Django dependencies.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")


class ModelRegistry:
    """
    Manages saving, loading, and versioning of trained model artifacts and their metadata.
    """

    def __init__(self, models_dir: str = DEFAULT_MODELS_DIR):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)

    def save_model_metadata(
        self,
        symbol: str,
        model_type: str,
        version: str,
        file_path: str,
        metrics: Dict[str, Any],
        is_active: bool = True,
    ) -> str:
        """
        Save JSON metadata for a trained model version.
        """
        meta_dir = os.path.join(self.models_dir, symbol.upper(), model_type.upper())
        os.makedirs(meta_dir, exist_ok=True)

        metadata = {
            "symbol": symbol.upper(),
            "model_type": model_type.upper(),
            "version": version,
            "file_path": file_path,
            "is_active": is_active,
            "metrics": metrics,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        meta_file = os.path.join(meta_dir, f"meta_{version}.json")
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Update latest pointer
            if is_active:
                latest_file = os.path.join(meta_dir, "latest.json")
                with open(latest_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)

            logger.info(f"Saved model metadata for {symbol} {model_type} version {version}")
            return meta_file
        except Exception as e:
            logger.error(f"Error saving model metadata: {e}")
            raise

    def get_latest_metadata(self, symbol: str, model_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve latest active model metadata for a symbol and model type.
        """
        latest_file = os.path.join(self.models_dir, symbol.upper(), model_type.upper(), "latest.json")
        if not os.path.exists(latest_file):
            return None

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading latest metadata from {latest_file}: {e}")
            return None
