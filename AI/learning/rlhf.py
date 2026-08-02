"""
Reinforcement Learning from Human Feedback (RLHF) for InvestWise AI.
Influences recommendation strategies without modifying production model weights.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class RLHFAdjustments:
    """RLHF adjustment parameters for recommendation strategies."""
    ranking_boost: Dict[str, float] = field(default_factory=dict)  # sector/company -> boost factor
    confidence_adjustment: float = 1.0  # Multiplier for confidence scores
    priority_weights: Dict[str, float] = field(default_factory=dict)  # strategy -> weight
    explanation_quality_target: float = 0.8  # Target explainability score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ranking_boost': self.ranking_boost,
            'confidence_adjustment': self.confidence_adjustment,
            'priority_weights': self.priority_weights,
            'explanation_quality_target': self.explanation_quality_target,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RLHFAdjustments':
        return cls(
            ranking_boost=data.get('ranking_boost', {}),
            confidence_adjustment=data.get('confidence_adjustment', 1.0),
            priority_weights=data.get('priority_weights', {}),
            explanation_quality_target=data.get('explanation_quality_target', 0.8),
        )


class RLHFTrainer:
    """
    Reinforcement Learning from Human Feedback system.
    Never directly changes XGBoost weights.
    Influences future recommendation strategies instead.
    """

    def __init__(self):
        self.user_adjustments: Dict[int, RLHFAdjustments] = {}
        self.global_adjustments = RLHFAdjustments()
        self.feedback_history: List[Dict[str, Any]] = []
        self.learning_rate = 0.1
        self.discount_factor = 0.95

    def record_feedback(self, user_id: int, feedback_data: Dict[str, Any]) -> None:
        """
        Record user feedback for RLHF training.
        
        Args:
            user_id: User identifier
            feedback_data: Dict containing feedback_type, symbol, sector, confidence, etc.
        """
        self.feedback_history.append({
            'user_id': user_id,
            **feedback_data
        })
        
        # Keep only recent feedback (last 1000 per user)
        user_feedback = [f for f in self.feedback_history if f['user_id'] == user_id]
        if len(user_feedback) > 1000:
            self.feedback_history = [
                f for f in self.feedback_history 
                if f['user_id'] != user_id or len([uf for uf in user_feedback if uf['user_id'] == user_id]) <= 1000
            ]

    def calculate_ranking_boost(self, user_id: int, sector: str, company: str) -> float:
        """
        Calculate ranking boost for a sector/company based on user feedback history.
        """
        if user_id not in self.user_adjustments:
            return 1.0
        
        adjustments = self.user_adjustments[user_id]
        
        # Check company-specific boost
        company_key = f"company:{company}"
        if company_key in adjustments.ranking_boost:
            return adjustments.ranking_boost[company_key]
        
        # Check sector-specific boost
        sector_key = f"sector:{sector}"
        if sector_key in adjustments.ranking_boost:
            return adjustments.ranking_boost[sector_key]
        
        return 1.0

    def calculate_confidence_adjustment(self, user_id: int) -> float:
        """
        Calculate confidence score adjustment based on user's historical acceptance rate.
        """
        if user_id not in self.user_adjustments:
            return 1.0
        
        return self.user_adjustments[user_id].confidence_adjustment

    def calculate_priority_weights(self, user_id: int, strategy_type: str) -> float:
        """
        Calculate priority weight for a given strategy type.
        """
        if user_id not in self.user_adjustments:
            return 1.0
        
        adjustments = self.user_adjustments[user_id]
        return adjustments.priority_weights.get(strategy_type, 1.0)

    def update_user_adjustments(self, user_id: int, reward_signal: float, feedback_data: Dict[str, Any]) -> None:
        """
        Update RLHF adjustments based on new feedback and reward signal.
        
        Args:
            user_id: User identifier
            reward_signal: Calculated reward (-1.0 to 1.0)
            feedback_data: Feedback context including sector, company, strategy, etc.
        """
        if user_id not in self.user_adjustments:
            self.user_adjustments[user_id] = RLHFAdjustments()
        
        adjustments = self.user_adjustments[user_id]
        
        # Update ranking boost for sector/company
        sector = feedback_data.get('sector', '')
        company = feedback_data.get('company', '')
        
        if sector:
            sector_key = f"sector:{sector}"
            current_boost = adjustments.ranking_boost.get(sector_key, 1.0)
            # Positive reward increases boost, negative decreases
            adjustments.ranking_boost[sector_key] = max(0.5, min(2.0, current_boost + self.learning_rate * reward_signal))
        
        if company:
            company_key = f"company:{company}"
            current_boost = adjustments.ranking_boost.get(company_key, 1.0)
            adjustments.ranking_boost[company_key] = max(0.5, min(2.0, current_boost + self.learning_rate * reward_signal))
        
        # Update confidence adjustment based on overall acceptance rate
        acceptance_rate = self._calculate_acceptance_rate(user_id)
        adjustments.confidence_adjustment = 0.5 + (acceptance_rate * 0.5)  # Scale 0.5 to 1.0
        
        # Update priority weights for strategies
        strategy = feedback_data.get('strategy_type', 'balanced')
        current_weight = adjustments.priority_weights.get(strategy, 1.0)
        adjustments.priority_weights[strategy] = max(0.5, min(2.0, current_weight + self.learning_rate * reward_signal))
        
        logger.info(
            f"Updated RLHF adjustments for user {user_id}: "
            f"reward={reward_signal:.4f}, sector={sector}, company={company}"
        )

    def _calculate_acceptance_rate(self, user_id: int) -> float:
        """Calculate user's historical acceptance rate."""
        user_feedback = [f for f in self.feedback_history if f['user_id'] == user_id]
        if not user_feedback:
            return 0.5
        
        accepted = sum(1 for f in user_feedback if f.get('action') in ['ACCEPTED', 'FOLLOWED', 'READ'])
        return accepted / len(user_feedback)

    def get_user_adjustments(self, user_id: int) -> RLHFAdjustments:
        """
        Get current RLHF adjustments for a user.
        """
        if user_id not in self.user_adjustments:
            self.user_adjustments[user_id] = RLHFAdjustments()
        return self.user_adjustments[user_id]

    def get_global_adjustments(self) -> RLHFAdjustments:
        """
        Get global RLHF adjustments aggregated across all users.
        """
        if not self.user_adjustments:
            return self.global_adjustments
        
        # Aggregate adjustments from all users
        all_ranking_boosts = defaultdict(list)
        all_priority_weights = defaultdict(list)
        confidence_adjustments = []
        
        for adjustments in self.user_adjustments.values():
            for key, boost in adjustments.ranking_boost.items():
                all_ranking_boosts[key].append(boost)
            for strategy, weight in adjustments.priority_weights.items():
                all_priority_weights[strategy].append(weight)
            confidence_adjustments.append(adjustments.confidence_adjustment)
        
        # Calculate averages
        global_ranking_boost = {
            key: sum(values) / len(values) 
            for key, values in all_ranking_boosts.items()
        }
        global_priority_weights = {
            strategy: sum(weights) / len(weights)
            for strategy, weights in all_priority_weights.items()
        }
        global_confidence = sum(confidence_adjustments) / len(confidence_adjustments) if confidence_adjustments else 1.0
        
        return RLHFAdjustments(
            ranking_boost=global_ranking_boost,
            confidence_adjustment=global_confidence,
            priority_weights=global_priority_weights,
        )

    def export_adjustments(self, user_id: int) -> Dict[str, Any]:
        """
        Export RLHF adjustments for storage in database.
        """
        adjustments = self.get_user_adjustments(user_id)
        return {
            'user_id': user_id,
            'adjustments': adjustments.to_dict(),
            'feedback_count': len([f for f in self.feedback_history if f['user_id'] == user_id]),
        }

    def import_adjustments(self, adjustment_data: Dict[str, Any]) -> None:
        """
        Import RLHF adjustments from database.
        """
        user_id = adjustment_data['user_id']
        self.user_adjustments[user_id] = RLHFAdjustments.from_dict(adjustment_data['adjustments'])

    def apply_rlhf_to_recommendation(
        self,
        user_id: int,
        base_score: float,
        sector: str,
        company: str,
        strategy_type: str = 'balanced'
    ) -> Dict[str, Any]:
        """
        Apply RLHF adjustments to a base recommendation score.
        
        Returns:
            Dict with adjusted score and metadata
        """
        adjustments = self.get_user_adjustments(user_id)
        
        # Apply ranking boost
        ranking_boost = self.calculate_ranking_boost(user_id, sector, company)
        
        # Apply confidence adjustment
        confidence_adj = self.calculate_confidence_adjustment(user_id)
        
        # Apply priority weights
        priority_weight = self.calculate_priority_weights(user_id, strategy_type)
        
        # Calculate adjusted score
        adjusted_score = base_score * ranking_boost * confidence_adj * priority_weight
        adjusted_score = max(0.0, min(100.0, adjusted_score))
        
        return {
            'original_score': base_score,
            'adjusted_score': round(adjusted_score, 2),
            'ranking_boost': ranking_boost,
            'confidence_adjustment': confidence_adj,
            'priority_weight': priority_weight,
            'rlhf_applied': True,
        }


