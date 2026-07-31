"""
Feature Engineering for InvestWise AI 3.0.
Generates 60+ features identically for offline training and online inference:
- Price Features (8)
- Technical Features (12)
- Financial Features (19)
- Valuation Features (8)
- Macro Features (8)
- News Features (9)
- Competitor Features (7)
No code duplication. No hardcoded values. Independently testable.
"""
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

logger = logging.getLogger("investwise.ai.training.feature_engineering")


class FeatureEngineer:
    """
    Computes 60+ standardized features from price time-series and domain data dictionaries.
    Must be identical in both offline training and online prediction pipelines.
    """
    @classmethod
    def engineer_features(
        cls,
        price_df: pd.DataFrame,
        financial_ratios: Optional[Dict[str, float]] = None,
        valuation_metrics: Optional[Dict[str, float]] = None,
        macro_indicators: Optional[Dict[str, float]] = None,
        news_features: Optional[Dict[str, Any]] = None,
        competitor_features: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Generate full feature matrix for a stock symbol DataFrame.
        """
        logger.info("Engineering 60+ features identically across pipelines...")
        if price_df.empty:
            return price_df

        df = price_df.copy()

        # Ensure base columns exist
        for col in ("open", "high", "low", "close", "volume"):
            if col not in df.columns:
                df[col] = np.nan
        if "adj_close" not in df.columns:
            df["adj_close"] = df["close"]

        # ----------------------------------------------------------------------
        # 1. PRICE FEATURES (8)
        # Open, High, Low, Close, Adjusted Close, Volume, Returns, Log Returns
        # ----------------------------------------------------------------------
        df["return_1d"] = df["close"].pct_change(1)
        df["log_return_1d"] = np.log(df["close"] / df["close"].shift(1))

        # ----------------------------------------------------------------------
        # 2. TECHNICAL FEATURES (12)
        # RSI, MACD, EMA, SMA, ATR, ADX, Bollinger Bands, Momentum, OBV, VWAP, Stochastic, CCI
        # ----------------------------------------------------------------------
        df["EMA_20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["SMA_50"] = df["close"].rolling(window=50, min_periods=1).mean()

        # RSI_14
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss + 1e-9)
        df["RSI_14"] = 100.0 - (100.0 / (1.0 + rs))

        # MACD
        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema_12 - ema_26

        # Bollinger Bands (20-day, 2 sigma)
        sma_20 = df["close"].rolling(window=20, min_periods=1).mean()
        std_20 = df["close"].rolling(window=20, min_periods=1).std().fillna(0)
        df["BB_UPPER"] = sma_20 + 2.0 * std_20
        df["BB_LOWER"] = sma_20 - 2.0 * std_20

        # ATR_14 (Average True Range)
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["ATR_14"] = true_range.rolling(window=14, min_periods=1).mean()

        # ADX_14 (Average Directional Index simplified)
        up_move = df["high"] - df["high"].shift(1)
        down_move = df["low"].shift(1) - df["low"]
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        plus_di = 100 * pd.Series(plus_dm).rolling(window=14, min_periods=1).mean() / (df["ATR_14"] + 1e-9)
        minus_di = 100 * pd.Series(minus_dm).rolling(window=14, min_periods=1).mean() / (df["ATR_14"] + 1e-9)
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
        df["ADX_14"] = dx.rolling(window=14, min_periods=1).mean()

        # MOMENTUM_10
        df["MOMENTUM_10"] = df["close"] - df["close"].shift(10)

        # OBV (On-Balance Volume)
        direction = np.sign(df["close"].diff()).fillna(0)
        df["OBV"] = (direction * df["volume"]).cumsum()

        # VWAP
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        df["VWAP"] = (typical_price * df["volume"]).cumsum() / (df["volume"].cumsum() + 1e-9)

        # STOCH_K (Stochastic Oscillator %K)
        low_14 = df["low"].rolling(window=14, min_periods=1).min()
        high_14 = df["high"].rolling(window=14, min_periods=1).max()
        df["STOCH_K"] = 100.0 * (df["close"] - low_14) / (high_14 - low_14 + 1e-9)

        # CCI_20 (Commodity Channel Index)
        tp_sma20 = typical_price.rolling(window=20, min_periods=1).mean()
        tp_mad = typical_price.rolling(window=20, min_periods=1).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True).fillna(1.0)
        df["CCI_20"] = (typical_price - tp_sma20) / (0.015 * tp_mad + 1e-9)

        # ----------------------------------------------------------------------
        # 3. FINANCIAL FEATURES (19)
        # Revenue Growth, EPS Growth, ROE, ROA, ROCE, Operating Margin, Gross Margin,
        # Net Margin, Debt Equity, Interest Coverage, Current Ratio, Quick Ratio,
        # Free Cash Flow, Book Value, Dividend Yield, PEG, P/E, P/B, EV/EBITDA
        # ----------------------------------------------------------------------
        fin = financial_ratios or {}
        fin_keys = [
            "revenue_growth", "eps_growth", "roe", "roa", "roce",
            "operating_margin", "gross_margin", "net_margin", "debt_to_equity",
            "interest_coverage", "current_ratio", "quick_ratio", "free_cash_flow",
            "book_value_per_share", "dividend_yield", "peg_ratio", "pe_ratio",
            "pb_ratio", "ev_to_ebitda"
        ]
        for key in fin_keys:
            df[f"fin_{key}"] = float(fin.get(key, 0.0))

        # ----------------------------------------------------------------------
        # 4. VALUATION FEATURES (8)
        # DCF, Intrinsic Value, Margin of Safety, Enterprise Value, Market Cap,
        # Fair Value, Growth Rate, Expected CAGR
        # ----------------------------------------------------------------------
        val = valuation_metrics or {}
        val_keys = [
            "dcf", "intrinsic_value", "margin_of_safety", "enterprise_value",
            "market_cap", "fair_value", "growth_rate", "expected_cagr"
        ]
        for key in val_keys:
            df[f"val_{key}"] = float(val.get(key, 0.0))

        # ----------------------------------------------------------------------
        # 5. MACRO FEATURES (8)
        # GDP Growth, Inflation, Interest Rates, Currency, Oil Prices, Gold Prices,
        # Bond Yield, Unemployment
        # ----------------------------------------------------------------------
        mac = macro_indicators or {}
        mac_keys = [
            "gdp_growth", "inflation_rate", "interest_rate", "usd_inr",
            "oil_price_usd", "gold_price_usd", "bond_yield_10y", "unemployment_rate"
        ]
        for key in mac_keys:
            df[f"mac_{key}"] = float(mac.get(key, 0.0))

        # ----------------------------------------------------------------------
        # 6. NEWS FEATURES (9)
        # Sentiment Score, Confidence, Topic Classification, Positive/Negative Mentions,
        # Risk Events, CEO/Product/Competitor Mentions
        # ----------------------------------------------------------------------
        nws = news_features or {}
        df["news_sentiment_score"] = float(nws.get("sentiment_score", 0.5))
        df["news_confidence"] = float(nws.get("confidence", 0.5))
        df["news_positive_mentions"] = float(nws.get("positive_mentions", 0.0))
        df["news_negative_mentions"] = float(nws.get("negative_mentions", 0.0))
        df["news_risk_events_detected"] = float(nws.get("risk_events_detected", 0.0))
        df["news_ceo_mentions"] = float(nws.get("ceo_mentions", 0.0))
        df["news_product_mentions"] = float(nws.get("product_mentions", 0.0))
        df["news_competitor_mentions"] = float(nws.get("competitor_mentions", 0.0))
        topics = nws.get("topic_classification", [])
        df["news_topic_count"] = float(len(topics) if isinstance(topics, list) else 0.0)

        # ----------------------------------------------------------------------
        # 7. COMPETITOR FEATURES (7)
        # Industry Rank, Market Share, Revenue Comparison, Margin Comparison,
        # Innovation Score, Patent Count, Brand Strength
        # ----------------------------------------------------------------------
        comp = competitor_features or {}
        comp_keys = [
            "industry_rank", "market_share_percent",
            "revenue_vs_peer_avg_percent", "margin_vs_peer_avg_percent",
            "innovation_score", "patent_count", "brand_strength_score"
        ]
        for key in comp_keys:
            df[f"comp_{key}"] = float(comp.get(key, 0.0))

        # Target column for training (5-day forward return)
        df["Target_Return_5d"] = df["close"].pct_change(5).shift(-5)

        # Fill any minor initial NaN Technical indicator values cleanly
        df = df.bfill().ffill().fillna(0.0)

        logger.info(f"Engineering complete: created {df.shape[1]} total columns.")
        return df


engineer_features = FeatureEngineer.engineer_features
