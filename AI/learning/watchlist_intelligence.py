"""
Watchlist Intelligence for InvestWise AI Learning Engine.
Manages AI-generated watchlists with intelligent categorization and monitoring.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WatchlistCategory(Enum):
    WAITING_VALUATION = "Waiting for Better Valuation"
    WAITING_EARNINGS = "Waiting for Earnings"
    WAITING_BREAKOUT = "Waiting for Breakout"
    WAITING_MACRO = "Waiting for Macro Improvement"
    WAITING_COMPETITOR = "Waiting for Competitor Update"
    WAITING_TECHNICAL = "Waiting for Technical Confirmation"


@dataclass
class WatchlistItem:
    """Individual watchlist item with monitoring state."""
    symbol: str
    company_name: str
    category: WatchlistCategory
    added_at: str
    trigger_conditions: Dict[str, Any]
    current_status: Dict[str, Any]
    priority: float = 1.0


class WatchlistIntelligence:
    """
    AI-generated watchlists with intelligent categorization and monitoring.
    """

    def __init__(self):
        self.user_watchlists: Dict[int, Dict[str, List[WatchlistItem]]] = {}
        self.monitoring_config = {
            'price_change_threshold': 0.05,  # 5% price change
            'volume_spike_threshold': 2.0,  # 2x average volume
            'valuation_attractive_threshold': 0.8,  # Score > 0.8
        }

    def create_intelligent_watchlist(
        self,
        user_id: int,
        watchlist_name: str,
        symbols: List[str],
        category: WatchlistCategory,
        trigger_conditions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create an AI-generated watchlist with intelligent categorization.
        """
        if user_id not in self.user_watchlists:
            self.user_watchlists[user_id] = {}
        
        items = []
        for symbol in symbols:
            item = WatchlistItem(
                symbol=symbol,
                company_name='',  # To be filled by data service
                category=category,
                added_at=datetime.utcnow().isoformat(),
                trigger_conditions=trigger_conditions or self._default_triggers(category),
                current_status={},
                priority=1.0
            )
            items.append(item)
        
        self.user_watchlists[user_id][watchlist_name] = items
        
        logger.info(f"Created watchlist '{watchlist_name}' for user {user_id} with {len(items)} items")
        return {
            'watchlist_name': watchlist_name,
            'category': category.value,
            'item_count': len(items),
            'symbols': [item.symbol for item in items],
        }

    def categorize_stock(self, stock_data: Dict[str, Any]) -> WatchlistCategory:
        """
        Intelligently categorize a stock based on current data.
        """
        # Check for valuation opportunity
        if stock_data.get('valuation_score', 0) > 0.8:
            return WatchlistCategory.WAITING_VALUATION
        
        # Check for earnings announcement
        if stock_data.get('days_to_earnings') is not None and 0 <= stock_data.get('days_to_earnings', -1) <= 14:
            return WatchlistCategory.WAITING_EARNINGS
        
        # Check for technical breakout potential
        if stock_data.get('technical_score', 0) > 0.7 and stock_data.get('volume_trend') == 'increasing':
            return WatchlistCategory.WAITING_BREAKOUT
        
        # Check for macro dependency
        if stock_data.get('macro_sensitivity', 0) > 0.6:
            return WatchlistCategory.WAITING_MACRO
        
        # Check for competitor dependency
        if stock_data.get('competitor_news_impact', 0) > 0.5:
            return WatchlistCategory.WAITING_COMPETITOR
        
        # Default to technical confirmation
        return WatchlistCategory.WAITING_TECHNICAL

    def _default_triggers(self, category: WatchlistCategory) -> Dict[str, Any]:
        """Get default trigger conditions for a category."""
        triggers = {
            WatchlistCategory.WAITING_VALUATION: {
                'price_change_percent': 0.10,
                'valuation_score_threshold': 0.85,
                'pe_ratio_below': 15.0,
            },
            WatchlistCategory.WAITING_EARNINGS: {
                'days_before_earnings': 7,
                'analyst_expectation_change': 0.05,
            },
            WatchlistCategory.WAITING_BREAKOUT: {
                'volume_spike': 2.0,
                'price_above_resistance': True,
                'rsi_below': 70,
            },
            WatchlistCategory.WAITING_MACRO: {
                'interest_rate_change': 0.25,
                'inflation_data': 'CPI',
                'gdp_growth': 3.0,
            },
            WatchlistCategory.WAITING_COMPETITOR: {
                'competitor_announcement': True,
                'market_share_change': 0.05,
            },
            WatchlistCategory.WAITING_TECHNICAL: {
                'moving_average_crossover': True,
                'macd_bullish': True,
                'volume_confirmation': True,
            },
        }
        return triggers.get(category, {})

    def monitor_watchlist(
        self,
        user_id: int,
        watchlist_name: str,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Monitor watchlist items and detect trigger conditions.
        """
        if user_id not in self.user_watchlists or watchlist_name not in self.user_watchlists[user_id]:
            return []
        
        items = self.user_watchlists[user_id][watchlist_name]
        alerts = []
        
        for item in items:
            symbol = item.symbol
            if symbol not in market_data:
                continue
            
            stock_data = market_data[symbol]
            triggered = self._check_triggers(item, stock_data)
            
            if triggered:
                alert = {
                    'symbol': symbol,
                    'company_name': item.company_name,
                    'category': item.category.value,
                    'trigger_reason': triggered,
                    'current_data': stock_data,
                    'priority': item.priority,
                    'timestamp': datetime.utcnow().isoformat(),
                }
                alerts.append(alert)
        
        return alerts

    def _check_triggers(self, item: WatchlistItem, stock_data: Dict[str, Any]) -> Optional[str]:
        """Check if any trigger conditions are met."""
        triggers = item.trigger_conditions
        
        # Price change trigger
        if 'price_change_percent' in triggers:
            price_change = stock_data.get('price_change_percent', 0)
            if abs(price_change) >= triggers['price_change_percent']:
                return f"Price changed {price_change:.2f}%"
        
        # Valuation trigger
        if 'valuation_score_threshold' in triggers:
            valuation_score = stock_data.get('valuation_score', 0)
            if valuation_score >= triggers['valuation_score_threshold']:
                return f"Valuation score reached {valuation_score:.2f}"
        
        # Volume spike trigger
        if 'volume_spike' in triggers:
            volume_ratio = stock_data.get('volume_ratio', 1.0)
            if volume_ratio >= triggers['volume_spike']:
                return f"Volume spike detected ({volume_ratio:.1f}x average)"
        
        # Technical breakout trigger
        if triggers.get('price_above_resistance') and stock_data.get('above_resistance', False):
            return "Price broke above resistance level"
        
        # Earnings trigger
        if 'days_before_earnings' in triggers:
            days_to_earnings = stock_data.get('days_to_earnings', 999)
            if days_to_earnings <= triggers['days_before_earnings']:
                return f"Earnings in {days_to_earnings} days"
        
        return None

    def update_watchlist_priority(
        self,
        user_id: int,
        watchlist_name: str,
        symbol: str,
        priority: float
    ) -> bool:
        """Update priority of a watchlist item."""
        if user_id not in self.user_watchlists or watchlist_name not in self.user_watchlists[user_id]:
            return False
        
        for item in self.user_watchlists[user_id][watchlist_name]:
            if item.symbol == symbol:
                item.priority = max(0.1, min(2.0, priority))
                return True
        
        return False

    def get_user_watchlists(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all watchlists for a user."""
        if user_id not in self.user_watchlists:
            return []
        
        result = []
        for watchlist_name, items in self.user_watchlists[user_id].items():
            result.append({
                'name': watchlist_name,
                'category': items[0].category.value if items else 'Unknown',
                'item_count': len(items),
                'symbols': [item.symbol for item in items],
                'created_at': items[0].added_at if items else datetime.utcnow().isoformat(),
            })
        
        return result

    def remove_from_watchlist(
        self,
        user_id: int,
        watchlist_name: str,
        symbol: str
    ) -> bool:
        """Remove a symbol from watchlist."""
        if user_id not in self.user_watchlists or watchlist_name not in self.user_watchlists[user_id]:
            return False
        
        items = self.user_watchlists[user_id][watchlist_name]
        self.user_watchlists[user_id][watchlist_name] = [item for item in items if item.symbol != symbol]
        
        return True


class AutonomousMonitor:
    """
    Continuous monitoring of portfolio, watchlist, market, and economy.
    """

    def __init__(self, watchlist_intelligence: WatchlistIntelligence = None):
        self.watchlist_intelligence = watchlist_intelligence or WatchlistIntelligence()
        self.alert_handlers = []
        self.monitoring_active = False

    def register_alert_handler(self, handler) -> None:
        """Register an alert handler function."""
        self.alert_handlers.append(handler)

    def start_monitoring(self) -> None:
        """Start autonomous monitoring."""
        self.monitoring_active = True
        logger.info("Autonomous monitoring started")

    def stop_monitoring(self) -> None:
        """Stop autonomous monitoring."""
        self.monitoring_active = False
        logger.info("Autonomous monitoring stopped")

    def check_portfolio_triggers(
        self,
        user_id: int,
        portfolio_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check portfolio for trigger conditions.
        """
        alerts = []
        
        # Check for significant price changes
        for holding in portfolio_data.get('holdings', []):
            symbol = holding.get('symbol')
            if symbol in market_data:
                stock_data = market_data[symbol]
                price_change = stock_data.get('price_change_percent', 0)
                
                if abs(price_change) >= 0.10:  # 10% change
                    alerts.append({
                        'alert_type': 'PORTFOLIO_RISK',
                        'symbol': symbol,
                        'message': f"Significant price change: {price_change:.2f}%",
                        'priority': 'HIGH' if abs(price_change) >= 0.15 else 'MEDIUM',
                        'data': stock_data,
                    })
        
        # Check for sector concentration risk
        sector_allocation = portfolio_data.get('sector_allocation', {})
        for sector, allocation in sector_allocation.items():
            if allocation > 30:  # >30% in one sector
                alerts.append({
                    'alert_type': 'PORTFOLIO_RISK',
                    'message': f"High sector concentration: {sector} at {allocation:.1f}%",
                    'priority': 'MEDIUM',
                    'data': {'sector': sector, 'allocation': allocation},
                })
        
        return alerts

    def check_market_triggers(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check market-wide trigger conditions.
        """
        alerts = []
        
        # Check market volatility
        vix = market_data.get('vix', 0)
        if vix > 30:
            alerts.append({
                'alert_type': 'MACRO',
                'message': f"High market volatility (VIX: {vix:.2f})",
                'priority': 'HIGH',
                'data': {'vix': vix},
            })
        
        # Check interest rates
        interest_rate = market_data.get('interest_rate', 0)
        if interest_rate > 6.0:
            alerts.append({
                'alert_type': 'MACRO',
                'message': f"High interest rate environment: {interest_rate:.2f}%",
                'priority': 'MEDIUM',
                'data': {'interest_rate': interest_rate},
            })
        
        return alerts

    def generate_alerts(
        self,
        user_id: int,
        portfolio_data: Dict[str, Any],
        watchlists: List[str],
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate comprehensive alerts from all monitoring sources.
        """
        all_alerts = []
        
        # Portfolio alerts
        portfolio_alerts = self.check_portfolio_triggers(user_id, portfolio_data, market_data)
        all_alerts.extend(portfolio_alerts)
        
        # Watchlist alerts
        for watchlist_name in watchlists:
            watchlist_alerts = self.watchlist_intelligence.monitor_watchlist(
                user_id, watchlist_name, market_data
            )
            all_alerts.extend(watchlist_alerts)
        
        # Market alerts
        market_alerts = self.check_market_triggers(market_data)
        all_alerts.extend(market_alerts)
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_alerts.sort(key=lambda x: priority_order.get(x.get('priority', 'LOW'), 4))
        
        return all_alerts