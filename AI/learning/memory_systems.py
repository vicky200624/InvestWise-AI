"""
Memory systems for InvestWise AI Learning Engine.
Manages conversation, portfolio, and research memory.
Standalone module with zero Django dependencies.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class ConversationMemoryManager:
    """
    Manages conversation memory for context-aware interactions.
    Never exposes private memory to other users.
    """

    def __init__(self, max_memories_per_user: int = 1000, max_age_days: int = 90):
        self.max_memories_per_user = max_memories_per_user
        self.max_age_days = max_age_days
        self.user_memories: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    def store_memory(
        self,
        user_id: int,
        session_id: str,
        memory_type: str,
        entities: List[str],
        summary: str,
        key_points: List[str],
        sentiment: str = '',
        context_data: Dict[str, Any] = None,
        relevance_score: float = 1.0
    ) -> Dict[str, Any]:
        """
        Store a new conversation memory.
        """
        memory = {
            'user_id': user_id,
            'session_id': session_id,
            'memory_type': memory_type,
            'entities': entities,
            'summary': summary,
            'key_points': key_points,
            'sentiment': sentiment,
            'context_data': context_data or {},
            'relevance_score': relevance_score,
            'created_at': datetime.utcnow().isoformat(),
            'last_accessed': datetime.utcnow().isoformat(),
        }
        
        self.user_memories[user_id].append(memory)
        
        # Enforce limits
        self._enforce_limits(user_id)
        
        logger.debug(f"Stored {memory_type} memory for user {user_id}")
        return memory

    def retrieve_relevant_memories(
        self,
        user_id: int,
        query_entities: List[str],
        memory_types: List[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to current query.
        """
        if user_id not in self.user_memories:
            return []
        
        user_mem_list = self.user_memories[user_id]
        
        # Filter by memory type if specified
        if memory_types:
            user_mem_list = [m for m in user_mem_list if m['memory_type'] in memory_types]
        
        # Calculate relevance score based on entity overlap
        scored_memories = []
        for memory in user_mem_list:
            score = self._calculate_relevance(memory, query_entities)
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by relevance and recency
        scored_memories.sort(key=lambda x: (x[0], x[1]['last_accessed']), reverse=True)
        
        # Update last_accessed for retrieved memories
        for _, memory in scored_memories[:max_results]:
            memory['last_accessed'] = datetime.utcnow().isoformat()
        
        return [m for _, m in scored_memories[:max_results]]

    def _calculate_relevance(self, memory: Dict[str, Any], query_entities: List[str]) -> float:
        """Calculate relevance score between memory and query."""
        if not query_entities:
            return memory['relevance_score']
        
        memory_entities = set(e.lower() for e in memory.get('entities', []))
        query_entities_lower = set(e.lower() for e in query_entities)
        
        # Calculate overlap
        overlap = len(memory_entities & query_entities_lower)
        if overlap == 0:
            return 0.0
        
        # Combine with base relevance and recency
        base_relevance = memory['relevance_score']
        entity_relevance = overlap / len(query_entities_lower)
        
        # Decay based on age
        created_at = datetime.fromisoformat(memory['created_at'])
        age_days = (datetime.utcnow() - created_at).days
        recency_decay = max(0.1, 1.0 - (age_days / self.max_age_days))
        
        return base_relevance * entity_relevance * recency_decay

    def _enforce_limits(self, user_id: int) -> None:
        """Enforce memory limits per user."""
        memories = self.user_memories[user_id]
        
        # Remove old memories
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_age_days)
        memories = [
            m for m in memories
            if datetime.fromisoformat(m['created_at']) > cutoff_date
        ]
        
        # Keep only most recent if over limit
        if len(memories) > self.max_memories_per_user:
            memories = sorted(memories, key=lambda x: x['last_accessed'], reverse=True)[:self.max_memories_per_user]
        
        self.user_memories[user_id] = memories

    def get_user_context(self, user_id: int, max_memories: int = 20) -> Dict[str, Any]:
        """
        Get aggregated context for a user.
        """
        if user_id not in self.user_memories:
            return {}
        
        memories = self.user_memories[user_id][:max_memories]
        
        # Aggregate entities
        all_entities = []
        all_key_points = []
        sentiments = []
        
        for memory in memories:
            all_entities.extend(memory.get('entities', []))
            all_key_points.extend(memory.get('key_points', []))
            if memory.get('sentiment'):
                sentiments.append(memory['sentiment'])
        
        return {
            'recent_entities': list(set(all_entities))[:20],
            'key_points': list(set(all_key_points))[:10],
            'dominant_sentiment': max(set(sentiments), key=sentiments.count) if sentiments else 'NEUTRAL',
            'memory_count': len(memories),
        }


