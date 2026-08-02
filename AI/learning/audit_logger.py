"""
Audit Logging for InvestWise AI Learning Engine.
Comprehensive audit trail for all model changes and decisions.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AuditActionType(Enum):
    PREDICTION = "PREDICTION"
    RECOMMENDATION = "RECOMMENDATION"
    EXPLANATION = "EXPLANATION"
    FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED"
    MODEL_TRAINED = "MODEL_TRAINED"
    MODEL_DEPLOYED = "MODEL_DEPLOYED"
    MODEL_ARCHIVED = "MODEL_ARCHIVED"
    DRIFT_DETECTED = "DRIFT_DETECTED"
    CANDIDATE_CREATED = "CANDIDATE_CREATED"
    REWARD_CALCULATED = "REWARD_CALCULATED"
    RLHF_UPDATED = "RLHF_UPDATED"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    model_version: str
    action_type: AuditActionType
    timestamp: str
    symbol: str = ''
    user_id: Optional[int] = None
    prediction: Dict[str, Any] = field(default_factory=dict)
    recommendation: Dict[str, Any] = field(default_factory=dict)
    explanation: Dict[str, Any] = field(default_factory=dict)
    user_feedback: Dict[str, Any] = field(default_factory=dict)
    deployment_date: Optional[str] = None
    training_dataset: str = ''
    git_commit: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """
    Comprehensive audit logging for all model changes and decisions.
    Ensures full traceability and compliance.
    """

    def __init__(self, max_entries: int = 100000):
        self.audit_log: List[AuditEntry] = []
        self.max_entries = max_entries
        self.user_sessions: Dict[int, List[str]] = {}  # user_id -> list of session_ids

    def log_prediction(
        self,
        model_version: str,
        symbol: str,
        prediction_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> AuditEntry:
        """
        Log a model prediction.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.PREDICTION,
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            user_id=user_id,
            prediction=prediction_data,
            metadata={'prediction_type': prediction_data.get('type', 'unknown')}
        )
        
        self._add_entry(entry)
        logger.debug(f"Logged prediction for {symbol} using model {model_version}")
        return entry

    def log_recommendation(
        self,
        model_version: str,
        symbol: str,
        recommendation_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> AuditEntry:
        """
        Log a recommendation generated for user.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.RECOMMENDATION,
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            user_id=user_id,
            recommendation=recommendation_data,
            metadata={
                'score': recommendation_data.get('score'),
                'confidence': recommendation_data.get('confidence'),
                'rlhf_applied': recommendation_data.get('rlhf_applied', False)
            }
        )
        
        self._add_entry(entry)
        logger.info(f"Logged recommendation for {symbol}: {recommendation_data.get('score')}/100")
        return entry

    def log_explanation(
        self,
        model_version: str,
        symbol: str,
        explanation_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> AuditEntry:
        """
        Log an explanation generated for a recommendation.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.EXPLANATION,
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            user_id=user_id,
            explanation=explanation_data,
            metadata={
                'explanation_type': explanation_data.get('type', 'full'),
                'shap_generated': bool(explanation_data.get('shap_values'))
            }
        )
        
        self._add_entry(entry)
        logger.debug(f"Logged explanation for {symbol}")
        return entry

    def log_feedback(
        self,
        model_version: str,
        symbol: str,
        feedback_data: Dict[str, Any],
        user_id: int
    ) -> AuditEntry:
        """
        Log user feedback received.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.FEEDBACK_RECEIVED,
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            user_id=user_id,
            user_feedback=feedback_data,
            metadata={
                'feedback_type': feedback_data.get('feedback_type'),
                'action': feedback_data.get('action'),
                'reward_signal': feedback_data.get('reward_signal')
            }
        )
        
        self._add_entry(entry)
        logger.info(f"Logged feedback from user {user_id} for {symbol}: {feedback_data.get('action')}")
        return entry

    def log_model_trained(
        self,
        model_version: str,
        training_data: Dict[str, Any],
        metrics: Dict[str, float],
        git_commit: str = ''
    ) -> AuditEntry:
        """
        Log model training event.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.MODEL_TRAINED,
            timestamp=datetime.utcnow().isoformat(),
            training_dataset=training_data.get('dataset_version', ''),
            git_commit=git_commit,
            metadata={
                'training_samples': training_data.get('sample_count', 0),
                'training_duration_seconds': training_data.get('duration_seconds', 0),
                'metrics': metrics
            }
        )
        
        self._add_entry(entry)
        logger.info(f"Logged model training: {model_version}")
        return entry

    def log_model_deployed(
        self,
        model_version: str,
        deployed_by: str,
        previous_version: str = '',
        deployment_notes: str = ''
    ) -> AuditEntry:
        """
        Log model deployment to production.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.MODEL_DEPLOYED,
            timestamp=datetime.utcnow().isoformat(),
            deployment_date=datetime.utcnow().isoformat(),
            metadata={
                'deployed_by': deployed_by,
                'previous_version': previous_version,
                'deployment_notes': deployment_notes
            }
        )
        
        self._add_entry(entry)
        logger.info(f"Logged model deployment: {model_version} (by {deployed_by})")
        return entry

    def log_model_archived(
        self,
        model_version: str,
        reason: str = ''
    ) -> AuditEntry:
        """
        Log model archival.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.MODEL_ARCHIVED,
            timestamp=datetime.utcnow().isoformat(),
            metadata={'reason': reason}
        )
        
        self._add_entry(entry)
        logger.info(f"Logged model archival: {model_version}")
        return entry

    def log_drift_detected(
        self,
        model_version: str,
        drift_results: Dict[str, Any]
    ) -> AuditEntry:
        """
        Log drift detection event.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.DRIFT_DETECTED,
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                'drift_detected': drift_results.get('drift_detected', False),
                'overall_severity': drift_results.get('overall_severity', 'LOW'),
                'drifts_found': drift_results.get('drifts_found', 0),
                'recommendation': drift_results.get('recommendation', ''),
                'results': drift_results.get('results', [])[:5]  # Top 5 results
            }
        )
        
        self._add_entry(entry)
        if drift_results.get('drift_detected'):
            logger.warning(f"Logged drift detection for {model_version}: {drift_results.get('overall_severity')}")
        return entry

    def log_candidate_created(
        self,
        candidate_version: str,
        training_data: Dict[str, Any],
        parent_model: str
    ) -> AuditEntry:
        """
        Log candidate model creation.
        """
        entry = AuditEntry(
            model_version=candidate_version,
            action_type=AuditActionType.CANDIDATE_CREATED,
            timestamp=datetime.utcnow().isoformat(),
            training_dataset=training_data.get('dataset_version', ''),
            metadata={
                'parent_model': parent_model,
                'training_samples': training_data.get('sample_count', 0),
                'status': 'Candidate'
            }
        )
        
        self._add_entry(entry)
        logger.info(f"Logged candidate model creation: {candidate_version}")
        return entry

    def log_reward_calculated(
        self,
        model_version: str,
        symbol: str,
        reward_data: Dict[str, Any],
        user_id: int
    ) -> AuditEntry:
        """
        Log reward calculation for feedback.
        """
        entry = AuditEntry(
            model_version=model_version,
            action_type=AuditActionType.REWARD_CALCULATED,
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol,
            user_id=user_id,
            metadata={
                'reward_signal': reward_data.get('reward_signal'),
                'reward_components': reward_data.get('reward_components', {}),
                'feedback_type': reward_data.get('feedback_type')
            }
        )
        
        self._add_entry(entry)
        logger.debug(f"Logged reward calculation for user {user_id}, symbol {symbol}")
        return entry

    def log_rlhf_updated(
        self,
        user_id: int,
        rlhf_data: Dict[str, Any]
    ) -> AuditEntry:
        """
        Log RLHF adjustment update.
        """
        entry = AuditEntry(
            model_version='RLHF',
            action_type=AuditActionType.RLHF_UPDATED,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            metadata={
                'user_id': user_id,
                'ranking_boost_count': len(rlhf_data.get('ranking_boost', {})),
                'confidence_adjustment': rlhf_data.get('confidence_adjustment'),
                'priority_weights_count': len(rlhf_data.get('priority_weights', {}))
            }
        )
        
        self._add_entry(entry)
        logger.debug(f"Logged RLHF update for user {user_id}")
        return entry

    def _add_entry(self, entry: AuditEntry) -> None:
        """Add entry to audit log with size management."""
        self.audit_log.append(entry)
        
        # Enforce size limit
        if len(self.audit_log) > self.max_entries:
            self.audit_log = self.audit_log[-self.max_entries:]

    def get_audit_trail(
        self,
        model_version: str = None,
        user_id: int = None,
        action_type: AuditActionType = None,
        symbol: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit log with filters.
        """
        filtered = self.audit_log
        
        if model_version:
            filtered = [e for e in filtered if e.model_version == model_version]
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        if action_type:
            filtered = [e for e in filtered if e.action_type == action_type]
        if symbol:
            filtered = [e for e in filtered if e.symbol == symbol]
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        # Sort by timestamp descending
        filtered = sorted(filtered, key=lambda x: x.timestamp, reverse=True)
        
        return [self._entry_to_dict(e) for e in filtered[:limit]]

    def get_model_audit_trail(self, model_version: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit trail for a specific model version."""
        return self.get_audit_trail(model_version=model_version, limit=limit)

    def get_user_audit_trail(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit trail for a specific user."""
        return self.get_audit_trail(user_id=user_id, limit=limit)

    def get_symbol_audit_trail(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit trail for a specific symbol."""
        return self.get_audit_trail(symbol=symbol, limit=limit)

    def export_audit_log(
        self,
        start_date: str = None,
        end_date: str = None,
        format: str = 'json'
    ) -> str:
        """
        Export audit log for compliance/backup.
        """
        entries = self.get_audit_trail(start_date=start_date, end_date=end_date, limit=self.max_entries)
        
        if format == 'json':
            return json.dumps(entries, indent=2)
        elif format == 'csv':
            # Simple CSV format
            if not entries:
                return ''
            
            headers = ['timestamp', 'model_version', 'action_type', 'symbol', 'user_id']
            lines = [','.join(headers)]
            
            for entry in entries:
                line = ','.join([
                    entry.get('timestamp', ''),
                    entry.get('model_version', ''),
                    entry.get('action_type', ''),
                    entry.get('symbol', ''),
                    str(entry.get('user_id', ''))
                ])
                lines.append(line)
            
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_audit_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics.
        """
        if not self.audit_log:
            return {
                'total_entries': 0,
                'date_range': {'start': None, 'end': None}
            }
        
        # Count by action type
        action_counts = {}
        for entry in self.audit_log:
            action_type = entry.action_type.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        # Count by model version
        model_counts = {}
        for entry in self.audit_log:
            model = entry.model_version
            model_counts[model] = model_counts.get(model, 0) + 1
        
        # Date range
        timestamps = [e.timestamp for e in self.audit_log]
        
        return {
            'total_entries': len(self.audit_log),
            'date_range': {
                'start': min(timestamps),
                'end': max(timestamps)
            },
            'action_type_distribution': action_counts,
            'model_version_distribution': model_counts,
            'unique_users': len(set(e.user_id for e in self.audit_log if e.user_id)),
            'unique_symbols': len(set(e.symbol for e in self.audit_log if e.symbol))
        }

    def _entry_to_dict(self, entry: AuditEntry) -> Dict[str, Any]:
        """Convert AuditEntry to dictionary."""
        return {
            'model_version': entry.model_version,
            'action_type': entry.action_type.value,
            'timestamp': entry.timestamp,
            'symbol': entry.symbol,
            'user_id': entry.user_id,
            'prediction': entry.prediction,
            'recommendation': entry.recommendation,
            'explanation': entry.explanation,
            'user_feedback': entry.user_feedback,
            'deployment_date': entry.deployment_date,
            'training_dataset': entry.training_dataset,
            'git_commit': entry.git_commit,
            'metadata': entry.metadata
        }

    def clear_old_entries(self, days_to_keep: int = 365) -> int:
        """
        Clear audit entries older than specified days.
        Returns number of entries cleared.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()
        
        original_count = len(self.audit_log)
        self.audit_log = [e for e in self.audit_log if e.timestamp >= cutoff_str]
        cleared_count = original_count - len(self.audit_log)
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} old audit entries (older than {days_to_keep} days)")
        
        return cleared_count