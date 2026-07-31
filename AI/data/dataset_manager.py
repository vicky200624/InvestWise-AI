"""
Dataset Versioning and Management for InvestWise AI 3.0.
Manages immutable dataset directories:
datasets/
├── raw/
├── cleaned/
├── processed/
├── features/
├── training/
├── validation/
├── test/
└── metadata.json
Enforces:
- Never overwrite datasets.
- Time-based 70/15/15 train/val/test splits without random shuffling.
"""
import os
import json
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd

logger = logging.getLogger("investwise.ai.data.dataset_manager")

DEFAULT_DATASETS_DIR = Path("/home/vicky/Documents/investai/datasets")


class DatasetManager:
    """
    Manages immutable dataset versioning and time-based splits.
    """
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or DEFAULT_DATASETS_DIR
        self.dirs = {
            "raw": self.root_dir / "raw",
            "cleaned": self.root_dir / "cleaned",
            "processed": self.root_dir / "processed",
            "features": self.root_dir / "features",
            "training": self.root_dir / "training",
            "validation": self.root_dir / "validation",
            "test": self.root_dir / "test",
        }
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.root_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self) -> None:
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {"datasets": {}, "latest_version": ""}
        else:
            self.metadata = {"datasets": {}, "latest_version": ""}

    def _save_metadata(self) -> None:
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save datasets metadata: {e}")

    def create_dataset_version(
        self,
        symbol: str,
        feature_df: pd.DataFrame,
        version_label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an immutable dataset version and split into 70% Train,
        15% Validation, and 15% Test using strict chronological order.
        """
        symbol = symbol.upper().strip()
        version = version_label or datetime.utcnow().strftime("v-%Y%m%d-%H%M%S")

        # Check for existing version to prevent overwrites
        if version in self.metadata["datasets"]:
            raise ValueError(f"Dataset version {version} already exists! Never overwrite datasets.")

        df = feature_df.copy()
        if "date" in df.columns:
            df = df.sort_values("date").reset_index(drop=True)

        n = len(df)
        if n < 10:
            raise ValueError(f"Dataset too small ({n} rows) for meaningful 70/15/15 time split.")

        # Strict chronological time-based split: 70% / 15% / 15%
        idx_train = int(n * 0.70)
        idx_val = int(n * 0.85)

        train_df = df.iloc[:idx_train].copy()
        val_df = df.iloc[idx_train:idx_val].copy()
        test_df = df.iloc[idx_val:].copy()

        # Save immutable files
        train_path = self.dirs["training"] / f"{symbol}_{version}_train.parquet"
        val_path = self.dirs["validation"] / f"{symbol}_{version}_val.parquet"
        test_path = self.dirs["test"] / f"{symbol}_{version}_test.parquet"

        try:
            train_df.to_parquet(train_path, index=False)
            val_df.to_parquet(val_path, index=False)
            test_df.to_parquet(test_path, index=False)
        except Exception:
            # Fallback to CSV if pyarrow/fastparquet not configured
            train_path = self.dirs["training"] / f"{symbol}_{version}_train.csv"
            val_path = self.dirs["validation"] / f"{symbol}_{version}_val.csv"
            test_path = self.dirs["test"] / f"{symbol}_{version}_test.csv"
            train_df.to_csv(train_path, index=False)
            val_df.to_csv(val_path, index=False)
            test_df.to_csv(test_path, index=False)

        metadata_entry = {
            "version": version,
            "symbol": symbol,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "total_rows": n,
            "train_rows": len(train_df),
            "val_rows": len(val_df),
            "test_rows": len(test_df),
            "train_path": str(train_path),
            "val_path": str(val_path),
            "test_path": str(test_path),
            "feature_columns": [c for c in df.columns if c not in ("date", "symbol")]
        }

        self.metadata["datasets"][version] = metadata_entry
        self.metadata["latest_version"] = version
        self._save_metadata()

        logger.info(
            f"[{symbol}] Created immutable dataset version={version} "
            f"(Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)})."
        )
        return metadata_entry

    def load_dataset_split(
        self,
        version: str,
        split: str = "train"
    ) -> pd.DataFrame:
        """
        Load an immutable train, validation, or test dataset split.
        """
        entry = self.metadata["datasets"].get(version)
        if not entry:
            raise ValueError(f"Dataset version {version} not found in registry!")

        key_map = {"train": "train_path", "validation": "val_path", "val": "val_path", "test": "test_path"}
        path_key = key_map.get(split.lower(), "train_path")
        file_path = Path(entry[path_key])

        if file_path.exists():
            if file_path.suffix == ".parquet":
                return pd.read_parquet(file_path)
            return pd.read_csv(file_path)
        return pd.DataFrame()


dataset_manager = DatasetManager()
