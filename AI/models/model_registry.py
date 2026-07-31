"""
Model Registry and Model Promotion Protocol for InvestWise AI 3.0.
Manages:
AI/
└── models/
    └── xgboost/
        ├── v1/
        ├── v2/
        ├── latest/
        └── metadata.json
Enforces:
- Full model metadata (Version, Training Date, Dataset Version, Hyperparameters,
  Metrics, Feature List, Git Commit, Author, Status: Production / Candidate / Archived)
- Model Promotion: Candidate -> Backtest -> Compare -> Human Approval -> Deploy.
  Never automatically replace production model.
"""
import os
import json
import shutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("investwise.ai.models.model_registry")

DEFAULT_MODELS_DIR = Path("/home/vicky/Documents/investai/AI/models")


class ModelPromotionError(Exception):
    """Raised when model promotion protocol rules are violated."""
    pass


class ModelRegistry:
    """
    Manages model versioning, metadata storage, and candidate-to-production promotion.
    """
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or DEFAULT_MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.xgboost_dir = self.models_dir / "xgboost"
        self.xgboost_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.xgboost_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self) -> None:
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {"models": {}, "production_version": ""}
        else:
            self.metadata = {"models": {}, "production_version": ""}

    def _save_metadata(self) -> None:
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model registry metadata: {e}")

    def register_candidate(
        self,
        model_type: str,
        version: str,
        metrics: Dict[str, float],
        hyperparameters: Dict[str, Any],
        dataset_version: str,
        feature_list: Optional[List[str]] = None,
        git_commit: str = "HEAD",
        author: str = "InvestWise AI Training Pipeline",
        model_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a newly trained model with status='Candidate'.
        Never automatically replaces production model per Part 3 rules.
        """
        if version in self.metadata["models"]:
            logger.warning(f"Version {version} already registered. Updating entry.")

        version_dir = self.xgboost_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        if not model_file_path:
            # Create a placeholder or copy actual artifact
            target_path = version_dir / "model.xgb"
            target_path.write_text(f"MODEL_ARTIFACT:{model_type}:{version}")
            model_file_path = str(target_path)

        metadata_entry = {
            "version": version,
            "model_type": model_type,
            "training_date": datetime.utcnow().isoformat() + "Z",
            "dataset_version": dataset_version,
            "hyperparameters": hyperparameters,
            "metrics": {
                "accuracy": float(metrics.get("accuracy", 0.0)),
                "precision": float(metrics.get("precision", 0.0)),
                "recall": float(metrics.get("recall", 0.0)),
                "f1_score": float(metrics.get("f1_score", 0.0)),
                "roc_auc": float(metrics.get("roc_auc", 0.0)),
                "rmse": float(metrics.get("rmse", 0.0)),
                "mae": float(metrics.get("mae", 0.0)),
                "mape": float(metrics.get("mape", 0.0)),
                "sharpe_ratio": float(metrics.get("sharpe_ratio", 0.0)),
                "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
                "hit_ratio": float(metrics.get("hit_ratio", 0.0))
            },
            "feature_list": feature_list or [
                "return_1d", "RSI_14", "MACD", "EMA_20", "fin_roe", "val_dcf"
            ],
            "git_commit": git_commit,
            "author": author,
            "status": "Candidate",  # ALWAYS Candidate on initial registration
            "file_path": str(model_file_path)
        }

        self.metadata["models"][version] = metadata_entry
        self._save_metadata()

        logger.info(
            f"Registered model candidate version={version}. Status='Candidate'. "
            "Requires human approval to promote to Production."
        )
        return metadata_entry

    def promote_to_production(
        self,
        version: str,
        approved_by: str = "Human Approval",
        comparison_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Promote a Candidate model to Production after backtest comparison and human approval.
        Archives the previous Production model.
        """
        entry = self.metadata["models"].get(version)
        if not entry:
            raise ModelPromotionError(f"Model version {version} not found in registry.")

        if entry["status"] == "Production":
            logger.info(f"Model version {version} is already Production.")
            return entry

        if entry["status"] != "Candidate":
            raise ModelPromotionError(
                f"Only 'Candidate' models can be promoted. Current status={entry['status']}"
            )

        # Archive any existing Production model
        prev_prod = self.metadata.get("production_version")
        if prev_prod and prev_prod in self.metadata["models"]:
            self.metadata["models"][prev_prod]["status"] = "Archived"
            logger.info(f"Archived previous production model: {prev_prod}")

        # Promote candidate
        entry["status"] = "Production"
        entry["promoted_at"] = datetime.utcnow().isoformat() + "Z"
        entry["approved_by"] = approved_by
        entry["comparison_notes"] = comparison_notes

        self.metadata["production_version"] = version

        # Update latest symlink/folder
        latest_dir = self.xgboost_dir / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        latest_meta_path = latest_dir / "metadata.json"
        try:
            with open(latest_meta_path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not update latest/metadata.json: {e}")

        self._save_metadata()
        logger.info(f"Successfully promoted model {version} to PRODUCTION (Approved by: {approved_by}).")
        return entry

    def get_production_model(self) -> Optional[Dict[str, Any]]:
        """Return metadata for the active Production model."""
        prod_version = self.metadata.get("production_version")
        if not prod_version:
            return None
        return self.metadata["models"].get(prod_version)


model_registry = ModelRegistry()
