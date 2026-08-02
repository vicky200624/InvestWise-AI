"""
Comprehensive tests for InvestWise AI Learning Engine.
Tests all major components: feedback, rewards, RLHF, memory, drift detection, etc.
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add AI directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AI'))

from learning.feedback_processor import FeedbackProcessor
from learning.enhanced_reward_model import EnhancedRewardCalculator, RewardComponents
from learning.rlhf import RLHFTrainer, AdaptiveLearningEngine, RLHFAdjustments
from learning.memory_systems import (
    ConversationMemoryManager,
    PortfolioMemoryManager,
    ResearchMemoryManager,
    MemoryConsolidator
)
from learning.watchlist_intelligence import (
    WatchlistIntelligence,
    WatchlistCategory,
    AutonomousMonitor
)
from learning.drift_detector import DriftDetector, DriftResult
from learning.explainability_engine import ExplainabilityEngine
from learning.learning_pipeline import LearningPipeline, PipelineConfig, LearningScheduler
from learning.audit_logger import AuditLogger, AuditActionType


class TestFeedbackProcessor(unittest.TestCase):
    """Test feedback processing."""

    def setUp(self):
        self.processor = FeedbackProcessor()

    def test_process_feedback_batch(self):
        """Test processing a batch of feedback."""
        feedback_records = [
            {"feedback_type": "HELPFUL", "predicted_score": 75.0, "actual_return_percent": 5.0},
            {"feedback_type": "UNHELPFUL", "predicted_score": 30.0, "actual_return_percent": -3.0},
            {"feedback_type": "HELPFUL", "predicted_score": 60.0},
        ]
        
        result = self.processor.process_feedback_batch(feedback_records)
        
        self.assertEqual(len(result), 3)
        self.assertIn('reward_signal', result[0])
        self.assertIn('sample_weight', result[0])
        self.assertGreater(result[0]['reward_signal'], 0)  # Positive feedback
        self.assertLess(result[1]['reward_signal'], 0)  # Negative feedback


class TestEnhancedRewardCalculator(unittest.TestCase):
    """Test enhanced reward calculation."""

    def setUp(self):
        self.calculator = EnhancedRewardCalculator()

    def test_calculate_enhanced_reward_positive(self):
        """Test positive reward calculation."""
        reward, components = self.calculator.calculate_enhanced_reward(
            feedback_type="AGREE",
            predicted_score=75.0,
            actual_return_percent=10.0,
            user_confidence_weight=1.0
        )
        
        self.assertGreater(reward, 0)
        self.assertIsInstance(components, RewardComponents)
        self.assertGreater(components.portfolio_return, 0)

    def test_calculate_enhanced_reward_negative(self):
        """Test negative reward calculation."""
        reward, components = self.calculator.calculate_enhanced_reward(
            feedback_type="DISAGREE",
            predicted_score=50.0,
            actual_return_percent=-5.0,
            user_confidence_weight=1.0
        )
        
        self.assertLess(reward, 0)
        self.assertLess(components.user_satisfaction, 0)

    def test_reward_components_weights(self):
        """Test that reward components are properly weighted."""
        reward, components = self.calculator.calculate_enhanced_reward(
            feedback_type="OUTCOME_EVAL",
            predicted_score=80.0,
            actual_return_percent=15.0,
            holding_duration_days=60,
            risk_before=0.7,
            risk_after=0.5
        )
        
        # Check all components are calculated
        self.assertNotEqual(components.recommendation_accuracy, 0.0)
        self.assertNotEqual(components.portfolio_return, 0.0)
        self.assertGreater(components.risk_reduction, 0)  # Risk decreased
        
        # Total should be in valid range
        self.assertGreaterEqual(reward, -1.0)
        self.assertLessEqual(reward, 1.0)


class TestRLHFTrainer(unittest.TestCase):
    """Test RLHF system."""

    def setUp(self):
        self.rlhf_trainer = RLHFTrainer()

    def test_record_feedback(self):
        """Test recording feedback."""
        feedback_data = {
            "feedback_type": "AGREE",
            "symbol": "AAPL",
            "sector": "Technology",
            "company": "Apple Inc.",
            "action": "ACCEPTED"
        }
        
        self.rlhf_trainer.record_feedback(user_id=1, feedback_data=feedback_data)
        
        user_feedback = [f for f in self.rlhf_trainer.feedback_history if f['user_id'] == 1]
        self.assertEqual(len(user_feedback), 1)

    def test_update_user_adjustments(self):
        """Test updating RLHF adjustments."""
        feedback_data = {
            "sector": "Technology",
            "company": "AAPL",
            "strategy_type": "growth"
        }
        
        self.rlhf_trainer.update_user_adjustments(
            user_id=1,
            reward_signal=0.8,
            feedback_data=feedback_data
        )
        
        adjustments = self.rlhf_trainer.get_user_adjustments(1)
        self.assertIsNotNone(adjustments)
        self.assertIn("sector:Technology", adjustments.ranking_boost)
        self.assertIn("company:AAPL", adjustments.ranking_boost)

    def test_apply_rlhf_to_recommendation(self):
        """Test applying RLHF adjustments to recommendations."""
        # First, create some positive feedback
        for _ in range(5):
            self.rlhf_trainer.update_user_adjustments(
                user_id=1,
                reward_signal=0.5,
                feedback_data={"sector": "Technology", "company": "AAPL", "strategy_type": "growth"}
            )
        
        result = self.rlhf_trainer.apply_rlhf_to_recommendation(
            user_id=1,
            base_score=70.0,
            sector="Technology",
            company="AAPL",
            strategy_type="growth"
        )
        
        self.assertIn('adjusted_score', result)
        self.assertIn('ranking_boost', result)
        self.assertGreater(result['ranking_boost'], 1.0)  # Should be boosted


class TestAdaptiveLearningEngine(unittest.TestCase):
    """Test adaptive learning engine."""

    def setUp(self):
        self.engine = AdaptiveLearningEngine()

    def test_learn_preferences(self):
        """Test learning user preferences."""
        feedback_batch = [
            {
                "reward_signal": 0.8,
                "sector": "Technology",
                "company": "AAPL",
                "strategy_type": "growth",
                "risk_profile": "MODERATE",
                "investment_horizon": "LONG"
            },
            {
                "reward_signal": 0.6,
                "sector": "Technology",
                "company": "MSFT",
                "strategy_type": "growth",
                "risk_profile": "MODERATE",
                "investment_horizon": "LONG"
            }
        ]
        
        preferences = self.engine.learn_preferences(user_id=1, feedback_batch=feedback_batch)
        
        self.assertIn('preferred_sectors', preferences)
        self.assertIn('preferred_companies', preferences)
        self.assertEqual(preferences['risk_tolerance'], 'MODERATE')

    def test_get_learning_insights(self):
        """Test getting learning insights."""
        insights = self.engine.get_learning_insights(user_id=1)
        
        self.assertIn('total_feedback', insights)
        self.assertIn('learning_progress', insights)
        self.assertIn('confidence_level', insights)


class TestMemorySystems(unittest.TestCase):
    """Test memory systems."""

    def test_conversation_memory_manager(self):
        """Test conversation memory management."""
        manager = ConversationMemoryManager()
        
        # Store memory
        memory = manager.store_memory(
            user_id=1,
            session_id="session123",
            memory_type="RESEARCH_TOPIC",
            entities=["AAPL", "Apple"],
            summary="User researched Apple stock",
            key_points=["Strong revenue growth", "Buy recommendation"],
            sentiment="POSITIVE"
        )
        
        self.assertIsNotNone(memory)
        self.assertEqual(memory['user_id'], 1)
        
        # Retrieve relevant memories
        relevant = manager.retrieve_relevant_memories(
            user_id=1,
            query_entities=["AAPL"],
            max_results=5
        )
        
        self.assertGreater(len(relevant), 0)

    def test_portfolio_memory_manager(self):
        """Test portfolio memory management."""
        manager = PortfolioMemoryManager()
        
        # Record portfolio snapshot
        holdings = [
            {"symbol": "AAPL", "qty": 10, "avg_price": 150.0, "current_value": 2000.0},
            {"symbol": "MSFT", "qty": 5, "avg_price": 300.0, "current_value": 1800.0}
        ]
        
        snapshot = manager.record_portfolio_snapshot(user_id=1, holdings=holdings)
        
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot['total_value'], 3800.0)
        
        # Get current portfolio
        current = manager.get_current_portfolio(user_id=1)
        self.assertIsNotNone(current)
        
        # Calculate metrics
        metrics = manager.calculate_portfolio_metrics(user_id=1)
        self.assertIn('total_value', metrics)
        self.assertIn('sector_allocation', metrics)

    def test_research_memory_manager(self):
        """Test research memory management."""
        manager = ResearchMemoryManager()
        
        # Record research activity
        activity = manager.record_research_activity(
            user_id=1,
            activity_type="COMPANY_ANALYZED",
            symbol="AAPL",
            company_name="Apple Inc.",
            query="Apple stock analysis",
            result_summary="Strong buy recommendation",
            session_id="session123"
        )
        
        self.assertIsNotNone(activity)
        
        # Get research history
        history = manager.get_research_history(user_id=1, symbol="AAPL")
        self.assertEqual(len(history), 1)
        
        # Get frequently researched
        frequent = manager.get_frequently_researched(user_id=1, top_n=5)
        self.assertIsInstance(frequent, list)


class TestWatchlistIntelligence(unittest.TestCase):
    """Test watchlist intelligence."""

    def setUp(self):
        self.watchlist_intel = WatchlistIntelligence()

    def test_create_intelligent_watchlist(self):
        """Test creating AI-generated watchlist."""
        result = self.watchlist_intel.create_intelligent_watchlist(
            user_id=1,
            watchlist_name="Value Opportunities",
            symbols=["AAPL", "MSFT", "GOOGL"],
            category=WatchlistCategory.WAITING_VALUATION
        )
        
        self.assertEqual(result['item_count'], 3)
        self.assertEqual(result['category'], "Waiting for Better Valuation")

    def test_categorize_stock(self):
        """Test intelligent stock categorization."""
        # Test valuation category
        stock_data = {"valuation_score": 0.9}
        category = self.watchlist_intel.categorize_stock(stock_data)
        self.assertEqual(category, WatchlistCategory.WAITING_VALUATION)
        
        # Test earnings category
        stock_data = {"days_to_earnings": 7}
        category = self.watchlist_intel.categorize_stock(stock_data)
        self.assertEqual(category, WatchlistCategory.WAITING_EARNINGS)
        
        # Test breakout category
        stock_data = {"technical_score": 0.8, "volume_trend": "increasing"}
        category = self.watchlist_intel.categorize_stock(stock_data)
        self.assertEqual(category, WatchlistCategory.WAITING_BREAKOUT)

    def test_monitor_watchlist(self):
        """Test watchlist monitoring."""
        # Create watchlist
        self.watchlist_intel.create_intelligent_watchlist(
            user_id=1,
            watchlist_name="Test Watchlist",
            symbols=["AAPL"],
            category=WatchlistCategory.WAITING_VALUATION
        )
        
        # Monitor with market data
        market_data = {
            "AAPL": {
                "price_change_percent": 0.12,
                "valuation_score": 0.9
            }
        }
        
        alerts = self.watchlist_intel.monitor_watchlist(
            user_id=1,
            watchlist_name="Test Watchlist",
            market_data=market_data
        )
        
        self.assertIsInstance(alerts, list)


class TestDriftDetector(unittest.TestCase):
    """Test drift detection."""

    def setUp(self):
        self.detector = DriftDetector()

    def test_set_reference_data(self):
        """Test setting reference data."""
        features = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100)
        })
        predictions = np.random.randn(100)
        metrics = {'accuracy': 0.85, 'precision': 0.83}
        
        self.detector.set_reference_data(features, predictions, metrics)
        
        self.assertIsNotNone(self.detector.reference_predictions)
        self.assertEqual(len(self.detector.reference_feature_distributions), 2)

    def test_detect_data_drift(self):
        """Test data drift detection."""
        # Set reference
        ref_features = pd.DataFrame({'feature1': np.random.randn(100)})
        self.detector.set_reference_data(ref_features, np.random.randn(100), {})
        
        # Test with similar data (no drift)
        current_features = pd.DataFrame({'feature1': np.random.randn(100)})
        results = self.detector.detect_data_drift(current_features)
        
        self.assertIsInstance(results, list)

    def test_detect_performance_drift(self):
        """Test performance drift detection."""
        self.detector.reference_performance = {'accuracy': 0.85, 'precision': 0.83}
        
        # Test with degraded performance
        current_metrics = {'accuracy': 0.75, 'precision': 0.73}
        results = self.detector.detect_performance_drift(current_metrics)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_comprehensive_drift_check(self):
        """Test comprehensive drift check."""
        # Setup reference
        ref_features = pd.DataFrame({'feature1': np.random.randn(100)})
        ref_preds = np.random.randn(100)
        self.detector.set_reference_data(ref_features, ref_preds, {'accuracy': 0.85})
        
        # Run comprehensive check
        current_features = pd.DataFrame({'feature1': np.random.randn(100)})
        current_preds = np.random.randn(100)
        current_actuals = np.random.randn(100)
        current_metrics = {'accuracy': 0.85}
        
        results = self.detector.comprehensive_drift_check(
            current_features, current_preds, current_actuals, current_metrics
        )
        
        self.assertIn('drift_detected', results)
        self.assertIn('results', results)
        self.assertIn('recommendation', results)


class TestExplainabilityEngine(unittest.TestCase):
    """Test explainability engine."""

    def setUp(self):
        self.engine = ExplainabilityEngine()

    def test_generate_explanation(self):
        """Test explanation generation."""
        explanation = self.engine.generate_explanation(
            symbol="AAPL",
            company_name="Apple Inc.",
            investment_score=85.0,
            confidence=0.9,
            shap_values={"revenue_growth": 0.3, "profit_margin": 0.2},
            fundamental_data={
                "revenue_growth": 0.18,
                "profit_margin": 0.22,
                "roe": 0.18,
                "debt_to_equity": 0.4,
                "free_cash_flow": 90e9
            },
            technical_data={
                "sma_20": 175.0,
                "sma_50": 170.0,
                "current_price": 180.0,
                "rsi": 55.0,
                "macd": 2.5,
                "macd_signal": 2.0
            },
            sentiment_data={},
            macro_data={"interest_rate": 4.5, "inflation": 3.0, "gdp_growth": 2.8},
            news_data=[],
            competitor_data={"market_share": 0.25, "advantages": ["Brand strength", "Ecosystem"]},
            risk_factors=["Market volatility", "Regulatory changes"],
            intrinsic_value={"dcf_value": 200.0, "current_price": 180.0}
        )
        
        self.assertIsNotNone(explanation)
        self.assertIn('components', explanation)
        self.assertIn('shap_explanation', explanation)
        self.assertIn('natural_language_summary', explanation)
        self.assertEqual(explanation['symbol'], 'AAPL')

    def test_generate_scenario_analysis(self):
        """Test scenario analysis generation."""
        scenarios = self.engine.generate_scenario_analysis(
            symbol="AAPL",
            company_name="Apple Inc.",
            current_price=180.0,
            intrinsic_value=200.0,
            volatility=0.25,
            time_horizon_days=365
        )
        
        self.assertIn('scenarios', scenarios)
        self.assertEqual(len(scenarios['scenarios']), 3)
        self.assertIn('expected_cagr', scenarios)
        self.assertIn('risk', scenarios)

    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        confidence = self.engine.calculate_confidence_score(
            model_agreement=0.8,
            data_completeness=0.9,
            prediction_stability=0.75,
            market_volatility=0.3,
            historical_accuracy=0.85
        )
        
        self.assertIn('confidence_score', confidence)
        self.assertIn('confidence_level', confidence)
        self.assertGreaterEqual(confidence['confidence_score'], 0.0)
        self.assertLessEqual(confidence['confidence_score'], 1.0)


class TestLearningPipeline(unittest.TestCase):
    """Test learning pipeline."""

    def setUp(self):
        config = PipelineConfig(
            feedback_batch_size=10,
            retrain_frequency_days=7,
            min_feedback_for_retrain=5
        )
        self.pipeline = LearningPipeline(config)

    def test_stage_recommendation(self):
        """Test recommendation generation."""
        recommendation_data = {
            "recommendation_id": "rec123",
            "user_id": 1,
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "base_score": 75.0,
            "sector": "Technology",
            "company": "Apple Inc.",
            "strategy_type": "growth"
        }
        
        result = self.pipeline.stage_recommendation(recommendation_data)
        
        self.assertEqual(result['stage'], 'RECOMMENDATION')
        self.assertIn('adjusted_score', result)
        self.assertIn('explanation', result)

    def test_stage_user_decision(self):
        """Test capturing user decision."""
        feedback_data = {
            "user_id": 1,
            "symbol": "AAPL",
            "action": "ACCEPTED",
            "feedback_type": "BUY_ACCEPTED"
        }
        
        result = self.pipeline.stage_user_decision(feedback_data)
        
        self.assertEqual(result['stage'], 'USER_DECISION')
        self.assertEqual(len(self.pipeline.feedback_queue), 1)

    def test_process_feedback_batch(self):
        """Test processing feedback batch."""
        # Add some feedback
        for i in range(5):
            self.pipeline.stage_user_decision({
                "user_id": 1,
                "symbol": f"STOCK{i}",
                "action": "ACCEPTED",
                "feedback_type": "BUY_ACCEPTED"
            })
        
        result = self.pipeline.process_feedback_batch()
        
        self.assertEqual(result['processed'], 5)
        self.assertEqual(self.pipeline.total_feedback_processed, 5)

    def test_should_retrain(self):
        """Test retrain decision logic."""
        # Initially should retrain (no previous retrain)
        self.assertTrue(self.pipeline.should_retrain())
        
        # Set last retrain date
        self.pipeline.last_retrain_date = datetime.utcnow()
        self.assertFalse(self.pipeline.should_retrain())


class TestLearningScheduler(unittest.TestCase):
    """Test learning scheduler."""

    def setUp(self):
        self.pipeline = LearningPipeline()
        self.scheduler = LearningScheduler(self.pipeline)

    def test_get_daily_tasks(self):
        """Test getting daily tasks."""
        tasks = self.scheduler.get_daily_tasks()
        
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)
        self.assertEqual(tasks[0]['frequency'], 'DAILY')

    def test_get_weekly_tasks(self):
        """Test getting weekly tasks."""
        tasks = self.scheduler.get_weekly_tasks()
        
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)
        self.assertEqual(tasks[0]['frequency'], 'WEEKLY')

    def test_get_monthly_tasks(self):
        """Test getting monthly tasks."""
        tasks = self.scheduler.get_monthly_tasks()
        
        self.assertIsInstance(tasks, list)
        self.assertGreater(len(tasks), 0)
        self.assertEqual(tasks[0]['frequency'], 'MONTHLY')

    def test_get_all_scheduled_tasks(self):
        """Test getting all scheduled tasks."""
        all_tasks = self.scheduler.get_all_scheduled_tasks()
        
        self.assertIsInstance(all_tasks, list)
        self.assertGreater(len(all_tasks), 0)
        
        # Check all frequencies are present
        frequencies = [task['frequency'] for task in all_tasks]
        self.assertIn('DAILY', frequencies)
        self.assertIn('WEEKLY', frequencies)
        self.assertIn('MONTHLY', frequencies)
        self.assertIn('QUARTERLY', frequencies)


class TestAuditLogger(unittest.TestCase):
    """Test audit logging."""

    def setUp(self):
        self.logger = AuditLogger(max_entries=1000)

    def test_log_prediction(self):
        """Test logging prediction."""
        entry = self.logger.log_prediction(
            model_version="v1.0",
            symbol="AAPL",
            prediction_data={"score": 75.0, "type": "investment"},
            user_id=1
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.action_type, AuditActionType.PREDICTION)
        self.assertEqual(len(self.logger.audit_log), 1)

    def test_log_recommendation(self):
        """Test logging recommendation."""
        entry = self.logger.log_recommendation(
            model_version="v1.0",
            symbol="AAPL",
            recommendation_data={"score": 85.0, "confidence": 0.9},
            user_id=1
        )
        
        self.assertEqual(entry.action_type, AuditActionType.RECOMMENDATION)

    def test_log_feedback(self):
        """Test logging feedback."""
        entry = self.logger.log_feedback(
            model_version="v1.0",
            symbol="AAPL",
            feedback_data={"action": "ACCEPTED", "reward_signal": 0.8},
            user_id=1
        )
        
        self.assertEqual(entry.action_type, AuditActionType.FEEDBACK_RECEIVED)

    def test_get_audit_trail(self):
        """Test querying audit trail."""
        # Add some entries
        self.logger.log_prediction("v1.0", "AAPL", {}, user_id=1)
        self.logger.log_recommendation("v1.0", "MSFT", {}, user_id=1)
        self.logger.log_feedback("v1.0", "AAPL", {}, user_id=1)
        
        # Query by user
        trail = self.logger.get_audit_trail(user_id=1)
        self.assertEqual(len(trail), 3)
        
        # Query by symbol
        trail = self.logger.get_audit_trail(symbol="AAPL")
        self.assertEqual(len(trail), 2)
        
        # Query by action type
        trail = self.logger.get_audit_trail(action_type=AuditActionType.FEEDBACK_RECEIVED)
        self.assertEqual(len(trail), 1)

    def test_get_audit_statistics(self):
        """Test getting audit statistics."""
        # Add some entries
        for i in range(10):
            self.logger.log_prediction("v1.0", f"STOCK{i}", {}, user_id=1)
        
        stats = self.logger.get_audit_statistics()
        
        self.assertEqual(stats['total_entries'], 10)
        self.assertIn('action_type_distribution', stats)
        self.assertIn('model_version_distribution', stats)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete learning engine."""

    def test_complete_learning_workflow(self):
        """Test complete workflow from recommendation to learning."""
        pipeline = LearningPipeline()
        
        # Stage 1: Generate recommendation
        recommendation = pipeline.stage_recommendation({
            "recommendation_id": "rec001",
            "user_id": 1,
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "base_score": 75.0,
            "sector": "Technology",
            "company": "Apple Inc.",
            "strategy_type": "growth"
        })
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation['stage'], 'RECOMMENDATION')
        
        # Stage 2: User accepts recommendation
        feedback = pipeline.stage_user_decision({
            "user_id": 1,
            "symbol": "AAPL",
            "action": "ACCEPTED",
            "feedback_type": "BUY_ACCEPTED",
            "recommendation_id": "rec001"
        })
        
        self.assertEqual(feedback['stage'], 'USER_DECISION')
        
        # Stage 3: Store feedback
        stored = pipeline.stage_store_feedback(feedback)
        self.assertTrue(stored.get('stored', False))
        
        # Stage 4: Evaluate result (simulate positive return)
        evaluation = pipeline.stage_evaluate_result({
            "symbol": "AAPL",
            "price_before": 150.0,
            "price_after": 165.0
        })
        
        self.assertIn('actual_return_percent', evaluation)
        self.assertGreater(evaluation['actual_return_percent'], 0)
        
        # Stage 5: Calculate reward
        reward_data = pipeline.stage_reward_calculation({
            "user_id": 1,
            "symbol": "AAPL",
            "feedback_type": "BUY_ACCEPTED",
            "predicted_score": 75.0,
            "actual_return_percent": 10.0
        })
        
        self.assertIn('reward_signal', reward_data)
        self.assertGreater(reward_data['reward_signal'], 0)
        
        # Process batch
        result = pipeline.process_feedback_batch()
        self.assertGreater(result['processed'], 0)


if __name__ == '__main__':
    unittest.main()