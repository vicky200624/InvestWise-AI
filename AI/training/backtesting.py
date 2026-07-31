"""
Walk-forward validation and backtesting engine for AI investment models.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class WalkForwardBacktester:
    """
    Implements walk-forward validation for financial time series models.
    """

    def __init__(self, train_window_days: int = 500, test_window_days: int = 60, step_days: int = 60):
        self.train_window_days = train_window_days
        self.test_window_days = test_window_days
        self.step_days = step_days

    def run_backtest(
        self,
        df: pd.DataFrame,
        model_train_fn: Any,
        model_predict_fn: Any,
        target_col: str = "Close",
    ) -> Dict[str, Any]:
        """
        Run walk-forward validation across historical dataset.

        Args:
            df: DataFrame containing Date index/column and features/target.
            model_train_fn: Callable taking train DataFrame and returning trained model.
            model_predict_fn: Callable taking trained model and test DataFrame and returning predictions.
            target_col: Target column name.

        Returns:
            Dict containing performance metrics: Sharpe ratio, Max Drawdown, Win Rate, Total Return.
        """
        if len(df) < self.train_window_days + self.test_window_days:
            logger.warning("Dataset too small for walk-forward backtest.")
            return {"error": "Insufficient data"}

        predictions = []
        actuals = []
        dates = []

        start_idx = 0
        while start_idx + self.train_window_days + self.test_window_days <= len(df):
            train_slice = df.iloc[start_idx : start_idx + self.train_window_days]
            test_slice = df.iloc[
                start_idx + self.train_window_days : start_idx + self.train_window_days + self.test_window_days
            ]

            try:
                model = model_train_fn(train_slice)
                preds = model_predict_fn(model, test_slice)
                predictions.extend(preds)
                actuals.extend(test_slice[target_col].values)
                if "Date" in test_slice.columns:
                    dates.extend(test_slice["Date"].values)
                else:
                    dates.extend(test_slice.index.values)
            except Exception as e:
                logger.error(f"Error during walk-forward fold: {e}")

            start_idx += self.step_days

        return self.calculate_metrics(np.array(actuals), np.array(predictions))

    @staticmethod
    def calculate_metrics(actuals: np.ndarray, predictions: np.ndarray) -> Dict[str, float]:
        """
        Calculate financial and ML metrics from actual vs predicted values.
        """
        if len(actuals) == 0 or len(predictions) == 0:
            return {"sharpe_ratio": 0.0, "max_drawdown": 0.0, "win_rate": 0.0, "mae": 0.0}

        # Calculate directional accuracy / win rate
        actual_returns = np.diff(actuals) / actuals[:-1]
        pred_returns = np.diff(predictions) / predictions[:-1]

        direction_match = np.sign(actual_returns) == np.sign(pred_returns)
        win_rate = float(np.mean(direction_match)) if len(direction_match) > 0 else 0.0

        # Strategy returns (long when pred_return > 0)
        strategy_returns = np.where(pred_returns > 0, actual_returns, 0.0)

        # Sharpe ratio (annualized assuming daily returns)
        mean_ret = np.mean(strategy_returns)
        std_ret = np.std(strategy_returns)
        sharpe_ratio = float((mean_ret / (std_ret + 1e-9)) * np.sqrt(252))

        # Max drawdown
        cum_returns = np.cumprod(1 + strategy_returns)
        peak = np.maximum.accumulate(cum_returns)
        drawdown = (cum_returns - peak) / peak
        max_drawdown = float(np.min(drawdown)) if len(drawdown) > 0 else 0.0

        mae = float(np.mean(np.abs(actuals - predictions)))

        return {
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown": round(max_drawdown, 4),
            "win_rate": round(win_rate, 4),
            "mae": round(mae, 4),
        }
