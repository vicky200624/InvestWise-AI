"""
InvestWise AI 3.0 — Unified Database Models Re-export

Re-exports all Django ORM models from the authoritative modular DRF apps:
- apps.accounts.models: UserPortfolio, BrokerCredentials
- apps.portfolio.models: AssetHolding
- apps.research.models: StockAnalysis, AgentTask, RAGDocument, InvestmentFeedback, TrainedModel, MacroIndicator
- apps.chat.models: ChatSession, ChatMessage
- apps.watchlist.models: Watchlist, WatchlistItem, PriceAlert
"""

from apps.accounts.models import UserPortfolio, BrokerCredentials
from apps.portfolio.models import AssetHolding
from apps.research.models import (
    StockAnalysis,
    AgentTask,
    RAGDocument,
    InvestmentFeedback,
    TrainedModel,
    MacroIndicator,
)
from apps.chat.models import ChatSession, ChatMessage
from apps.watchlist.models import Watchlist, WatchlistItem, PriceAlert

__all__ = [
    'UserPortfolio',
    'BrokerCredentials',
    'AssetHolding',
    'ChatSession',
    'ChatMessage',
    'StockAnalysis',
    'AgentTask',
    'RAGDocument',
    'InvestmentFeedback',
    'TrainedModel',
    'MacroIndicator',
    'Watchlist',
    'WatchlistItem',
    'PriceAlert',
]