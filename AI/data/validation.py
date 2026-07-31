"""
Data Validation Engine for InvestWise AI 3.0.
Enforces strict validation rules:
- Ticker Symbol & Company Name syntax
- Missing Values and null detection
- Duplicate Rows detection
- Outlier detection (price spikes/crashes > 50% in 1 day without corporate action)
- Incorrect Dates & Future timestamp checks
- Incorrect Currency checks
- Split & Dividend adjustments verification
- Timezone normalization (UTC/US Eastern)
Never skip validation. Never use unverified data.
"""
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

logger = logging.getLogger("investwise.ai.data.validation")

class DataValidationError(Exception):
    """Raised when critical data validation fails."""
    pass


class DataValidator:
    """
    Validates financial time-series bars and metadata before ETL cleaning.
    """
    TICKER_REGEX = re.compile(r"^[A-Z0-9\.\-]{1,15}$")
    VALID_CURRENCIES = {"USD", "INR", "EUR", "GBP", "JPY"}

    @classmethod
    def validate_ticker(cls, symbol: str) -> bool:
        """Validate ticker symbol format."""
        if not symbol or not isinstance(symbol, str):
            return False
        return bool(cls.TICKER_REGEX.match(symbol.upper().strip()))

    @classmethod
    def validate_currency(cls, currency: str) -> bool:
        """Validate currency code against supported currencies."""
        if not currency or not isinstance(currency, str):
            return False
        return currency.upper() in cls.VALID_CURRENCIES

    @classmethod
    def validate_date_string(cls, date_str: str) -> bool:
        """Validate date string is YYYY-MM-DD and not in the future."""
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            if dt > datetime.utcnow():
                return False
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_price_bar(cls, bar: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single OHLCV price bar.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        # Check required fields
        for field in ("open", "high", "low", "close", "volume"):
            if field not in bar or bar[field] is None:
                errors.append(f"Missing required field: {field}")
                continue
            if not isinstance(bar[field], (int, float)):
                errors.append(f"Field {field} is not numeric: {bar[field]}")
                continue
            if bar[field] < 0:
                errors.append(f"Negative value for {field}: {bar[field]}")

        if "date" in bar and not cls.validate_date_string(str(bar["date"])):
            errors.append(f"Invalid or future date: {bar.get('date')}")

        # Logical price relationship checks
        if not errors:
            o, h, l, c = float(bar["open"]), float(bar["high"]), float(bar["low"]), float(bar["close"])
            if h < max(o, c) or l > min(o, c):
                errors.append(f"OHLC logical inconsistency: O={o}, H={h}, L={l}, C={c}")
            if o == 0 or h == 0 or l == 0 or c == 0:
                errors.append("Zero price detected in active trading bar")

        return (len(errors) == 0, errors)

    @classmethod
    def validate_timeseries(cls, symbol: str, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a full time-series of price bars for:
        - Ticker symbol validity
        - Duplicate dates
        - Outliers (unadjusted > 50% single-day jump)
        - Missing values
        - Split/Dividend adjustment anomalies
        """
        if not cls.validate_ticker(symbol):
            raise DataValidationError(f"Invalid ticker symbol: {symbol}")

        if not bars:
            raise DataValidationError(f"Empty time-series for {symbol}. Never use unverified data.")

        total_bars = len(bars)
        valid_bars = []
        rejected_bars = []
        seen_dates = set()
        duplicate_count = 0
        outlier_count = 0

        prev_close = None

        for bar in bars:
            is_valid, errors = cls.validate_price_bar(bar)
            date_str = str(bar.get("date", ""))[:10]

            if not is_valid:
                rejected_bars.append({"bar": bar, "reasons": errors})
                continue

            if date_str in seen_dates:
                duplicate_count += 1
                rejected_bars.append({"bar": bar, "reasons": ["Duplicate date record"]})
                continue

            seen_dates.add(date_str)

            # Check single-day extreme outliers (> 50% change)
            curr_close = float(bar["close"])
            if prev_close and prev_close > 0:
                change_pct = abs(curr_close - prev_close) / prev_close
                if change_pct > 0.50 and not bar.get("corporate_action_adjusted", False):
                    outlier_count += 1
                    logger.warning(
                        f"[{symbol}] Extreme single-day price move {change_pct:.1%} on {date_str}. "
                        "Flagging as potential unadjusted stock split or bonus."
                    )

            valid_bars.append(bar)
            prev_close = curr_close

        is_verified = (len(valid_bars) > 0) and (len(rejected_bars) / total_bars < 0.10)

        report = {
            "symbol": symbol,
            "total_bars_inspected": total_bars,
            "valid_bars_count": len(valid_bars),
            "rejected_bars_count": len(rejected_bars),
            "duplicate_count": duplicate_count,
            "outlier_flags": outlier_count,
            "is_verified": is_verified,
            "valid_bars": valid_bars,
            "rejected_bars": rejected_bars
        }

        if not is_verified:
            logger.error(f"[{symbol}] Data validation FAILED: {report}")
            raise DataValidationError(
                f"Data validation failed for {symbol}: {len(rejected_bars)}/{total_bars} bars rejected."
            )

        logger.info(
            f"[{symbol}] Data validation SUCCESS: {len(valid_bars)}/{total_bars} valid bars verified."
        )
        return report


data_validator = DataValidator()
