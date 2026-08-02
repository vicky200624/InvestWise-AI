"""
Model Drift Detection for InvestWise AI Learning Engine.
Detects data drift, concept drift, feature drift, performance drift, and prediction drift.
Standalone module with zero Django dependencies.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DriftResult:
    """Result of drift detection analysis."""
    drift_type: str
    drift_score: float
    threshold: float
    drift_detected: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    details: Dict[str, Any]
    detected_at: str


class DriftDetector:
    """
    Detects various types of model drift in production.
    """

    def __init__(
        self,
        data_drift_threshold: float = 0.15,
        concept_drift_threshold: float = 0.20,
        performance_drift_threshold: float = 0.10,
        prediction_drift_threshold: float = 0.15,
    ):
        self.data_drift_threshold = data_drift_threshold
        self.concept_drift_threshold = concept_drift_threshold
        self.performance_drift_threshold = performance_drift_threshold
        self.prediction_drift_threshold = prediction_drift_threshold
        
        # Store reference distributions
        self.reference_feature_distributions: Dict[str, np.ndarray] = {}
        self.reference_predictions: Optional[np.ndarray] = None
        self.reference_performance: Dict[str, float] = {}

    def set_reference_data(
        self,
        features: pd.DataFrame,
        predictions: np.ndarray,
        performance_metrics: Dict[str, float]
    ) -> None:
        """
        Set reference (training) data distributions for comparison.
        """
        # Store feature distributions
        for column in features.columns:
            self.reference_feature_distributions[column] = features[column].dropna().values
        
        # Store reference predictions
        self.reference_predictions = predictions
        
        # Store reference performance
        self.reference_performance = performance_metrics
        
        logger.info(f"Set reference data: {len(features.columns)} features, {len(predictions)} predictions")

    def detect_data_drift(
        self,
        current_features: pd.DataFrame,
        feature_names: List[str] = None
    ) -> List[DriftResult]:
        """
        Detect data drift by comparing feature distributions.
        Uses Kolmogorov-Smirnov test for numerical features.
        """
        results = []
        features_to_check = feature_names or list(current_features.columns)
        
        for feature_name in features_to_check:
            if feature_name not in self.reference_feature_distributions:
                continue
            
            if feature_name not in current_features.columns:
                continue
            
            reference_dist = self.reference_feature_distributions[feature_name]
            current_dist = current_features[feature_name].dropna().values
            
            if len(current_dist) < 10:
                continue
            
            # Perform KS test
            try:
                statistic, p_value = stats.ks_2samp(reference_dist, current_dist)
                drift_score = float(statistic)
                drift_detected = drift_score > self.data_drift_threshold
                
                severity = self._calculate_severity(drift_score, self.data_drift_threshold)
                
                result = DriftResult(
                    drift_type='DATA_DRIFT',
                    drift_score=drift_score,
                    threshold=self.data_drift_threshold,
                    drift_detected=drift_detected,
                    severity=severity,
                    details={
                        'feature': feature_name,
                        'p_value': float(p_value),
                        'reference_mean': float(np.mean(reference_dist)),
                        'current_mean': float(np.mean(current_dist)),
                        'reference_std': float(np.std(reference_dist)),
                        'current_std': float(np.std(current_dist)),
                    },
                    detected_at=datetime.utcnow().isoformat()
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error detecting drift for feature {feature_name}: {e}")
        
        return results

    def detect_concept_drift(
        self,
        current_predictions: np.ndarray,
        current_actuals: np.ndarray
    ) -> DriftResult:
        """
        Detect concept drift by comparing prediction-error distributions.
        """
        if self.reference_predictions is None:
            return DriftResult(
                drift_type='CONCEPT_DRIFT',
                drift_score=0.0,
                threshold=self.concept_drift_threshold,
                drift_detected=False,
                severity='LOW',
                details={'error': 'No reference predictions set'},
                detected_at=datetime.utcnow().isoformat()
            )
        
        # Calculate error distributions
        reference_errors = np.abs(self.reference_predictions - current_actuals[:len(self.reference_predictions)])
        current_errors = np.abs(current_predictions - current_actuals)
        
        if len(current_errors) < 10:
            return DriftResult(
                drift_type='CONCEPT_DRIFT',
                drift_score=0.0,
                threshold=self.concept_drift_threshold,
                drift_detected=False,
                severity='LOW',
                details={'error': 'Insufficient current data'},
                detected_at=datetime.utcnow().isoformat()
            )
        
        # Compare error distributions
        try:
            statistic, p_value = stats.ks_2samp(reference_errors, current_errors)
            drift_score = float(statistic)
            drift_detected = drift_score > self.concept_drift_threshold
            
            severity = self._calculate_severity(drift_score, self.concept_drift_threshold)
            
            return DriftResult(
                drift_type='CONCEPT_DRIFT',
                drift_score=drift_score,
                threshold=self.concept_drift_threshold,
                drift_detected=drift_detected,
                severity=severity,
                details={
                    'p_value': float(p_value),
                    'reference_mean_error': float(np.mean(reference_errors)),
                    'current_mean_error': float(np.mean(current_errors)),
                    'error_increase': float(np.mean(current_errors) - np.mean(reference_errors)),
                },
                detected_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error detecting concept drift: {e}")
            return DriftResult(
                drift_type='CONCEPT_DRIFT',
                drift_score=0.0,
                threshold=self.concept_drift_threshold,
                drift_detected=False,
                severity='LOW',
                details={'error': str(e)},
                detected_at=datetime.utcnow().isoformat()
            )

    def detect_performance_drift(
        self,
        current_metrics: Dict[str, float]
    ) -> List[DriftResult]:
        """
        Detect performance drift by comparing current metrics to reference.
        """
        results = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name not in self.reference_performance:
                continue
            
            reference_value = self.reference_performance[metric_name]
            
            # Calculate relative change
            if reference_value != 0:
                relative_change = abs(current_value - reference_value) / abs(reference_value)
            else:
                relative_change = abs(current_value)
            
            drift_detected = relative_change > self.performance_drift_threshold
            severity = self._calculate_severity(relative_change, self.performance_drift_threshold)
            
            result = DriftResult(
                drift_type='PERFORMANCE_DRIFT',
                drift_score=relative_change,
                threshold=self.performance_drift_threshold,
                drift_detected=drift_detected,
                severity=severity,
                details={
                    'metric': metric_name,
                    'reference_value': reference_value,
                    'current_value': current_value,
                    'absolute_change': current_value - reference_value,
                    'relative_change': relative_change,
                },
                detected_at=datetime.utcnow().isoformat()
            )
            results.append(result)
        
        return results

    def detect_prediction_drift(
        self,
        current_predictions: np.ndarray
    ) -> DriftResult:
        """
        Detect prediction drift by comparing prediction distributions.
        """
        if self.reference_predictions is None or len(self.reference_predictions) == 0:
            return DriftResult(
                drift_type='PREDICTION_DRIFT',
                drift_score=0.0,
                threshold=self.prediction_drift_threshold,
                drift_detected=False,
                severity='LOW',
                details={'error': 'No reference predictions set'},
                detected_at=datetime.utcnow().isoformat()
            )
        
        try:
            # Compare prediction distributions
            statistic, p_value = stats.ks_2samp(self.reference_predictions, current_predictions)
            drift_score = float(statistic)
            drift_detected = drift_score > self.prediction_drift_threshold
            
            severity = self._calculate_severity(drift_score, self.prediction_drift_threshold)
            
            return DriftResult(
                drift_type='PREDICTION_DRIFT',
                drift_score=drift_score,
                threshold=self.prediction_drift_threshold,
                drift_detected=drift_detected,
                severity=severity,
                details={
                    'p_value': float(p_value),
                    'reference_mean': float(np.mean(self.reference_predictions)),
                    'current_mean': float(np.mean(current_predictions)),
                    'reference_std': float(np.std(self.reference_predictions)),
                    'current_std': float(np.std(current_predictions)),
                },
                detected_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error detecting prediction drift: {e}")
            return DriftResult(
                drift_type='PREDICTION_DRIFT',
                drift_score=0.0,
                threshold=self.prediction_drift_threshold,
                drift_detected=False,
                severity='LOW',
                details={'error': str(e)},
                detected_at=datetime.utcnow().isoformat()
            )

    def comprehensive_drift_check(
        self,
        current_features: pd.DataFrame,
        current_predictions: np.ndarray,
        current_actuals: np.ndarray,
        current_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Run all drift detection checks.
        """
        all_results = []
        
        # Data drift
        data_drift_results = self.detect_data_drift(current_features)
        all_results.extend(data_drift_results)
        
        # Concept drift
        concept_drift = self.detect_concept_drift(current_predictions, current_actuals)
        all_results.append(concept_drift)
        
        # Performance drift
        performance_drift_results = self.detect_performance_drift(current_metrics)
        all_results.extend(performance_drift_results)
        
        # Prediction drift
        prediction_drift = self.detect_prediction_drift(current_predictions)
        all_results.append(prediction_drift)
        
        # Summarize results
        drift_detected = any(r.drift_detected for r in all_results)
        critical_drifts = [r for r in all_results if r.severity == 'CRITICAL']
        high_drifts = [r for r in all_results if r.severity == 'HIGH']
        
        summary = {
            'drift_detected': drift_detected,
            'total_checks': len(all_results),
            'drifts_found': sum(1 for r in all_results if r.drift_detected),
            'critical_count': len(critical_drifts),
            'high_count': len(high_drifts),
            'overall_severity': self._determine_overall_severity(all_results),
            'results': [
                {
                    'type': r.drift_type,
                    'score': r.drift_score,
                    'detected': r.drift_detected,
                    'severity': r.severity,
                    'details': r.details,
                }
                for r in all_results
            ],
            'recommendation': self._generate_recommendation(all_results),
        }
        
        if drift_detected:
            logger.warning(
                f"Drift detected: {summary['drifts_found']}/{summary['total_checks']} checks failed. "
                f"Severity: {summary['overall_severity']}"
            )
        
        return summary

    def _calculate_severity(self, drift_score: float, threshold: float) -> str:
        """Calculate severity level based on drift score."""
        if drift_score >= threshold * 2.0:
            return 'CRITICAL'
        elif drift_score >= threshold * 1.5:
            return 'HIGH'
        elif drift_score >= threshold:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _determine_overall_severity(self, results: List[DriftResult]) -> str:
        """Determine overall severity from all results."""
        severity_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        max_severity = 'LOW'
        
        for result in results:
            if result.drift_detected:
                current_idx = severity_order.index(result.severity)
                max_idx = severity_order.index(max_severity)
                if current_idx > max_idx:
                    max_severity = result.severity
        
        return max_severity

    def _generate_recommendation(self, results: List[DriftResult]) -> str:
        """Generate recommendation based on drift results."""
        critical_count = sum(1 for r in results if r.severity == 'CRITICAL')
        high_count = sum(1 for r in results if r.severity == 'HIGH')
        
        if critical_count > 0:
            return "IMMEDIATE_ACTION: Critical drift detected. Flag model and initiate retraining."
        elif high_count > 0:
            return "URGENT_REVIEW: High drift detected. Schedule candidate model training."
        elif any(r.drift_detected for r in results):
            return "MONITOR: Drift detected. Continue monitoring and prepare for retraining."
        else:
            return "HEALTHY: No significant drift detected. Continue monitoring."