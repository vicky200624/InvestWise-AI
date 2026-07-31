"""
Unit tests for InvestWise AI 3.0 standalone AI package.
Zero Django dependencies required to run these tests.
"""

import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from AI.learning.reward_model import RewardCalculator
from AI.training.backtesting import WalkForwardBacktester
from AI.rag.embeddings import EmbeddingManager
from AI.services.fundamentals import calculate_piotroski_score, calculate_altman_z_score
from AI.services.market_data import fetch_technical_indicators
from AI.services.news_sentiment import analyze_sentiment
from AI.agents.orchestrator import run_analysis


class TestAIEngine(unittest.TestCase):
    def test_reward_calculator_agree(self):
        reward = RewardCalculator.calculate_reward("AGREE", 70.0)
        self.assertEqual(reward, 0.5)

    def test_reward_calculator_disagree(self):
        reward = RewardCalculator.calculate_reward("DISAGREE", 70.0)
        self.assertEqual(reward, -0.5)

    def test_reward_calculator_outcome_bullish_profit(self):
        reward = RewardCalculator.calculate_reward("OUTCOME_EVAL", 75.0, actual_return_percent=5.0)
        self.assertGreater(reward, 0.0)
        self.assertEqual(reward, 0.5)

    def test_backtester_metrics(self):
        actuals = np.array([100, 105, 110, 108, 115])
        preds = np.array([101, 104, 111, 109, 114])
        metrics = WalkForwardBacktester.calculate_metrics(actuals, preds)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("max_drawdown", metrics)
        self.assertIn("win_rate", metrics)
        self.assertIn("mae", metrics)

    def test_embedding_manager_fallback(self):
        em = EmbeddingManager("stub_model")
        emb = em.embed_text("AAPL stock analysis")
        self.assertEqual(len(emb), 1)
        self.assertEqual(len(emb[0]), 384)

    def test_piotroski_score_calculation(self):
        current_year = {
            "netIncome": 100,
            "totalAssets": 1000,
            "operatingCashFlow": 150,
            "longTermDebt": 200,
            "currentRatio": 2.0,
            "weightedAverageShsOut": 1000,
            "grossProfit": 400,
            "revenue": 1000
        }
        prior_year = {
            "totalAssets": 1000,
            "longTermDebt": 250,
            "currentRatio": 1.5,
            "weightedAverageShsOut": 1000,
            "grossProfit": 350,
            "revenue": 900
        }
        score = calculate_piotroski_score(current_year, prior_year)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 9)
        self.assertEqual(score, 9)

    def test_altman_z_score_calculation(self):
        financials = {
            "totalAssets": 100000,
            "totalLiabilities": 40000,
            "totalCurrentAssets": 50000,
            "totalCurrentLiabilities": 20000,
            "retainedEarnings": 30000,
            "ebit": 15000,
            "marketCap": 80000,
            "revenue": 120000
        }
        z_score = calculate_altman_z_score(financials)
        self.assertGreater(z_score, 2.99)  # Safe zone

    @patch("AI.services.market_data.fetch_historical_prices")
    def test_technical_indicators(self, mock_fetch):
        # Create synthetic dataframe of 250 days
        dates = pd.date_range(start="2024-01-01", periods=250, freq="D")
        close_prices = np.linspace(100, 150, 250)
        high_prices = close_prices + 2.0
        low_prices = close_prices - 2.0
        df = pd.DataFrame({"Close": close_prices, "High": high_prices, "Low": low_prices}, index=dates)
        mock_fetch.return_value = df

        indicators = fetch_technical_indicators("RELIANCE.NS")
        self.assertIn("sma_50", indicators)
        self.assertIn("sma_200", indicators)
        self.assertIn("rsi_14", indicators)
        self.assertIn("macd", indicators)
        self.assertIn("bb_upper", indicators)
        self.assertIn("bb_middle", indicators)
        self.assertIn("bb_lower", indicators)
        self.assertIn("atr_14", indicators)
        self.assertIn("adx_14", indicators)
        self.assertIn("support_level", indicators)
        self.assertIn("resistance_level", indicators)

    def test_finbert_sentiment_fallback(self):
        texts = [
            "Company reports record quarterly growth and surging operating profit",
            "Warning: major lawsuit and severe debt decline lead to massive loss"
        ]
        results = analyze_sentiment(texts)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "positive")
        self.assertEqual(results[1]["label"], "negative")

    @patch("AI.services.fundamentals.fetch_income_statement")
    @patch("AI.services.fundamentals.fetch_balance_sheet")
    @patch("AI.services.fundamentals.fetch_cash_flow")
    @patch("AI.services.fundamentals.fetch_ratios")
    @patch("AI.services.fundamentals.fetch_company_profile")
    @patch("AI.services.market_data.fetch_technical_indicators")
    @patch("AI.services.news_sentiment.get_market_sentiment_score")
    @patch("AI.services.rag_engine.query_documents")
    def test_10_step_orchestrator_schema(
        self,
        mock_rag,
        mock_sentiment,
        mock_techs,
        mock_profile,
        mock_ratios,
        mock_cf,
        mock_bs,
        mock_inc,
    ):
        mock_inc.return_value = [{"revenue": 1000, "netIncome": 150}]
        mock_bs.return_value = [{"totalAssets": 5000, "totalStockholdersEquity": 2500}]
        mock_cf.return_value = [{"operatingCashFlow": 200, "freeCashFlow": 180}]
        mock_ratios.return_value = {"peRatio": 18.0}
        mock_profile.return_value = {"companyName": "Reliance Industries", "industry": "Energy"}
        mock_techs.return_value = {"rsi_14": 55.0, "macd": 1.2, "sma_50": 2500, "sma_200": 2400}
        mock_sentiment.return_value = {"aggregate_score": 0.4, "positive": 5, "negative": 1, "neutral": 2}
        mock_rag.return_value = []

        result = run_analysis("RELIANCE.NS", "LONG", 1, "task-uuid-1234")
        # Verify exact JSON schema keys per Part 2 spec
        self.assertIn("recommendation", result)
        self.assertIn("investment_score", result)
        self.assertIn("confidence", result)
        self.assertIn("expected_cagr", result)
        self.assertIn("risk_score", result)
        self.assertIn("bull_case", result)
        self.assertIn("base_case", result)
        self.assertIn("bear_case", result)
        self.assertIn("shap_explanation", result)
        self.assertIn("sources", result)
        self.assertIn("timestamp", result)
        self.assertIn("model_version", result)
        self.assertEqual(result["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
