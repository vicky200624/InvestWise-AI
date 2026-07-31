"""
Reusable Feature Store for InvestWise AI 3.0.
Stores and serves:
- Historical Features (time-series DataFrame)
- Latest Features (latest point-in-time dictionary for real-time online inference)
- Training Features (versioned historical matrix for offline model training)
- Prediction Features (online inference features)
- Feature Metadata & Feature Versioning
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from pathlib import Path

logger = logging.getLogger("investwise.ai.data.feature_store")

# Feature Store base directory
DEFAULT_FEATURE_DIR = Path("/home/vicky/Documents/investai/datasets/features")


class FeatureStore:
    """
    Reusable Feature Store serving offline training and online prediction pipelines.
    Enforces feature schema consistency and versioning.
    """
    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = store_dir or DEFAULT_FEATURE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.store_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self) -> None:
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load feature store metadata: {e}")
                self.metadata = {"versions": {}, "latest_version": "v1.0.0"}
        else:
            self.metadata = {"versions": {}, "latest_version": "v1.0.0"}

    def _save_metadata(self) -> None:
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feature store metadata: {e}")

    def save_features(
        self,
        symbol: str,
        df: pd.DataFrame,
        version: str = "v1.0.0",
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Save historical and latest features for a symbol under a specific version.
        """
        symbol = symbol.upper().strip()
        version_dir = self.store_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        file_path = version_dir / f"{symbol}_features.parquet"
        csv_path = version_dir / f"{symbol}_features.csv"

        # Save parquet and CSV for redundancy
        try:
            df.to_parquet(file_path, index=False)
        except Exception:
            df.to_csv(csv_path, index=False)
            file_path = csv_path

        feature_cols = feature_names or [
            c for c in df.columns if c not in ("date", "symbol")
        ]

        # Extract latest point-in-time features for online inference
        latest_row = df.iloc[-1].to_dict() if len(df) > 0 else {}

        metadata_entry = {
            "symbol": symbol,
            "version": version,
            "row_count": len(df),
            "feature_count": len(feature_cols),
            "feature_names": feature_cols,
            "file_path": str(file_path),
            "latest_date": str(df["date"].iloc[-1]) if "date" in df.columns and len(df) > 0 else "",
            "latest_features": {
                k: float(v) if isinstance(v, (int, float)) else str(v)
                for k, v in latest_row.items()
            }
        }

        if version not in self.metadata["versions"]:
            self.metadata["versions"][version] = {}
        self.metadata["versions"][version][symbol] = metadata_entry
        self.metadata["latest_version"] = version
        self._save_metadata()

        logger.info(
            f"[{symbol}] Saved {len(df)} rows and {len(feature_cols)} features to Feature Store ({version})."
        )
        return metadata_entry

    def get_historical_features(
        self,
        symbol: str,
        version: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve historical feature DataFrame for offline training or backtesting.
        """
        symbol = symbol.upper().strip()
        version = version or self.metadata.get("latest_version", "v1.0.0")

        version_data = self.metadata.get("versions", {}).get(version, {})
        entry = version_data.get(symbol)
        if not entry:
            logger.warning(f"[{symbol}] No historical features found for version={version}")
            return pd.DataFrame()

        file_path = Path(entry["file_path"])
        if file_path.exists():
            try:
                if file_path.suffix == ".parquet":
                    return pd.read_parquet(file_path)
                return pd.read_csv(file_path)
            except Exception as e:
                logger.error(f"[{symbol}] Error reading historical features file {file_path}: {e}")
        return pd.DataFrame()

    def get_latest_features(
        self,
        symbol: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve latest point-in-time feature dictionary for online real-time prediction.
        """
        symbol = symbol.upper().strip()
        version = version or self.metadata.get("latest_version", "v1.0.0")

        version_data = self.metadata.get("versions", {}).get(version, {})
        entry = version_data.get(symbol)
        if not entry:
            logger.warning(f"[{symbol}] No latest features found in store for version={version}")
            return {}

        return entry.get("latest_features", {})


feature_store = FeatureStore()
