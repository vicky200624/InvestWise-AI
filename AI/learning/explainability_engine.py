"""
Explainability Engine for InvestWise AI Learning Engine.
Generates comprehensive explanations for all recommendations.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ExplanationComponents:
    """Breakdown of explanation components."""
    business_quality: Dict[str, Any]
    financial_health: Dict[str, Any]
    technical_trend: Dict[str, Any]
    macroeconomic_factors: Dict[str, Any]
    news_impact: Dict[str, Any]
    competitor_position: Dict[str, Any]
    risk_factors: Dict[str, Any]
    intrinsic_value: Dict[str, Any]


class ExplainabilityEngine:
    """
    Generates comprehensive explanations for investment recommendations.
    Every recommendation must explain all key factors.
    """

    def __init__(self):
        self.explanation_templates = {
            'positive': [
                "Strong {metric} indicates {insight}",
                "Excellent {metric} suggests {insight}",
                "Robust {metric} demonstrates {insight}",
            ],
            'negative': [
                "Weak {metric} raises concerns about {insight}",
                "Declining {metric} suggests {insight}",
                "Poor {metric} indicates {insight}",
            ],
            'neutral': [
                "Stable {metric} shows {insight}",
                "Moderate {metric} indicates {insight}",
            ]
        }

    def generate_explanation(
        self,
        symbol: str,
        company_name: str,
        investment_score: float,
        confidence: float,
        shap_values: Dict[str, float],
        fundamental_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        sentiment_data: Dict[str, Any],
        macro_data: Dict[str, Any],
        news_data: List[Dict[str, Any]],
        competitor_data: Dict[str, Any],
        risk_factors: List[str],
        intrinsic_value: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for a recommendation.
        
        Returns:
            Complete explanation with all components
        """
        # Generate component explanations
        business_quality = self._explain_business_quality(fundamental_data)
        financial_health = self._explain_financial_health(fundamental_data)
        technical_trend = self._explain_technical_trend(technical_data)
        macro_factors = self._explain_macro_factors(macro_data)
        news_impact = self._explain_news_impact(news_data)
        competitor_position = self._explain_competitor_position(competitor_data)
        risk_factors_explained = self._explain_risk_factors(risk_factors)
        intrinsic_value_explained = self._explain_intrinsic_value(intrinsic_value)
        
        # Generate SHAP-based explanation
        shap_explanation = self._generate_shap_explanation(shap_values)
        
        # Generate natural language summary
        natural_language_summary = self._generate_natural_language_summary(
            symbol=symbol,
            company_name=company_name,
            investment_score=investment_score,
            confidence=confidence,
            business_quality=business_quality,
            financial_health=financial_health,
            technical_trend=technical_trend,
            risk_factors=risk_factors_explained
        )
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'investment_score': investment_score,
            'confidence': confidence,
            'generated_at': datetime.utcnow().isoformat(),
            'components': {
                'business_quality': business_quality,
                'financial_health': financial_health,
                'technical_trend': technical_trend,
                'macroeconomic_factors': macro_factors,
                'news_impact': news_impact,
                'competitor_position': competitor_position,
                'risk_factors': risk_factors_explained,
                'intrinsic_value': intrinsic_value_explained,
            },
            'shap_explanation': shap_explanation,
            'natural_language_summary': natural_language_summary,
            'top_positive_factors': shap_explanation.get('top_positive', []),
            'top_negative_factors': shap_explanation.get('top_negative', []),
        }

    def _explain_business_quality(self, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explain business quality factors."""
        explanation = {
            'score': 0.0,
            'factors': [],
            'summary': ''
        }
        
        # Revenue growth
        revenue_growth = fundamental_data.get('revenue_growth', 0)
        if revenue_growth > 0.15:
            explanation['factors'].append({
                'factor': 'Revenue Growth',
                'value': f"{revenue_growth:.1%}",
                'sentiment': 'POSITIVE',
                'explanation': f"Strong revenue growth of {revenue_growth:.1%} indicates expanding market share and healthy business"
            })
        elif revenue_growth < 0:
            explanation['factors'].append({
                'factor': 'Revenue Growth',
                'value': f"{revenue_growth:.1%}",
                'sentiment': 'NEGATIVE',
                'explanation': f"Declining revenue of {abs(revenue_growth):.1%} raises concerns about market position"
            })
        
        # Profit margins
        profit_margin = fundamental_data.get('profit_margin', 0)
        if profit_margin > 0.15:
            explanation['factors'].append({
                'factor': 'Profit Margin',
                'value': f"{profit_margin:.1%}",
                'sentiment': 'POSITIVE',
                'explanation': f"Healthy profit margin of {profit_margin:.1%} demonstrates strong pricing power"
            })
        
        # ROE
        roe = fundamental_data.get('roe', 0)
        if roe > 0.15:
            explanation['factors'].append({
                'factor': 'Return on Equity',
                'value': f"{roe:.1%}",
                'sentiment': 'POSITIVE',
                'explanation': f"Strong ROE of {roe:.1%} indicates efficient capital utilization"
            })
        
        # Calculate overall score
        if explanation['factors']:
            positive_count = sum(1 for f in explanation['factors'] if f['sentiment'] == 'POSITIVE')
            explanation['score'] = positive_count / len(explanation['factors'])
        
        return explanation

    def _explain_financial_health(self, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explain financial health factors."""
        explanation = {
            'score': 0.0,
            'factors': [],
            'summary': ''
        }
        
        # Debt-to-equity
        debt_to_equity = fundamental_data.get('debt_to_equity', 0)
        if debt_to_equity < 0.5:
            explanation['factors'].append({
                'factor': 'Debt-to-Equity',
                'value': f"{debt_to_equity:.2f}",
                'sentiment': 'POSITIVE',
                'explanation': f"Low debt-to-equity ratio of {debt_to_equity:.2f} indicates strong balance sheet"
            })
        elif debt_to_equity > 1.5:
            explanation['factors'].append({
                'factor': 'Debt-to-Equity',
                'value': f"{debt_to_equity:.2f}",
                'sentiment': 'NEGATIVE',
                'explanation': f"High debt-to-equity ratio of {debt_to_equity:.2f} raises financial risk concerns"
            })
        
        # Free cash flow
        fcf = fundamental_data.get('free_cash_flow', 0)
        if fcf > 0:
            explanation['factors'].append({
                'factor': 'Free Cash Flow',
                'value': f"${fcf/1e9:.2f}B",
                'sentiment': 'POSITIVE',
                'explanation': f"Positive free cash flow of ${fcf/1e9:.2f}B demonstrates financial strength"
            })
        
        # Current ratio
        current_ratio = fundamental_data.get('current_ratio', 0)
        if 1.5 <= current_ratio <= 3.0:
            explanation['factors'].append({
                'factor': 'Current Ratio',
                'value': f"{current_ratio:.2f}",
                'sentiment': 'POSITIVE',
                'explanation': f"Healthy current ratio of {current_ratio:.2f} indicates good liquidity"
            })
        
        if explanation['factors']:
            positive_count = sum(1 for f in explanation['factors'] if f['sentiment'] == 'POSITIVE')
            explanation['score'] = positive_count / len(explanation['factors'])
        
        return explanation

    def _explain_technical_trend(self, technical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explain technical trend factors."""
        explanation = {
            'score': 0.0,
            'factors': [],
            'summary': '',
            'trend': 'NEUTRAL'
        }
        
        # Moving averages
        sma_20 = technical_data.get('sma_20', 0)
        sma_50 = technical_data.get('sma_50', 0)
        current_price = technical_data.get('current_price', 0)
        
        if current_price > sma_20 > sma_50:
            explanation['factors'].append({
                'factor': 'Moving Averages',
                'value': f"Price: {current_price:.2f}, SMA20: {sma_20:.2f}, SMA50: {sma_50:.2f}",
                'sentiment': 'POSITIVE',
                'explanation': "Price above both short and long-term moving averages indicates bullish trend"
            })
            explanation['trend'] = 'BULLISH'
        elif current_price < sma_20 < sma_50:
            explanation['factors'].append({
                'factor': 'Moving Averages',
                'value': f"Price: {current_price:.2f}, SMA20: {sma_20:.2f}, SMA50: {sma_50:.2f}",
                'sentiment': 'NEGATIVE',
                'explanation': "Price below both moving averages indicates bearish trend"
            })
            explanation['trend'] = 'BEARISH'
        
        # RSI
        rsi = technical_data.get('rsi', 50)
        if rsi < 30:
            explanation['factors'].append({
                'factor': 'RSI',
                'value': f"{rsi:.1f}",
                'sentiment': 'POSITIVE',
                'explanation': f"RSI at {rsi:.1f} indicates oversold condition, potential reversal"
            })
        elif rsi > 70:
            explanation['factors'].append({
                'factor': 'RSI',
                'value': f"{rsi:.1f}",
                'sentiment': 'NEGATIVE',
                'explanation': f"RSI at {rsi:.1f} indicates overbought condition, potential pullback"
            })
        
        # MACD
        macd = technical_data.get('macd', 0)
        macd_signal = technical_data.get('macd_signal', 0)
        if macd > macd_signal:
            explanation['factors'].append({
                'factor': 'MACD',
                'value': f"MACD: {macd:.2f}, Signal: {macd_signal:.2f}",
                'sentiment': 'POSITIVE',
                'explanation': "MACD above signal line indicates bullish momentum"
            })
        
        if explanation['factors']:
            positive_count = sum(1 for f in explanation['factors'] if f['sentiment'] == 'POSITIVE')
            explanation['score'] = positive_count / len(explanation['factors'])
        
        return explanation

    def _explain_macro_factors(self, macro_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explain macroeconomic factors."""
        explanation = {
            'score': 0.0,
            'factors': [],
            'summary': ''
        }
        
        # Interest rates
        interest_rate = macro_data.get('interest_rate', 0)
        if interest_rate < 4:
            explanation['factors'].append({
                'factor': 'Interest Rate Environment',
                'value': f"{interest_rate:.2f}%",
                'sentiment': 'POSITIVE',
                'explanation': f"Low interest rate environment at {interest_rate:.2f}% supports growth"
            })
        elif interest_rate > 6:
            explanation['factors'].append({
                'factor': 'Interest Rate Environment',
                'value': f"{interest_rate:.2f}%",
                'sentiment': 'NEGATIVE',
                'explanation': f"High interest rate environment at {interest_rate:.2f}% may pressure valuations"
            })
        
        # Inflation
        inflation = macro_data.get('inflation', 0)
        if 2 <= inflation <= 4:
            explanation['factors'].append({
                'factor': 'Inflation',
                'value': f"{inflation:.1f}%",
                'sentiment': 'POSITIVE',
                'explanation': f"Stable inflation at {inflation:.1f}% supports economic growth"
            })
        
        # GDP growth
        gdp_growth = macro_data.get('gdp_growth', 0)
        if gdp_growth > 2.5:
            explanation['factors'].append({
                'factor': 'GDP Growth',
                'value': f"{gdp_growth:.1f}%",
                'sentiment': 'POSITIVE',
                'explanation': f"Strong GDP growth of {gdp_growth:.1f}% indicates healthy economy"
            })
        
        if explanation['factors']:
            positive_count = sum(1 for f in explanation['factors'] if f['sentiment'] == 'POSITIVE')
            explanation['score'] = positive_count / len(explanation['factors'])
        
        return explanation

    def _explain_news_impact(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Explain news impact."""
        explanation = {
            'score': 0.0,
            'recent_news': [],
            'summary': ''
        }
        
        if not news_data:
            return explanation
        
        # Process recent news
        for news in news_data[:5]:  # Top 5 recent news
            sentiment = news.get('sentiment', 'NEUTRAL')
            explanation['recent_news'].append({
                'title': news.get('title', ''),
                'sentiment': sentiment,
                'impact': news.get('impact', 'LOW'),
                'date': news.get('date', ''),
            })
        
        # Calculate overall news sentiment
        sentiments = [n['sentiment'] for n in explanation['recent_news']]
        positive_count = sentiments.count('POSITIVE')
        negative_count = sentiments.count('NEGATIVE')
        
        if len(sentiments) > 0:
            explanation['score'] = (positive_count - negative_count) / len(sentiments)
        
        return explanation

    def _explain_competitor_position(self, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explain competitive position."""
        explanation = {
            'score': 0.0,
            'market_share': 0.0,
            'competitive_advantages': [],
            'summary': ''
        }
        
        market_share = competitor_data.get('market_share', 0)
        explanation['market_share'] = market_share
        
        if market_share > 0.20:
            explanation['competitive_advantages'].append(
                f"Market leader with {market_share:.1%} market share"
            )
        
        # Check for competitive advantages
        advantages = competitor_data.get('advantages', [])
        explanation['competitive_advantages'].extend(advantages[:3])
        
        if explanation['competitive_advantages']:
            explanation['score'] = min(1.0, len(explanation['competitive_advantages']) / 3)
        
        return explanation

    def _explain_risk_factors(self, risk_factors: List[str]) -> Dict[str, Any]:
        """Explain identified risk factors."""
        explanation = {
            'risk_count': len(risk_factors),
            'risks': [],
            'overall_risk_level': 'LOW'
        }
        
        for risk in risk_factors[:5]:  # Top 5 risks
            explanation['risks'].append({
                'risk': risk,
                'severity': 'MEDIUM',
                'mitigation': 'Monitor closely'
            })
        
        if len(risk_factors) > 5:
            explanation['overall_risk_level'] = 'HIGH'
        elif len(risk_factors) > 2:
            explanation['overall_risk_level'] = 'MEDIUM'
        
        return explanation

    def _explain_intrinsic_value(self, intrinsic_value: Dict[str, Any]) -> Dict[str, Any]:
        """Explain intrinsic value calculation."""
        explanation = {
            'dcf_value': 0.0,
            'current_price': 0.0,
            'upside_potential': 0.0,
            'methodology': '',
            'key_assumptions': []
        }
        
        dcf_value = intrinsic_value.get('dcf_value', 0)
        current_price = intrinsic_value.get('current_price', 0)
        
        explanation['dcf_value'] = dcf_value
        explanation['current_price'] = current_price
        
        if current_price > 0:
            upside = (dcf_value - current_price) / current_price
            explanation['upside_potential'] = upside
        
        explanation['methodology'] = intrinsic_value.get('methodology', 'DCF Analysis')
        explanation['key_assumptions'] = intrinsic_value.get('assumptions', [])[:5]
        
        return explanation

    def _generate_shap_explanation(self, shap_values: Dict[str, float]) -> Dict[str, Any]:
        """Generate SHAP-based explanation."""
        if not shap_values:
            return {'top_positive': [], 'top_negative': [], 'feature_importance': {}}
        
        # Sort by absolute value
        sorted_features = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
        
        top_positive = []
        top_negative = []
        
        for feature, value in sorted_features:
            if value > 0:
                top_positive.append({
                    'feature': feature,
                    'shap_value': round(value, 4),
                    'impact': 'POSITIVE'
                })
            else:
                top_negative.append({
                    'feature': feature,
                    'shap_value': round(value, 4),
                    'impact': 'NEGATIVE'
                })
        
        return {
            'top_positive': top_positive[:5],
            'top_negative': top_negative[:5],
            'feature_importance': dict(sorted_features[:10])
        }

    def _generate_natural_language_summary(
        self,
        symbol: str,
        company_name: str,
        investment_score: float,
        confidence: float,
        business_quality: Dict[str, Any],
        financial_health: Dict[str, Any],
        technical_trend: Dict[str, Any],
        risk_factors: Dict[str, Any]
    ) -> str:
        """Generate natural language summary of recommendation."""
        
        # Overall recommendation
        if investment_score >= 75:
            recommendation = "STRONG BUY"
        elif investment_score >= 60:
            recommendation = "BUY"
        elif investment_score >= 40:
            recommendation = "HOLD"
        elif investment_score >= 25:
            recommendation = "SELL"
        else:
            recommendation = "STRONG SELL"
        
        summary_parts = [
            f"{company_name} ({symbol}) has an investment score of {investment_score:.1f}/100, "
            f"indicating a {recommendation} recommendation with {confidence:.0%} confidence."
        ]
        
        # Add positive factors
        positive_factors = []
        if business_quality.get('score', 0) > 0.5:
            positive_factors.append("strong business quality")
        if financial_health.get('score', 0) > 0.5:
            positive_factors.append("solid financial health")
        if technical_trend.get('trend') == 'BULLISH':
            positive_factors.append("bullish technical trend")
        
        if positive_factors:
            summary_parts.append(f"Key strengths include {', '.join(positive_factors)}.")
        
        # Add risk factors
        risk_count = risk_factors.get('risk_count', 0)
        if risk_count > 0:
            summary_parts.append(f"Investors should be aware of {risk_count} risk factor{'s' if risk_count > 1 else ''}.")
        
        return ' '.join(summary_parts)

    def generate_scenario_analysis(
        self,
        symbol: str,
        company_name: str,
        current_price: float,
        intrinsic_value: float,
        volatility: float,
        time_horizon_days: int = 365
    ) -> Dict[str, Any]:
        """
        Generate bull/base/bear scenario analysis.
        """
        # Calculate scenarios
        bull_case = {
            'name': 'Bull Case',
            'expected_price': intrinsic_value * 1.3,
            'expected_cagr': ((intrinsic_value * 1.3) / current_price - 1) * 100,
            'probability': 0.25,
            'supporting_factors': [
                "Strong earnings growth exceeding expectations",
                "Sector tailwinds and market expansion",
                "Successful new product launches",
                "Macroeconomic environment remains favorable"
            ]
        }
        
        base_case = {
            'name': 'Base Case',
            'expected_price': intrinsic_value,
            'expected_cagr': (intrinsic_value / current_price - 1) * 100,
            'probability': 0.50,
            'supporting_factors': [
                "Earnings grow in line with expectations",
                "Current valuation multiples maintained",
                "No significant market disruptions"
            ]
        }
        
        bear_case = {
            'name': 'Bear Case',
            'expected_price': current_price * 0.7,
            'expected_cagr': (0.7 - 1) * 100,
            'probability': 0.25,
            'supporting_factors': [
                "Earnings miss due to market conditions",
                "Increased competition pressures margins",
                "Macroeconomic slowdown impacts demand"
            ]
        }
        
        # Calculate risk metrics
        expected_return = (
            bull_case['expected_cagr'] * bull_case['probability'] +
            base_case['expected_cagr'] * base_case['probability'] +
            bear_case['expected_cagr'] * bear_case['probability']
        )
        
        risk = volatility * 100  # Convert to percentage
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'current_price': current_price,
            'time_horizon_days': time_horizon_days,
            'scenarios': [bull_case, base_case, bear_case],
            'expected_cagr': round(expected_return, 2),
            'risk': round(risk, 2),
            'risk_adjusted_return': round(expected_return / (risk + 0.01), 2),
        }

    def calculate_confidence_score(
        self,
        model_agreement: float,
        data_completeness: float,
        prediction_stability: float,
        market_volatility: float,
        historical_accuracy: float
    ) -> Dict[str, Any]:
        """
        Calculate confidence score based on multiple factors.
        """
        # Weighted combination
        weights = {
            'model_agreement': 0.25,
            'data_completeness': 0.20,
            'prediction_stability': 0.20,
            'market_volatility': 0.15,
            'historical_accuracy': 0.20
        }
        
        # Invert market volatility (lower volatility = higher confidence)
        volatility_factor = max(0.0, 1.0 - market_volatility)
        
        confidence_score = (
            model_agreement * weights['model_agreement'] +
            data_completeness * weights['data_completeness'] +
            prediction_stability * weights['prediction_stability'] +
            volatility_factor * weights['market_volatility'] +
            historical_accuracy * weights['historical_accuracy']
        )
        
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Determine confidence level
        if confidence_score >= 0.8:
            confidence_level = 'HIGH'
        elif confidence_score >= 0.6:
            confidence_level = 'MEDIUM'
        else:
            confidence_level = 'LOW'
        
        return {
            'confidence_score': round(confidence_score, 2),
            'confidence_level': confidence_level,
            'components': {
                'model_agreement': round(model_agreement, 2),
                'data_completeness': round(data_completeness, 2),
                'prediction_stability': round(prediction_stability, 2),
                'market_volatility': round(market_volatility, 2),
                'historical_accuracy': round(historical_accuracy, 2),
            }
        }