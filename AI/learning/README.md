# InvestWise AI Learning Engine

## Overview

The Learning Engine is responsible for continuously improving InvestWise AI through safe, auditable, versioned, and reproducible learning. It implements a complete learning pipeline from user feedback to model deployment.

## Core Principles

- **Never retrain immediately** - Follows scheduled approach
- **Never modify production models during inference** - Separate candidate training
- **Safe** - Human approval required for deployment
- **Auditable** - Comprehensive audit logging
- **Versioned** - Full model versioning and promotion protocol
- **Reproducible** - All training is reproducible

## Architecture

```
AI/learning/
├── __init__.py                 # Package initialization
├── feedback_processor.py       # Processes feedback records
├── reward_model.py             # Basic reward calculation
├── enhanced_reward_model.py    # Advanced multi-factor reward calculation
├── rlhf.py                     # Reinforcement Learning from Human Feedback
├── memory_systems.py           # Conversation, portfolio, and research memory
├── watchlist_intelligence.py   # AI-generated watchlists with monitoring
├── drift_detector.py           # Model drift detection
├── explainability_engine.py    # Comprehensive explanations and confidence scores
├── learning_pipeline.py        # Orchestrates complete learning workflow
└── audit_logger.py             # Comprehensive audit trail
```

## Components

### 1. Feedback System

**File**: `backend/apps/feedback/models.py`

Comprehensive feedback database capturing every user interaction:
- BUY/SELL/HOLD Accepted/Rejected
- Portfolio Modified
- Watchlist Added/Removed
- Company Followed
- Research Read
- Manual Rating
- Risk/Horizon Changes

**Key Models**:
- `Feedback` - Main feedback records with reward signals
- `UserPreferenceProfile` - Learned user preferences and RLHF adjustments
- `ConversationMemory` - Context-aware conversation history
- `PortfolioMemory` - Historical portfolio snapshots
- `ResearchMemory` - User research activity tracking
- `AIWatchlist` - AI-generated intelligent watchlists
- `ModelPerformanceMetric` - Performance tracking for drift detection
- `AuditLog` - Comprehensive audit trail
- `Alert` - Portfolio, watchlist, and market alerts

### 2. Reward Model

**Files**: 
- `AI/learning/reward_model.py` - Basic reward calculation
- `AI/learning/enhanced_reward_model.py` - Advanced multi-factor rewards

**Reward Components** (weighted):
1. **Recommendation Accuracy** (30%) - Based on feedback type and actual returns
2. **Portfolio Return** (25%) - Normalized return percentage
3. **User Satisfaction** (20%) - Explicit feedback signals
4. **Holding Duration** (10%) - Optimal 30-365 days
5. **Risk Reduction** (10%) - Change in portfolio risk
6. **Loss Prevention** (5%) - Correct bearish predictions

**Reward Range**: [-1.0, 1.0]

### 3. RLHF (Reinforcement Learning from Human Feedback)

**File**: `AI/learning/rlhf.py`

**Key Concepts**:
- Never directly changes XGBoost weights
- Influences future recommendation strategies
- Learns user preferences over time

**Adjustments**:
- **Ranking Boost** - Sector/company-specific boost factors (0.5x to 2.0x)
- **Confidence Adjustment** - Based on user's acceptance rate (0.5 to 1.0)
- **Priority Weights** - Strategy type preferences (growth, value, dividend, etc.)
- **Explanation Quality Target** - Target explainability score

**Classes**:
- `RLHFTrainer` - Manages RLHF adjustments per user
- `AdaptiveLearningEngine` - Learns user preferences from feedback
- `RLHFAdjustments` - Dataclass for adjustment parameters

### 4. Memory Systems

**File**: `AI/learning/memory_systems.py`

**Three Types of Memory**:

#### Conversation Memory
- Recent conversations
- Research topics
- Portfolio discussions
- Company comparisons
- User preferences
- **Never exposes private memory to other users**

#### Portfolio Memory
- Historical holdings
- Current holdings
- Average buy price
- Holding duration
- Realized/unrealized profit
- Risk exposure
- Sector allocation

