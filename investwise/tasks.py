"""
InvestWise AI 3.0 — Celery Async Tasks

All long-running operations are dispatched as Celery tasks to avoid blocking
Django's request-response cycle. Tasks push real-time progress updates to
the frontend via Django Channels (Redis channel layer).

Task categories:
1. Full Stock Analysis — Runs the 4-cluster LangGraph orchestrator
2. Data Ingestion — SEC filing parsing and ChromaDB embedding
3. Model Training — Periodic LSTM/FNN/XGBoost retraining
4. RLHF Processing — Reward signal computation from user feedback
5. Data Refresh — Scheduled macro data and price cache updates
"""
import logging
import time
from datetime import datetime

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

logger = logging.getLogger('investwise')


def _broadcast_to_task(task_id: str, event: dict) -> None:
    """
    Helper to broadcast an event to a WebSocket channel group.

    Sends the event to all WebSocket connections subscribed to the
    'agent_{task_id}' group via the Redis channel layer.

    Args:
        task_id: UUID of the AgentTask
        event: Dict with 'type' key matching a consumer handler method name
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'agent_{task_id}',
                event
            )
    except Exception as e:
        logger.warning(f"Failed to broadcast to task {task_id}: {e}")


# =============================================================================
# TASK 1: Full Stock Analysis Pipeline
# =============================================================================

@shared_task(
    bind=True,
    name='investwise.tasks.run_full_analysis',
    max_retries=2,
    soft_time_limit=240,
    time_limit=300,
)
def run_full_analysis(self, user_id: int, symbol: str, time_horizon: str,
                      task_id: str) -> dict:
    """
    Execute the complete 4-cluster LangGraph analysis pipeline for a stock.

    This is the primary async task. It:
    1. Updates the AgentTask status to RUNNING
    2. Invokes the LangGraph orchestrator (Fundamental → Quant → Market Intel → Portfolio)
    3. Streams progress updates via WebSocket
    4. Saves the StockAnalysis result to the database
    5. Updates AgentTask status to COMPLETED

    Args:
        user_id: ID of the requesting user
        symbol: Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')
        time_horizon: 'SHORT' or 'LONG'
        task_id: UUID string of the AgentTask record

    Returns:
        Dict with analysis_id and summary scores
    """
    from investwise.models import AgentTask, StockAnalysis
    from django.contrib.auth.models import User

    start_time = time.time()

    # --- 1. Mark task as RUNNING ---
    try:
        agent_task = AgentTask.objects.get(id=task_id)
        agent_task.status = 'RUNNING'
        agent_task.celery_task_id = self.request.id
        agent_task.started_at = timezone.now()
        agent_task.current_step = 'Initializing analysis pipeline...'
        agent_task.progress_percent = 5
        agent_task.save()
    except AgentTask.DoesNotExist:
        logger.error(f"AgentTask {task_id} not found")
        return {'error': f'AgentTask {task_id} not found'}

    _broadcast_to_task(task_id, {
        'type': 'agent_progress',
        'step': 'Initializing analysis pipeline...',
        'cluster': 'orchestrator',
        'percent': 5,
    })

    try:
        # --- 2. Run the LangGraph Orchestrator ---
        from investwise.agents.orchestrator import run_analysis

        # Define a progress callback that broadcasts to WebSocket
        def progress_callback(step: str, cluster: str, percent: int,
                              detail: str = ''):
            _broadcast_to_task(task_id, {
                'type': 'agent_progress',
                'step': step,
                'cluster': cluster,
                'percent': percent,
                'detail': detail,
            })
            # Also update the DB for polling clients
            AgentTask.objects.filter(id=task_id).update(
                current_step=step,
                progress_percent=percent,
            )

        result = run_analysis(
            symbol=symbol,
            time_horizon=time_horizon,
            user_id=user_id,
            task_id=task_id,
        )

        if not result or result.get('status') == 'FAILED':
            raise Exception(
                result.get('errors', ['Unknown analysis failure'])[0]
                if result else 'Analysis returned no result'
            )

        # --- 3. Broadcast cluster completion events ---
        for cluster_name in ['fundamental', 'quant', 'sentiment']:
            score_key = f'{cluster_name}_score' if cluster_name != 'quant' \
                else 'quant_score'
            # Try to get score from the appropriate analysis data
            cluster_data_key = {
                'fundamental': 'fundamental_analysis',
                'quant': 'quant_valuation',
                'sentiment': 'market_intelligence',
            }[cluster_name]

            cluster_data = result.get(cluster_data_key, {}) or {}
            score = cluster_data.get('score', 0)

            _broadcast_to_task(task_id, {
                'type': 'agent_cluster_complete',
                'cluster': cluster_name,
                'score': score,
                'summary': cluster_data.get('summary', ''),
            })

        # --- 4. Save StockAnalysis to database ---
        user = User.objects.get(id=user_id)
        processing_time = time.time() - start_time

        fundamental_data = result.get('fundamental_analysis', {}) or {}
        quant_data = result.get('quant_valuation', {}) or {}
        sentiment_data = result.get('market_intelligence', {}) or {}
        nn_prediction = result.get('nn_prediction', {}) or {}

        analysis = StockAnalysis.objects.create(
            stock_symbol=symbol,
            stock_name=result.get('stock_name', symbol),
            user=user,
            time_horizon=time_horizon,
            investment_score=result.get('investment_score', 50.0),
            confidence=result.get('confidence', 0.5),
            recommendation=result.get('recommendation', 'HOLD'),
            fundamental_score=fundamental_data.get('score'),
            quant_score=quant_data.get('score'),
            sentiment_score=sentiment_data.get('score'),
            fundamental_data=fundamental_data,
            quant_data=quant_data,
            sentiment_data=sentiment_data,
            shap_values=result.get('shap_explanation', {}).get('shap_values'),
            top_factors=result.get('shap_explanation', {}).get('top_factors'),
            nn_model_used=nn_prediction.get('model_type', 'ENSEMBLE'),
            predicted_price=nn_prediction.get('predicted_price'),
            current_price=nn_prediction.get('current_price'),
            prediction_horizon_days=nn_prediction.get('horizon_days', 30),
            portfolio_suggestion=result.get('portfolio_suggestion'),
            processing_time_seconds=processing_time,
        )

        # --- 5. Mark task as COMPLETED ---
        agent_task.status = 'COMPLETED'
        agent_task.completed_at = timezone.now()
        agent_task.progress_percent = 100
        agent_task.current_step = 'Analysis complete'
        agent_task.result_data = {
            'analysis_id': analysis.id,
            'investment_score': analysis.investment_score,
            'recommendation': analysis.recommendation,
        }
        agent_task.save()

        # --- 6. Broadcast completion ---
        _broadcast_to_task(task_id, {
            'type': 'agent_complete',
            'analysis_id': analysis.id,
            'investment_score': analysis.investment_score,
            'recommendation': analysis.recommendation,
            'confidence': analysis.confidence,
            'cluster_scores': {
                'fundamental': analysis.fundamental_score,
                'quant': analysis.quant_score,
                'sentiment': analysis.sentiment_score,
            },
            'top_factors': analysis.top_factors or [],
            'predicted_price': analysis.predicted_price,
            'processing_time': round(processing_time, 1),
        })

        logger.info(
            f"Analysis complete: {symbol} | Score: {analysis.investment_score:.0f} | "
            f"{analysis.recommendation} | {processing_time:.1f}s"
        )

        return {
            'analysis_id': analysis.id,
            'investment_score': analysis.investment_score,
            'recommendation': analysis.recommendation,
            'processing_time': round(processing_time, 1),
        }

    except Exception as e:
        # --- Handle failure ---
        error_msg = str(e)
        logger.error(f"Analysis failed for {symbol}: {error_msg}", exc_info=True)

        AgentTask.objects.filter(id=task_id).update(
            status='FAILED',
            error_message=error_msg,
            completed_at=timezone.now(),
            current_step=f'Failed: {error_msg[:100]}',
        )

        _broadcast_to_task(task_id, {
            'type': 'agent_error',
            'message': error_msg,
            'cluster': 'orchestrator',
            'recoverable': False,
        })

        # Retry on transient errors (network timeouts, API rate limits)
        if any(keyword in error_msg.lower() for keyword in
               ['timeout', 'rate limit', '429', '503', 'connection']):
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {'error': error_msg}


# =============================================================================
# TASK 2: SEC Filing Ingestion (RAG Pipeline)
# =============================================================================

@shared_task(
    name='investwise.tasks.ingest_sec_filing',
    soft_time_limit=120,
    time_limit=180,
)
def ingest_sec_filing(symbol: str, filing_type: str = '10-K',
                      count: int = 3) -> dict:
    """
    Fetch SEC EDGAR filings, parse to text, chunk, and ingest into ChromaDB.

    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        filing_type: SEC filing type ('10-K', '10-Q', '8-K')
        count: Number of most recent filings to ingest

    Returns:
        Dict with ingested document count and total chunks
    """
    from investwise.services import sec_edgar, rag_engine
    from investwise.models import RAGDocument

    logger.info(f"Ingesting {count} {filing_type} filings for {symbol}")
    total_chunks = 0
    docs_ingested = 0

    try:
        # Resolve ticker to CIK
        cik = sec_edgar.get_cik_from_ticker(symbol)
        if not cik:
            return {'error': f'Could not resolve CIK for {symbol}'}

        # Fetch filing metadata
        filings = sec_edgar.fetch_company_filings(cik, filing_type, count)

        for filing in filings:
            try:
                # Download and parse filing text
                filing_text = sec_edgar.download_filing_text(
                    filing.get('url', '')
                )
                if not filing_text:
                    continue

                # Chunk the text
                chunks = sec_edgar.chunk_text(filing_text)
                if not chunks:
                    continue

                # Ingest into ChromaDB
                collection_name = f"sec_{symbol.lower().replace('.', '_')}"
                metadata = {
                    'symbol': symbol,
                    'filing_type': filing_type,
                    'filing_date': filing.get('filing_date', ''),
                    'source': 'SEC_EDGAR',
                }
                chunk_count = rag_engine.ingest_document(
                    chunks, metadata, collection_name
                )

                # Register in Django model
                RAGDocument.objects.create(
                    source_type=f'SEC_{filing_type.replace("-", "")}',
                    stock_symbol=symbol,
                    title=f"{symbol} {filing_type} - {filing.get('filing_date', 'Unknown')}",
                    source_url=filing.get('url', ''),
                    filing_date=filing.get('filing_date'),
                    chroma_collection=collection_name,
                    chunk_count=chunk_count,
                    file_size_bytes=len(filing_text.encode()),
                )

                total_chunks += chunk_count
                docs_ingested += 1
                logger.info(
                    f"Ingested {filing_type} for {symbol}: {chunk_count} chunks"
                )

            except Exception as e:
                logger.error(
                    f"Failed to ingest filing for {symbol}: {e}", exc_info=True
                )
                continue

    except Exception as e:
        logger.error(f"Filing ingestion failed for {symbol}: {e}", exc_info=True)
        return {'error': str(e)}

    return {
        'symbol': symbol,
        'filing_type': filing_type,
        'documents_ingested': docs_ingested,
        'total_chunks': total_chunks,
    }


# =============================================================================
# TASK 3: Model Retraining
# =============================================================================

@shared_task(
    name='investwise.tasks.retrain_models',
    soft_time_limit=600,
    time_limit=900,
)
def retrain_models(model_type: str = 'LSTM', symbol: str = None) -> dict:
    """
    Retrain ML models with latest data.

    Args:
        model_type: 'LSTM', 'GRU', 'FNN', 'XGBOOST', or 'ALL'
        symbol: Stock symbol (None for general model)

    Returns:
        Dict with training metrics
    """
    logger.info(f"Retraining {model_type} model for {symbol or 'GENERAL'}")

    results = {}

    try:
        if model_type in ('LSTM', 'GRU', 'ALL'):
            from investwise.ml.lstm_model import train_rnn_model
            rnn_type = 'LSTM' if model_type != 'GRU' else 'GRU'
            if symbol:
                results['rnn'] = train_rnn_model(symbol, model_type=rnn_type)
            else:
                logger.info("RNN models require a specific symbol")

        if model_type in ('FNN', 'ALL'):
            from investwise.ml.fnn_model import train_fnn_model
            if symbol:
                results['fnn'] = train_fnn_model(symbol)

        if model_type in ('XGBOOST', 'ALL'):
            logger.info(
                "XGBoost retraining requires labeled data from RLHF feedback"
            )

    except Exception as e:
        logger.error(f"Model retraining failed: {e}", exc_info=True)
        return {'error': str(e)}

    return results


# =============================================================================
# TASK 4: RLHF Feedback Processing
# =============================================================================

@shared_task(name='investwise.tasks.process_rlhf_feedback')
def process_rlhf_feedback(feedback_id: int) -> dict:
    """
    Process a user's investment feedback to compute the RLHF reward signal.

    The reward signal is based on:
    - Did the user agree or reject the recommendation?
    - If actual_outcome is available, was the recommendation correct?

    Reward mapping:
    - User agreed + outcome positive: +1.0
    - User agreed + outcome negative: -1.0
    - User rejected + outcome confirms rejection: +0.5
    - User rejected + outcome contradicts rejection: -0.5
    - No outcome data yet: 0.0 (neutral, will be reprocessed later)

    Args:
        feedback_id: ID of the InvestmentFeedback record

    Returns:
        Dict with computed reward signal
    """
    from investwise.models import InvestmentFeedback

    try:
        feedback = InvestmentFeedback.objects.select_related('analysis').get(
            id=feedback_id
        )

        # If we don't have outcome data yet, set neutral reward
        if feedback.actual_outcome is None:
            feedback.reward_signal = 0.0
            feedback.save()
            return {'feedback_id': feedback_id, 'reward': 0.0, 'status': 'pending_outcome'}

        # Determine if the AI's recommendation was directionally correct
        analysis = feedback.analysis
        outcome = feedback.actual_outcome  # Actual return %

        # Recommendation was correct if:
        # - BUY/STRONG_BUY and outcome > 0
        # - SELL/STRONG_SELL and outcome < 0
        # - HOLD and abs(outcome) < 5%
        rec = analysis.recommendation
        ai_was_correct = (
            (rec in ('BUY', 'STRONG_BUY') and outcome > 0) or
            (rec in ('SELL', 'STRONG_SELL') and outcome < 0) or
            (rec == 'HOLD' and abs(outcome) < 5.0)
        )

        # Compute reward signal
        user_agreed = feedback.feedback_type in (
            'BUY_AGREE', 'HOLD_AGREE', 'SELL_AGREE'
        )

        if user_agreed and ai_was_correct:
            reward = 1.0   # User trusted correct AI → reinforce
        elif user_agreed and not ai_was_correct:
            reward = -1.0  # User trusted incorrect AI → penalize
        elif not user_agreed and not ai_was_correct:
            reward = 0.5   # User correctly rejected bad AI → mild reinforce
        else:
            reward = -0.5  # User wrongly rejected good AI → mild penalize

        feedback.reward_signal = reward
        feedback.save()

        logger.info(
            f"RLHF reward computed: feedback={feedback_id}, "
            f"reward={reward}, ai_correct={ai_was_correct}, "
            f"user_agreed={user_agreed}"
        )

        return {
            'feedback_id': feedback_id,
            'reward': reward,
            'ai_was_correct': ai_was_correct,
            'user_agreed': user_agreed,
        }

    except InvestmentFeedback.DoesNotExist:
        logger.error(f"Feedback {feedback_id} not found")
        return {'error': f'Feedback {feedback_id} not found'}
    except Exception as e:
        logger.error(f"RLHF processing failed: {e}", exc_info=True)
        return {'error': str(e)}


# =============================================================================
# TASK 5: Periodic Macro Data Refresh (Celery Beat)
# =============================================================================

@shared_task(name='investwise.tasks.refresh_macro_data')
def refresh_macro_data() -> dict:
    """
    Periodic task to refresh cached macroeconomic data from FRED.

    Scheduled via Celery Beat (e.g., daily at 6:00 AM UTC).
    Fetches latest GDP, CPI, Fed Funds Rate, 10Y Treasury, Unemployment.

    Returns:
        Dict with count of records updated
    """
    from investwise.services.macro_data import cache_macro_data

    try:
        count = cache_macro_data()
        logger.info(f"Macro data refreshed: {count} records updated")
        return {'records_updated': count}
    except Exception as e:
        logger.error(f"Macro data refresh failed: {e}", exc_info=True)
        return {'error': str(e)}


# =============================================================================
# TASK 6: Outcome Tracking (Retroactive RLHF)
# =============================================================================

@shared_task(name='investwise.tasks.update_feedback_outcomes')
def update_feedback_outcomes() -> dict:
    """
    Periodic task to retroactively measure actual outcomes for past analyses.

    For each InvestmentFeedback without an actual_outcome, check if the
    prediction horizon has elapsed. If so, compute the actual return %
    and reprocess the RLHF reward signal.

    Scheduled via Celery Beat (e.g., daily).
    """
    from investwise.models import InvestmentFeedback
    from investwise.services.market_data import fetch_historical_prices

    updated = 0
    feedbacks = InvestmentFeedback.objects.filter(
        actual_outcome__isnull=True
    ).select_related('analysis')[:100]  # Process in batches

    for feedback in feedbacks:
        analysis = feedback.analysis
        days_since = (timezone.now() - analysis.created_at).days

        # Only measure outcome after prediction horizon has elapsed
        if days_since < analysis.prediction_horizon_days:
            continue

        try:
            # Fetch current price
            prices = fetch_historical_prices(
                analysis.stock_symbol, period='5d'
            )
            if prices is not None and not prices.empty:
                current = float(prices['Close'].iloc[-1])
                if analysis.current_price and analysis.current_price > 0:
                    actual_return = (
                        (current - analysis.current_price) /
                        analysis.current_price * 100
                    )
                    feedback.actual_outcome = round(actual_return, 2)
                    feedback.outcome_measured_at = timezone.now()
                    feedback.save()

                    # Reprocess RLHF reward with actual outcome
                    process_rlhf_feedback.delay(feedback.id)
                    updated += 1

        except Exception as e:
            logger.warning(
                f"Failed to update outcome for feedback {feedback.id}: {e}"
            )
            continue

    logger.info(f"Updated {updated} feedback outcomes")
    return {'outcomes_updated': updated}
