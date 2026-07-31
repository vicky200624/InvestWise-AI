"""
Unit Tests for InvestWise AI 3.0 — Part 3: Data Engineering Architecture.
Tests:
- Data Validation (ticker, date, currency, duplicates, outliers)
- Data Cleaning (missing values, deduplication, split/bonus adjustment)
- 60+ Feature Engineering (7 categories identically generated)
- Feature Store (versioned persistence and online lookup)
- Dataset Manager (immutable versioning and chronological 70/15/15 split)
- Model Registry & Promotion Protocol (Candidate -> Human Approval -> Production)
- Redis Cache TTL enforcement across Domain Services
"""
import unittest
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from AI.data.validation import data_validator, DataValidationError
from AI.data.cleaning import data_cleaner
from AI.training.feature_engineering import engineer_features
from AI.data.feature_store import FeatureStore
from AI.data.dataset_manager import DatasetManager
from AI.models.model_registry import ModelRegistry, ModelPromotionError
from backend.services.market_service import market_service, MARKET_PRICE_TTL
from backend.services.news_service import news_service, NEWS_TTL
from backend.services.macro_service import macro_service, MACRO_TTL


class TestDataEngineeringArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("/tmp/investwise_test_data_engineering")
        cls.test_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. DATA VALIDATION TESTS
    # --------------------------------------------------------------------------
    def test_ticker_and_currency_validation(self):
        self.assertTrue(data_validator.validate_ticker("AAPL"))
        self.assertTrue(data_validator.validate_ticker("RELIANCE.NS"))
        self.assertFalse(data_validator.validate_ticker("INVALID_TICKER_WITH_SPECIAL_CHARS###"))
        self.assertFalse(data_validator.validate_ticker(""))
        
        self.assertTrue(data_validator.validate_currency("USD"))
        self.assertTrue(data_validator.validate_currency("INR"))
        self.assertFalse(data_validator.validate_currency("XYZ_INVALID"))

    def test_date_and_future_timestamp_validation(self):
        past_date = "2025-01-15"
        self.assertTrue(data_validator.validate_date_string(past_date))

        future_date = (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d")
        self.assertFalse(data_validator.validate_date_string(future_date))

    def test_timeseries_validation_rejects_unverified_data(self):
        bad_bars = [
            {"date": "2025-01-01", "open": -10, "high": 100, "low": 90, "close": 95, "volume": -500},
            {"date": "2025-01-02", "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0},
        ]
        with self.assertRaises(DataValidationError):
            data_validator.validate_timeseries("AAPL", bad_bars)

    # --------------------------------------------------------------------------
    # 2. DATA CLEANING & CORPORATE ACTIONS TESTS
    # --------------------------------------------------------------------------
    def test_cleaning_deduplication_and_missing_values(self):
        raw_bars = [
            {"date": "2025-01-01", "open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000},
            {"date": "2025-01-01", "open": 100, "high": 106, "low": 99, "close": 104, "volume": 2000}, # Duplicate date
            {"date": "2025-01-02", "open": None, "high": None, "low": None, "close": None, "volume": None}, # Missing bar
            {"date": "2025-01-03", "open": 105, "high": 108, "low": 103, "close": 107, "volume": -1500}, # Negative vol
        ]
        cleaned_df = data_cleaner.clean_timeseries("AAPL", raw_bars)
        
        # Deduplication: 3 unique dates should remain
        self.assertEqual(len(cleaned_df), 3)
        # 2025-01-01 should keep the last row (close=104)
        self.assertEqual(cleaned_df.iloc[0]["close"], 104)
        # 2025-01-02 should be forward filled from 104
        self.assertEqual(cleaned_df.iloc[1]["close"], 104)
        # Negative volume should be absolute-valued or imputed
        self.assertGreater(cleaned_df.iloc[2]["volume"], 0)

    def test_stock_split_and_bonus_adjustment(self):
        raw_bars = [
            {"date": "2025-01-01", "open": 200, "high": 204, "low": 198, "close": 200, "volume": 1000},
            {"date": "2025-01-02", "open": 202, "high": 206, "low": 200, "close": 202, "volume": 1100},
            # 2:1 Split occurs overnight: price drops from 202 -> 101, volume doubles
            {"date": "2025-01-03", "open": 101, "high": 103, "low": 99, "close": 101, "volume": 2200},
        ]
        df = data_cleaner.clean_timeseries("AAPL", raw_bars)
        
        # Prior closes (initially 200, 202) should be adjusted downward by ~2.0 to ~100, 101
        self.assertAlmostEqual(df.iloc[0]["close"], 100.0, delta=1.0)
        self.assertAlmostEqual(df.iloc[1]["close"], 101.0, delta=1.0)

    # --------------------------------------------------------------------------
    # 3. 60+ FEATURE ENGINEERING TESTS
    # --------------------------------------------------------------------------
    def test_60_plus_feature_generation(self):
        bars = []
        for i in range(40):
            p = 100.0 + i
            bars.append({
                "date": f"2025-01-{(i % 28) + 1:02d}",
                "open": p - 1, "high": p + 2, "low": p - 2, "close": p,
                "volume": 10000 + i * 100
            })
        df = pd.DataFrame(bars)
        
        feat_df = engineer_features(
            price_df=df,
            financial_ratios={"roe": 0.22, "revenue_growth": 0.15, "free_cash_flow": 1200000000.0},
            valuation_metrics={"dcf": 135.0, "intrinsic_value": 140.0, "expected_cagr": 0.16},
            macro_indicators={"gdp_growth": 2.8, "interest_rate": 5.25},
            news_features={"sentiment_score": 0.72, "confidence": 0.88, "positive_mentions": 15},
            competitor_features={"industry_rank": 1, "innovation_score": 90.0}
        )

        # Check required columns across all 7 categories
        required_cols = [
            "return_1d", "log_return_1d",  # Price
            "RSI_14", "MACD", "EMA_20", "SMA_50", "ATR_14", "ADX_14", "BB_UPPER", "BB_LOWER", # Technical
            "fin_roe", "fin_revenue_growth", "fin_free_cash_flow",  # Financial
            "val_dcf", "val_intrinsic_value", "val_expected_cagr",  # Valuation
            "mac_gdp_growth", "mac_interest_rate",                  # Macro
            "news_sentiment_score", "news_confidence",              # News
            "comp_industry_rank", "comp_innovation_score",          # Competitor
            "Target_Return_5d"                                      # Target
        ]
        for col in required_cols:
            self.assertIn(col, feat_df.columns, f"Missing engineered column: {col}")

        # Ensure no unexpected NaNs in generated technical indicators
        self.assertFalse(feat_df["RSI_14"].isnull().any())
        self.assertFalse(feat_df["MACD"].isnull().any())

    # --------------------------------------------------------------------------
    # 4. REUSABLE FEATURE STORE TESTS
    # --------------------------------------------------------------------------
    def test_feature_store_versioning_and_lookup(self):
        store = FeatureStore(store_dir=self.test_dir / "features")
        bars = [{"date": "2025-01-01", "close": 150.0, "return_1d": 0.02, "RSI_14": 55.0}]
        df = pd.DataFrame(bars)
        
        meta = store.save_features("TEST", df, version="v1.0.0-test")
        self.assertEqual(meta["version"], "v1.0.0-test")

        hist = store.get_historical_features("TEST", version="v1.0.0-test")
        self.assertEqual(len(hist), 1)

        latest = store.get_latest_features("TEST", version="v1.0.0-test")
        self.assertIn("RSI_14", latest)
        self.assertEqual(latest["RSI_14"], 55.0)

    # --------------------------------------------------------------------------
    # 5. IMMUTABLE DATASET VERSIONING & 70/15/15 CHRONOLOGICAL SPLITS
    # --------------------------------------------------------------------------
    def test_dataset_manager_chronological_split_and_immutability(self):
        dm = DatasetManager(root_dir=self.test_dir / "datasets")
        rows = []
        for i in range(100):
            rows.append({
                "date": f"2025-01-{(i % 28) + 1:02d}",
                "symbol": "TEST",
                "close": 100 + i,
                "feature_x": i * 0.1
            })
        df = pd.DataFrame(rows)
        
        version = "v2026-test-1"
        meta = dm.create_dataset_version("TEST", df, version_label=version)
        
        # Check 70% Train, 15% Validation, 15% Test
        self.assertEqual(meta["train_rows"], 70)
        self.assertEqual(meta["val_rows"], 15)
        self.assertEqual(meta["test_rows"], 15)

        # Immutability check: never overwrite existing dataset version
        with self.assertRaises(ValueError):
            dm.create_dataset_version("TEST", df, version_label=version)

    # --------------------------------------------------------------------------
    # 6. MODEL REGISTRY & MODEL PROMOTION PROTOCOL
    # --------------------------------------------------------------------------
    def test_model_promotion_protocol(self):
        reg = ModelRegistry(models_dir=self.test_dir / "models")
        
        # 1. Register candidate
        version = "v1.0.0-candidate"
        reg.register_candidate(
            model_type="xgboost",
            version=version,
            metrics={"accuracy": 0.81, "sharpe_ratio": 1.95},
            hyperparameters={"n_estimators": 200},
            dataset_version="v2026-test-1"
        )
        
        # Verify status is Candidate and NOT Production
        entry = reg.metadata["models"][version]
        self.assertEqual(entry["status"], "Candidate")
        self.assertIsNone(reg.get_production_model())

        # 2. Promote to Production after human approval
        promoted = reg.promote_to_production(version, approved_by="Chief Risk Officer")
        self.assertEqual(promoted["status"], "Production")
        self.assertEqual(promoted["approved_by"], "Chief Risk Officer")

        # Verify active production model is set
        prod = reg.get_production_model()
        self.assertIsNotNone(prod)
        self.assertEqual(prod["version"], version)

    # --------------------------------------------------------------------------
    # 7. REDIS TTL ENFORCEMENT ON DOMAIN SERVICES
    # --------------------------------------------------------------------------
    def test_service_ttls_match_spec(self):
        self.assertEqual(MARKET_PRICE_TTL, 300)   # 5 Minutes
        self.assertEqual(NEWS_TTL, 1800)          # 30 Minutes
        self.assertEqual(MACRO_TTL, 86400)        # 24 Hours


if __name__ == "__main__":
    unittest.main()