#### Research Memory
- Companies analyzed
- Reports read
- Recommendations generated
- Questions asked
- Documents retrieved

**Classes**:
- `ConversationMemoryManager` - Manages conversation context
- `PortfolioMemoryManager` - Tracks portfolio history
- `ResearchMemoryManager` - Tracks research activities
- `MemoryConsolidator` - Consolidates memories into insights

### 5. Watchlist Intelligence

**File**: `AI/learning/watchlist_intelligence.py`

**AI-Generated Watchlist Categories**:
- Waiting for Better Valuation
- Waiting for Earnings
- Waiting for Breakout
- Waiting for Macro Improvement
- Waiting for Competitor Update
- Waiting for Technical Confirmation

**Monitoring**:
- Price changes
- Volume spikes
- Financial statements
- News
- Macroeconomic events
- Sector performance
- Competitor announcements

**Classes**:
- `WatchlistIntelligence` - Creates and monitors intelligent watchlists
- `AutonomousMonitor` - Continuous portfolio and market monitoring

### 6. Model Drift Detection

**File**: `AI/learning/drift_detector.py`

**Five Types of Drift**:
1. **Data Drift** - Feature distribution changes (KS test)
2. **Concept Drift** - Prediction-error distribution changes
3. **Feature Drift** - Individual feature changes
4. **Performance Drift** - Metric degradation
5. **Prediction Drift** - Prediction distribution changes

**Severity Levels**: LOW, MEDIUM, HIGH, CRITICAL

**Recommendations**:
- CRITICAL: Immediate action, flag model, initiate retraining
- HIGH: Urgent review, schedule candidate training
- MEDIUM: Monitor and prepare for retraining
- LOW: Continue monitoring

**Class**: `DriftDetector`

### 7. Explainability Engine

**File**: `AI/learning/explainability_engine.py`

**Every recommendation explains**:
- Business Quality (revenue growth, profit margins, ROE)
- Financial Health (debt-to-equity, free cash flow, current ratio)
- Technical Trend (moving averages, RSI, MACD)
- Macroeconomic Factors (interest rates, inflation, GDP)
- News Impact (recent news sentiment)
- Competitor Position (market share, advantages)
- Risk Factors (identified risks)
- Intrinsic Value (DCF analysis, upside potential)

**SHAP Explanations**:
- Top positive features
- Top negative features
- Feature importance

**Scenario Analysis**:
- Bull Case (25% probability)
- Base Case (50% probability)
- Bear Case (25% probability)
- Expected CAGR and risk metrics

**Confidence Score** (weighted):
- Model Agreement (25%)
- Data Completeness (20%)
- Prediction Stability (20%)
- Market Volatility (15%, inverted)
- Historical Accuracy (20%)

**Class**: `ExplainabilityEngine`

### 8. Learning Pipeline

**File**: `AI/learning/learning_pipeline.py`

**10-Stage Pipeline**:

1. **Recommendation** - Generate with RLHF adjustments
2. **User Decision** - Capture user feedback
3. **Store Feedback** - Persist to database
4. **Evaluate Result** - Calculate actual returns
5. **Reward Calculation** - Compute reward signals
6. **Candidate Training** - Train candidate model (never touches production)
7. **Validation** - Validate candidate model
8. **Backtesting** - Walk-forward validation
9. **Human Approval** - Require human approval
10. **Production Deployment** - Deploy only after approval

**Learning Schedule**:
- **Daily**: Collect feedback, process feedback batch
- **Weekly**: Evaluate feedback, generate candidate model, drift detection
- **Monthly**: Retrain model, performance review
- **Quarterly**: Comprehensive review, archive old models

**Classes**:
- `LearningPipeline` - Orchestrates the complete workflow
- `LearningScheduler` - Manages scheduled tasks
- `PipelineConfig` - Configuration parameters

### 9. Audit Logging

**File**: `AI/learning/audit_logger.py`

**Logged Actions**:
- PREDICTION
- RECOMMENDATION
- EXPLANATION
- FEEDBACK_RECEIVED
- MODEL_TRAINED
- MODEL_DEPLOYED
- MODEL_ARCHIVED
- DRIFT_DETECTED
- CANDIDATE_CREATED
- REWARD_CALCULATED
- RLHF_UPDATED

