"""
Enhanced reward model incorporating multiple factors for comprehensive reward calculation.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .reward_model import RewardCalculator

logger = logging.getLogger(__name__)


@dataclass
class RewardComponents:
    """Breakdown of reward calculation components."""
    recommendation_accuracy: float = 0.0
    portfolio_return: float = 0.0
    user_satisfaction: float = 0.0
    holding_duration: float = 0.0
    risk_reduction: float = 0.0
    loss_prevention: float = 0.0
    explainability_score: float = 0.0
    
    def total(self) -> float:
        """Calculate weighted total reward."""
        weights = {
            'recommendation_accuracy': 0.30,
            'portfolio_return': 0.25,
            'user_satisfaction': 0.20,
            'holding_duration': 0.10,
            'risk_reduction': 0.10,
            'loss_prevention': 0.05,
        }
        total = (
            self.recommendation_accuracy * weights['recommendation_accuracy'] +
            self.portfolio_return * weights['portfolio_return'] +
            self.user_satisfaction * weights['user_satisfaction'] +
            self.holding_duration * weights['holding_duration'] +
            self.risk_reduction * weights['risk_reduction'] +
            self.loss_prevention * weights['loss_prevention']
        )
        return max(-1.0, min(1.0, total))


class EnhancedRewardCalculator:
    """
    Advanced reward calculation incorporating multiple factors.
    """

    def __init__(self):
        self.base_calculator = RewardCalculator()

    def calculate_enhanced_reward(
        self,
        feedback_type: str,
        predicted_score: float,
        actual_return_percent: Optional[float] = None,
        user_confidence_weight: float = 1.0,
        portfolio_before: Optional[Dict[str, Any]] = None,
        portfolio_after: Optional[Dict[str, Any]] = None,
        holding_duration_days: Optional[int] = None,
        risk_before: Optional[float] = None,
        risk_after: Optional[float] = None,
        explanation_quality: Optional[float] = None,
    ) -> tuple[float, RewardComponents]:
        """
        Calculate comprehensive reward with component breakdown.
        
        Returns:
            Tuple of (total_reward, RewardComponents)
        """
        components = RewardComponents()
        
        # 1. Recommendation Accuracy (30%)
        base_reward = self.base_calculator.calculate_reward(
            feedback_type=feedback_type,
            predicted_score=predicted_score,
            actual_return_percent=actual_return_percent,
            user_confidence_weight=user_confidence_weight,
        )
        components.recommendation_accuracy = base_reward
        
        # 2. Portfolio Return (25%)
        if actual_return_percent is not None:
            # Normalize return to [-1, 1] range
            components.portfolio_return = max(-1.0, min(1.0, actual_return_percent / 20.0))
        
        # 3. User Satisfaction (20%)
        if feedback_type.upper() in ['AGREE', 'HELPFUL', 'ACCEPTED']:
            components.user_satisfaction = 0.5 * user_confidence_weight
        elif feedback_type.upper() in ['DISAGREE', 'UNHELPFUL', 'REJECTED']:
            components.user_satisfaction = -0.5 * user_confidence_weight
        
        # 4. Holding Duration (10%)
        if holding_duration_days is not None:
            # Optimal holding period is 30-365 days
            if 30 <= holding_duration_days <= 365:
                components.holding_duration = 0.5
            elif holding_duration_days < 30:
                components.holding_duration = -0.3  # Too short, likely speculative
            else:
                components.holding_duration = 0.3  # Long-term holding
        
        # 5. Risk Reduction (10%)
        if risk_before is not None and risk_after is not None:
            risk_change = risk_before - risk_after
            components.risk_reduction = max(-1.0, min(1.0, risk_change))
        
        # 6. Loss Prevention (5%)
        if actual_return_percent is not None and actual_return_percent < 0:
            # If prediction was bearish and loss occurred, reward for loss prevention
            if predicted_score <= 35.0:
                components.loss_prevention = min(0.5, abs(actual_return_percent) / 20.0)
            else:
                components.loss_prevention = max(-0.5, actual_return_percent / 20.0)
        
        # 7. Explainability Score (not included in total, tracked separately)
        if explanation_quality is not None:
            components.explainability_score = explanation_quality
        
        total_reward = components.total()
        return round(total_reward, 4), components

    def calculate_batch_rewards(
        self, feedback_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of feedback records with enhanced reward calculation.
        """
        results = []
        for rec in feedback_records:
            try:
                reward, components = self.calculate_enhanced_reward(
                    feedback_type=rec.get("feedback_type", "HELPFUL"),
                    predicted_score=float(rec.get("predicted_score", 50.0)),
                    actual_return_percent=rec.get("actual_return_percent"),
                    user_confidence_weight=rec.get("user_confidence_weight", 1.0),
                    portfolio_before=rec.get("portfolio_before"),
                    portfolio_after=rec.get("portfolio_after"),
                    holding_duration_days=rec.get("holding_duration_days"),
                    risk_before=rec.get("risk_before"),
                    risk_after=rec.get("risk_after"),
                    explanation_quality=rec.get("explanation_quality"),
                )
                
                results.append({
                    **rec,
                    "reward_signal": reward,
                    "reward_components": {
                        "recommendation_accuracy": components.recommendation_accuracy,
                        "portfolio_return": components.portfolio_return,
                        "user_satisfaction": components.user_satisfaction,
                        "holding_duration": components.holding_duration,
                        "risk_reduction": components.risk_reduction,
                        "loss_prevention": components.loss_prevention,
                        "explainability_score": components.explainability_score,
                    },
                    "sample_weight": 1.0 + abs(reward),
                })
            except Exception as e:
                logger.error(f"Error calculating enhanced reward for record {rec}: {e}")
        
        return results