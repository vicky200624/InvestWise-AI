"""
Feedback processing and training dataset enhancement from user interactions.
Standalone module with zero Django dependencies.
"""

import logging
from typing import List, Dict, Any
from .reward_model import RewardCalculator

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """
    Processes collected feedback records to generate tuning weights for ML models.
    """

    def __init__(self, reward_calculator: RewardCalculator = None):
        self.reward_calculator = reward_calculator or RewardCalculator()

    def process_feedback_batch(self, feedback_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of raw feedback dictionaries and calculate reward signals.

        Args:
            feedback_records: List of dicts with keys 'feedback_type', 'predicted_score', 'actual_return_percent'.

        Returns:
            List of dicts enriched with 'reward_signal' and 'sample_weight'.
        """
        processed = []
        for rec in feedback_records:
            try:
                reward = self.reward_calculator.calculate_reward(
                    feedback_type=rec.get("feedback_type", "HELPFUL"),
                    predicted_score=float(rec.get("predicted_score", 50.0)),
                    actual_return_percent=rec.get("actual_return_percent"),
                )
                # Sample weight is higher for strong positive or negative rewards
                sample_weight = 1.0 + abs(reward)

                processed.append({
                    **rec,
                    "reward_signal": reward,
                    "sample_weight": round(sample_weight, 4),
                })
            except Exception as e:
                logger.error(f"Error processing feedback record {rec}: {e}")

        return processed