**Features**:
- Queryable by model version, user, symbol, action type, date range
- Export to JSON/CSV
- Statistics and analytics
- Automatic cleanup of old entries

**Class**: `AuditLogger`

## Usage

### Basic Usage

```python
from AI.learning.learning_pipeline import LearningPipeline, PipelineConfig
from AI.learning.rlhf import RLHFTrainer
from AI.learning.memory_systems import ConversationMemoryManager

# Initialize pipeline
config = PipelineConfig(
    feedback_batch_size=100,
    retrain_frequency_days=30,
    min_feedback_for_retrain=50
)
pipeline = LearningPipeline(config)

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

# Stage 2: Capture user decision
feedback = pipeline.stage_user_decision({
    "user_id": 1,
    "symbol": "AAPL",
    "action": "ACCEPTED",
    "feedback_type": "BUY_ACCEPTED"
})

# Stage 3-5: Store, evaluate, calculate reward
stored = pipeline.stage_store_feedback(feedback)
evaluation = pipeline.stage_evaluate_result({
    "symbol": "AAPL",
    "price_before": 150.0,
    "price_after": 165.0
})
reward_data = pipeline.stage_reward_calculation(evaluation)

# Process batch
result = pipeline.process_feedback_batch()
```

### RLHF Usage

```python
from AI.learning.rlhf import RLHFTrainer

# Initialize trainer
rlhf = RLHFTrainer()

# Record feedback
rlhf.record_feedback(user_id=1, {
    "feedback_type": "AGREE",
    "symbol": "AAPL",
    "sector": "Technology",
    "company": "Apple Inc."
})

# Update adjustments
rlhf.update_user_adjustments(
    user_id=1,
    reward_signal=0.8,
    feedback_data={"sector": "Technology", "company": "AAPL"}
)

# Apply to recommendation
result = rlhf.apply_rlhf_to_recommendation(
    user_id=1,
    base_score=70.0,
    sector="Technology",
    company="AAPL",
    strategy_type="growth"
)
# result['adjusted_score'] will be boosted based on user preferences
```

### Memory Systems Usage

```python
from AI.learning.memory_systems import (
    ConversationMemoryManager,
    PortfolioMemoryManager,
    ResearchMemoryManager
)

# Conversation memory
conv_mgr = ConversationMemoryManager()
memory = conv_mgr.store_memory(
    user_id=1,
    session_id="session123",
    memory_type="RESEARCH_TOPIC",
    entities=["AAPL", "Apple"],
    summary="User researched Apple stock",
    key_points=["Strong revenue growth"]
)
relevant = conv_mgr.retrieve_relevant_memories(
    user_id=1,
    query_entities=["AAPL"]
)

# Portfolio memory
port_mgr = PortfolioMemoryManager()
snapshot = port_mgr.record_portfolio_snapshot(
    user_id=1,
    holdings=[{"symbol": "AAPL", "qty": 10, "avg_price": 150.0, "current_value": 2000.0}]
)
metrics = port_mgr.calculate_portfolio_metrics(user_id=1)

# Research memory
research_mgr = ResearchMemoryManager()
activity = research_mgr.record_research_activity(
    user_id=1,
    activity_type="COMPANY_ANALYZED",
    symbol="AAPL",
    company_name="Apple Inc."
)
```

### Drift Detection Usage

```python
from AI.learning.drift_detector import DriftDetector
import pandas as pd
import numpy as np

# Initialize detector
detector = DriftDetector()

# Set reference data (from training)
ref_features = pd.DataFrame({'feature1': np.random.randn(100)})
ref_preds = np.random.randn(100)
detector.set_reference_data(ref_features, ref_preds, {'accuracy': 0.85})

# Run drift detection
results = detector.comprehensive_drift_check(
    current_features=pd.DataFrame({'feature1': np.random.randn(100)}),
    current_predictions=np.random.randn(100),
    current_actuals=np.random.randn(100),
    current_metrics={'accuracy': 0.85}
)

if results['drift_detected']:
    print(f"Drift detected! Severity: {results['overall_severity']}")
    print(f"Recommendation: {results['recommendation']}")
```