class AdaptiveLearningEngine:
    """
    Learns user preferences over time and updates user profiles.
    """

    def __init__(self, rlhf_trainer: RLHFTrainer = None):
        self.rlhf_trainer = rlhf_trainer or RLHFTrainer()

    def learn_preferences(self, user_id: int, feedback_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Learn user preferences from a batch of feedback.
        
        Returns:
            Updated preference profile
        """
        if not feedback_batch:
            return {}
        
        # Aggregate feedback
        sector_preferences = defaultdict(float)
        company_preferences = defaultdict(float)
        strategy_preferences = defaultdict(float)
        risk_preferences = []
        horizon_preferences = []
        
        for feedback in feedback_batch:
            reward = feedback.get('reward_signal', 0.0)
            sector = feedback.get('sector', '')
            company = feedback.get('company', '')
            strategy = feedback.get('strategy_type', 'balanced')
            risk = feedback.get('risk_profile', 'MODERATE')
            horizon = feedback.get('investment_horizon', '')
            
            # Update preferences based on reward
            if sector:
                sector_preferences[sector] += reward
            if company:
                company_preferences[company] += reward
            
            strategy_preferences[strategy] += reward
            
            if risk:
                risk_map = {'LOW': 1, 'MODERATE': 2, 'HIGH': 3}
                risk_preferences.append(risk_map.get(risk, 2))
            
            if horizon:
                horizon_preferences.append(horizon)
        
        # Calculate learned preferences
        preferred_sectors = sorted(sector_preferences.items(), key=lambda x: x[1], reverse=True)[:5]
        preferred_companies = sorted(company_preferences.items(), key=lambda x: x[1], reverse=True)[:10]
        preferred_strategy = max(strategy_preferences.items(), key=lambda x: x[1])[0] if strategy_preferences else 'balanced'
        
        avg_risk = sum(risk_preferences) / len(risk_preferences) if risk_preferences else 2
        risk_tolerance = ['LOW', 'MODERATE', 'HIGH'][int(avg_risk) - 1] if avg_risk in [1, 2, 3] else 'MODERATE'
        
        # Update RLHF trainer
        for feedback in feedback_batch:
            self.rlhf_trainer.record_feedback(user_id, feedback)
            if feedback.get('reward_signal') is not None:
                self.rlhf_trainer.update_user_adjustments(user_id, feedback['reward_signal'], feedback)
        
        return {
            'preferred_sectors': [s[0] for s in preferred_sectors],
            'preferred_companies': [c[0] for c in preferred_companies],
            'preferred_strategy': preferred_strategy,
            'risk_tolerance': risk_tolerance,
            'preferred_horizon': max(set(horizon_preferences), key=horizon_preferences.count) if horizon_preferences else '',
        }

    def get_learning_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Get insights about user's learning progress.
        """
        if user_id not in self.rlhf_trainer.user_adjustments:
            return {
                'total_feedback': 0,
                'learning_progress': 'INITIAL',
                'confidence_level': 'LOW',
            }
        
        user_feedback = [f for f in self.rlhf_trainer.feedback_history if f['user_id'] == user_id]
        total_feedback = len(user_feedback)
        
        if total_feedback < 10:
            learning_progress = 'INITIAL'
            confidence_level = 'LOW'
        elif total_feedback < 50:
            learning_progress = 'LEARNING'
            confidence_level = 'MEDIUM'
        else:
            learning_progress = 'MATURE'
            confidence_level = 'HIGH'
        
        adjustments = self.rlhf_trainer.get_user_adjustments(user_id)
        
        return {
            'total_feedback': total_feedback,
            'learning_progress': learning_progress,
            'confidence_level': confidence_level,
            'sectors_learned': len(adjustments.ranking_boost),
            'strategies_learned': len(adjustments.priority_weights),
            'confidence_score': adjustments.confidence_adjustment,
        }