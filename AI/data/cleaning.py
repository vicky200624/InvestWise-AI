"""
Data Cleaning Engine for InvestWise AI 3.0.
Handles:
- Missing Values (forward/backward fill, median interpolation for volume)
- Duplicate Records deduplication
- Invalid Prices and Negative Volume correction
- Extreme Outliers winsorization / clipping
- Corporate Actions adjustments (Stock Splits, Bonuses)
"""
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger("investwise.ai.data.cleaning")


class DataCleaner:
    """
    Cleans validated financial time-series data into standardized,
    split-adjusted DataFrames ready for feature engineering.
    """
    @staticmethod
    def clean_timeseries(symbol: str, raw_bars: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Clean and normalize raw OHLCV time-series records.
        """
        if not raw_bars:
            return pd.DataFrame()

        df = pd.DataFrame(raw_bars)

        # 1. Standardize column names and types
        expected_cols = ["date", "open", "high", "low", "close", "volume"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = np.nan

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # 2. Handle Duplicate Records (keep last entry per date)
        before_dupes = len(df)
        df = df.drop_duplicates(subset=["date"], keep="last")
        dupes_removed = before_dupes - len(df)
        if dupes_removed > 0:
            logger.info(f"[{symbol}] Removed {dupes_removed} duplicate date rows.")

        # 3. Handle Negative Volume or Zero Prices
        df["volume"] = df["volume"].apply(lambda v: abs(v) if pd.notnull(v) and v < 0 else v)
        for p_col in ("open", "high", "low", "close"):
            df[p_col] = df[p_col].apply(lambda p: np.nan if pd.notnull(p) and p <= 0 else p)

        # 4. Handle Missing Values (forward fill up to 3 days, then backfill)
        df["close"] = df["close"].ffill(limit=3).bfill()
        df["open"] = df["open"].fillna(df["close"])
        df["high"] = df["high"].fillna(df[["open", "close"]].max(axis=1))
        df["low"] = df["low"].fillna(df[["open", "close"]].min(axis=1))
        
        median_vol = df["volume"].median()
        df["volume"] = df["volume"].fillna(median_vol if pd.notnull(median_vol) else 1000000)

        # 5. Handle Corporate Actions (Stock Splits / Bonuses detection & adjustment)
        df = DataCleaner._adjust_for_splits_and_bonuses(symbol, df)

        # 6. Clip extreme non-split returns outliers using IQR winsorization
        df = DataCleaner._clip_outliers(df)

        df["symbol"] = symbol.upper().strip()
        logger.info(f"[{symbol}] Data cleaning complete. Final rows: {len(df)}")
        return df

    @staticmethod
    def _adjust_for_splits_and_bonuses(symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and adjust historical OHLCV for stock splits and bonus issues.
        If overnight ratio is close to 2.0 (2:1 split), 5.0 (5:1 split), or 10.0 (10:1 split),
        adjust all prior prices downward and prior volumes upward.
        """
        if len(df) < 2:
            return df

        closes = df["close"].values
        split_ratios = [2.0, 3.0, 4.0, 5.0, 10.0]

        for i in range(1, len(closes)):
            prev_c = closes[i - 1]
            curr_c = closes[i]
            if prev_c <= 0 or curr_c <= 0:
                continue

            ratio = prev_c / curr_c
            for target_ratio in split_ratios:
                if 0.95 * target_ratio <= ratio <= 1.05 * target_ratio:
                    logger.warning(
                        f"[{symbol}] Detected {target_ratio:.0f}:1 stock split/bonus on "
                        f"{df.iloc[i]['date']}. Adjusting historical OHLCV prior to this date."
                    )
                    df.loc[:i - 1, ["open", "high", "low", "close"]] /= target_ratio
                    df.loc[:i - 1, "volume"] *= target_ratio
                    break

        return df

    @staticmethod
    def _clip_outliers(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        Winsorize extreme return spikes > 4 standard deviations from 20-day rolling mean.
        """
        if len(df) < window:
            return df

        returns = df["close"].pct_change()
        mean_ret = returns.rolling(window=window, min_periods=5).mean()
        std_ret = returns.rolling(window=window, min_periods=5).std()

        upper_bound = mean_ret + 4.0 * std_ret
        lower_bound = mean_ret - 4.0 * std_ret

        # If a day's return exceeds 4 sigma, clip it
        clipped_ret = returns.clip(lower=lower_bound, upper=upper_bound)
        
        # Reconstruct closes if clipping occurred
        if not returns.equals(clipped_ret):
            for i in range(1, len(df)):
                df.loc[i, "close"] = df.loc[i - 1, "close"] * (1.0 + clipped_ret.iloc[i])
                
        return df


data_cleaner = DataCleaner()