### Explainability Usage

```python
from AI.learning.explainability_engine import ExplainabilityEngine

engine = ExplainabilityEngine()

# Generate explanation
explanation = engine.generate_explanation(
    symbol="AAPL",
    company_name="Apple Inc.",
    investment_score=85.0,
    confidence=0.9,
    shap_values={"revenue_growth": 0.3, "profit_margin": 0.2},
    fundamental_data={"revenue_growth": 0.18, "profit_margin": 0.22},
    technical_data={"sma_20": 175.0, "current_price": 180.0, "rsi": 55.0},
    sentiment_data={},
    macro_data={"interest_rate": 4.5, "inflation": 3.0},
    news_data=[],
    competitor_data={"market_share": 0.25},
    risk_factors=["Market volatility"],
    intrinsic_value={"dcf_value": 200.0, "current_price": 180.0}
)

# Generate scenario analysis
scenarios = engine.generate_scenario_analysis(
    symbol="AAPL",
    company_name="Apple Inc.",
    current_price=180.0,
    intrinsic_value=200.0,
    volatility=0.25
)

# Calculate confidence
confidence = engine.calculate_confidence_score(
    model_agreement=0.8,
    data_completeness=0.9,
    prediction_stability=0.75,
    market_volatility=0.3,
    historical_accuracy=0.85
)
```

### Audit Logging Usage

```python
from AI.learning.audit_logger import AuditLogger, AuditActionType

logger = AuditLogger()

# Log various actions
logger.log_prediction("v1.0", "AAPL", {"score": 75.0}, user_id=1)
logger.log_recommendation("v1.0", "AAPL", {"score": 85.0}, user_id=1)
logger.log_feedback("v1.0", "AAPL", {"action": "ACCEPTED"}, user_id=1)
logger.log_model_trained("v2.0", {"dataset_version": "v1"}, {"accuracy": 0.85})
logger.log_model_deployed("v2.0", deployed_by="admin")

# Query audit trail
trail = logger.get_audit_trail(user_id=1, symbol="AAPL")

# Get statistics
stats = logger.get_audit_statistics()

# Export for compliance
export = logger.export_audit_log(format='json')
```

## Testing

Run comprehensive tests:

```bash
python -m unittest tests.test_learning_engine -v
```

**Test Coverage**:
- Feedback processing
- Reward calculation (positive/negative)
- RLHF system
- Adaptive learning
- Memory systems (conversation, portfolio, research)
- Watchlist intelligence
- Drift detection
- Explainability engine
- Learning pipeline
- Audit logging
- Integration tests (complete workflow)

## Safety Guarantees

1. **No Immediate Retraining** - Follows scheduled approach (daily/weekly/monthly/quarterly)
2. **No Production Model Modification During Inference** - Separate candidate training
3. **Human Approval Required** - All deployments require human approval
4. **Full Audit Trail** - Every action is logged
5. **Model Versioning** - Complete version history with promotion protocol
6. **Drift Detection** - Automatic detection of model degradation
7. **Explainability** - Every recommendation is fully explained
8. **Privacy** - User memory is never exposed to other users

## Performance Metrics

Tracked metrics:
- Prediction Accuracy
- Precision
- Recall
- F1 Score
- RMSE
- Sharpe Ratio
- Win Rate
- Average Return
- Maximum Drawdown

## Success Criteria

The Learning Engine is successful if:
- ✅ Recommendation quality improves over time
- ✅ User satisfaction increases
- ✅ Portfolio risk decreases
- ✅ Explainability remains transparent
- ✅ Models remain reproducible
- ✅ Production remains stable

## Dependencies

- numpy
- pandas
- scipy
- dataclasses (Python 3.7+)
- typing (Python 3.5+)
- Django (for models only, AI components are standalone)

## Integration with Backend

The Django models in `backend/apps/feedback/models.py` provide persistent storage for:
- Feedback records
- User preference profiles
- Memory systems
- Watchlists
- Performance metrics
- Audit logs
- Alerts

These models integrate with the standalone AI components through Django services/views.