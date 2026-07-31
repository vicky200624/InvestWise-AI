"""
Reward signal calculation for user feedback and market outcome evaluation.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RewardCalculator:
    """
    Computes numerical reward signals from user feedback and observed stock performance.
    """

    @staticmethod
    def calculate_reward(
        feedback_type: str,
        predicted_score: float,
        actual_return_percent: Optional[float] = None,
        user_confidence_weight: float = 1.0,
    ) -> float:
        """
        Calculate a continuous reward signal in range [-1.0, 1.0].

        Args:
            feedback_type: 'AGREE', 'DISAGREE', 'HELPFUL', 'UNHELPFUL', or 'OUTCOME_EVAL'.
            predicted_score: The 0-100 score predicted by AI.
            actual_return_percent: Percentage return observed after recommendation horizon (if available).
            user_confidence_weight: Multiplier based on user reliability/weight.

        Returns:
            float reward value between -1.0 and 1.0.
        """
        base_reward = 0.0

        if feedback_type.upper() == "AGREE" or feedback_type.upper() == "HELPFUL":
            base_reward = 0.5 * user_confidence_weight
        elif feedback_type.upper() == "DISAGREE" or feedback_type.upper() == "UNHELPFUL":
            base_reward = -0.5 * user_confidence_weight
        elif feedback_type.upper() == "OUTCOME_EVAL" and actual_return_percent is not None:
            # Check if recommendation direction matched actual return
            is_bullish = predicted_score >= 65.0
            is_bearish = predicted_score <= 35.0

            if is_bullish and actual_return_percent > 0:
                base_reward = min(1.0, actual_return_percent / 10.0)
            elif is_bullish and actual_return_percent < 0:
                base_reward = max(-1.0, actual_return_percent / 10.0)
            elif is_bearish and actual_return_percent < 0:
                base_reward = min(1.0, abs(actual_return_percent) / 10.0)
            elif is_bearish and actual_return_percent > 0:
                base_reward = max(-1.0, -actual_return_percent / 10.0)
            else:
                base_reward = 0.0

        return round(max(-1.0, min(1.0, base_reward)), 4)