class PortfolioMemoryManager:
    """
    Manages portfolio memory tracking historical and current state.
    """

    def __init__(self):
        self.user_portfolios: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    def record_portfolio_snapshot(
        self,
        user_id: int,
        holdings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Record current portfolio state as a snapshot.
        """
        snapshot = {
            'user_id': user_id,
            'holdings': holdings,
            'snapshot_date': datetime.utcnow().isoformat(),
            'total_value': sum(h.get('current_value', 0) for h in holdings),
            'total_invested': sum(h.get('avg_price', 0) * h.get('qty', 0) for h in holdings),
        }
        
        # Mark previous snapshots as not current
        for old_snapshot in self.user_portfolios[user_id]:
            old_snapshot['is_current'] = False
        
        self.user_portfolios[user_id].append(snapshot)
        
        logger.debug(f"Recorded portfolio snapshot for user {user_id}")
        return snapshot

    def get_current_portfolio(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get current portfolio snapshot."""
        if user_id not in self.user_portfolios:
            return None
        
        for snapshot in reversed(self.user_portfolios[user_id]):
            if snapshot.get('is_current', True):
                return snapshot
        
        return self.user_portfolios[user_id][-1] if self.user_portfolios[user_id] else None

    def get_historical_holdings(
        self,
        user_id: int,
        symbol: str,
        max_records: int = 10
    ) -> List[Dict[str, Any]]:
        """Get historical holdings for a specific symbol."""
        if user_id not in self.user_portfolios:
            return []
        
        historical = []
        for snapshot in self.user_portfolios[user_id]:
            for holding in snapshot.get('holdings', []):
                if holding.get('symbol') == symbol:
                    historical.append({
                        **holding,
                        'snapshot_date': snapshot['snapshot_date']
                    })
        
        return historical[-max_records:]

    def calculate_portfolio_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calculate portfolio performance metrics."""
        current = self.get_current_portfolio(user_id)
        if not current:
            return {}
        
        holdings = current.get('holdings', [])
        total_value = current.get('total_value', 0)
        total_invested = current.get('total_invested', 0)
        
        # Calculate unrealized profit/loss
        unrealized_pnl = total_value - total_invested
        unrealized_pnl_percent = (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0
        
        # Sector allocation
        sector_allocation = defaultdict(float)
        for holding in holdings:
            sector = holding.get('sector', 'Unknown')
            value = holding.get('current_value', 0)
            sector_allocation[sector] += value
        
        # Convert to percentages
        if total_value > 0:
            sector_allocation = {k: (v / total_value * 100) for k, v in sector_allocation.items()}
        
        return {
            'total_value': total_value,
            'total_invested': total_invested,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_percent': unrealized_pnl_percent,
            'sector_allocation': dict(sector_allocation),
            'holding_count': len(holdings),
        }


class ResearchMemoryManager:
    """
    Manages research memory tracking user's research activities.
    """

    def __init__(self, max_memories_per_user: int = 500):
        self.max_memories_per_user = max_memories_per_user
        self.user_research: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    def record_research_activity(
        self,
        user_id: int,
        activity_type: str,
        symbol: str = '',
        company_name: str = '',
        query: str = '',
        result_summary: str = '',
        session_id: str = '',
        documents_used: List[str] = None,
        confidence_score: float = None
    ) -> Dict[str, Any]:
        """
        Record a research activity.
        """
        activity = {
            'user_id': user_id,
            'activity_type': activity_type,
            'symbol': symbol,
            'company_name': company_name,
            'query': query,
            'result_summary': result_summary,
            'session_id': session_id,
            'documents_used': documents_used or [],
            'confidence_score': confidence_score,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        self.user_research[user_id].append(activity)
        
        # Enforce limits
        if len(self.user_research[user_id]) > self.max_memories_per_user:
            self.user_research[user_id] = self.user_research[user_id][-self.max_memories_per_user:]
        
        logger.debug(f"Recorded {activity_type} for user {user_id}, symbol={symbol}")
        return activity

    def get_research_history(
        self,
        user_id: int,
        symbol: str = None,
        activity_type: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get research history with optional filters."""
        if user_id not in self.user_research:
            return []
        
        history = self.user_research[user_id]
        
        # Apply filters
        if symbol:
            history = [h for h in history if h.get('symbol') == symbol]
        if activity_type:
            history = [h for h in history if h.get('activity_type') == activity_type]
        
        return history[-limit:]

    def get_frequently_researched(self, user_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently researched companies."""
        if user_id not in self.user_research:
            return []
        
        symbol_counts = defaultdict(int)
        symbol_names = {}
        
        for activity in self.user_research[user_id]:
            symbol = activity.get('symbol', '')
            if symbol:
                symbol_counts[symbol] += 1
                if activity.get('company_name'):
                    symbol_names[symbol] = activity['company_name']
        
        # Sort by frequency
        sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [
            {
                'symbol': symbol,
                'company_name': symbol_names.get(symbol, ''),
                'research_count': count
            }
            for symbol, count in sorted_symbols
        ]


class MemoryConsolidator:
    """
    Consolidates and summarizes memories for long-term storage.
    """

    def __init__(self):
        self.consolidation_threshold = 100  # Consolidate after N memories

    def consolidate_user_memories(
        self,
        user_id: int,
        conversation_mgr: ConversationMemoryManager,
        research_mgr: ResearchMemoryManager
    ) -> Dict[str, Any]:
        """
        Consolidate user memories into summary insights.
        """
        # Get conversation context
        conv_context = conversation_mgr.get_user_context(user_id)
        
        # Get research history
        research_history = research_mgr.get_research_history(user_id, limit=100)
        frequent_research = research_mgr.get_frequently_researched(user_id, top_n=10)
        
        # Generate insights
        insights = {
            'user_id': user_id,
            'consolidated_at': datetime.utcnow().isoformat(),
            'recent_interests': conv_context.get('recent_entities', [])[:10],
            'frequent_research': frequent_research,
            'dominant_sentiment': conv_context.get('dominant_sentiment', 'NEUTRAL'),
            'total_memories': conv_context.get('memory_count', 0),
            'research_activities': len(research_history),
        }
        
        logger.info(f"Consolidated memories for user {user_id}")
        return insights