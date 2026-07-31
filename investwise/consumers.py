"""
InvestWise AI 3.0 — WebSocket Consumers

Django Channels consumer for real-time streaming of AI agent analysis progress.
The frontend connects via WebSocket to receive live updates as each LangGraph
cluster processes the stock analysis.

Message types sent to client:
- agent_progress:  Step name + progress percentage (e.g., "Running FinBERT sentiment... 45%")
- agent_token:     Streaming text tokens from LLM evaluation
- agent_complete:  Final result with analysis_id and scores
- agent_error:     Error message if pipeline fails
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('investwise')


class AgentStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that streams real-time AI agent progress to the frontend.

    Connection flow:
    1. Client connects to ws://host/ws/agent/<task_id>/
    2. Consumer joins the channel group 'agent_<task_id>'
    3. Celery worker sends progress events to the group via Redis channel layer
    4. Consumer forwards events to the client as JSON WebSocket frames

    The Celery task (investwise/tasks.py) pushes messages using:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'agent_{task_id}',
            {'type': 'agent_progress', 'step': '...', 'percent': 45}
        )
    """

    async def connect(self):
        """Accept WebSocket connection and join the agent task's channel group."""
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'agent_{self.task_id}'

        # Verify user is authenticated
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            logger.warning(
                f"WebSocket connection rejected: unauthenticated user for task {self.task_id}"
            )
            await self.close()
            return

        # Join the task's channel group to receive broadcasts from Celery
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(
            f"WebSocket connected: user={user.username}, task={self.task_id}"
        )

        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'task_id': self.task_id,
            'message': 'Connected to analysis stream'
        }))

    async def disconnect(self, close_code):
        """Leave the channel group on disconnect."""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(
            f"WebSocket disconnected: task={self.task_id}, code={close_code}"
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming messages from the client.

        Currently supports:
        - {'type': 'ping'} — heartbeat to keep connection alive
        - {'type': 'cancel'} — request task cancellation
        """
        if text_data:
            try:
                data = json.loads(text_data)
                msg_type = data.get('type', '')

                if msg_type == 'ping':
                    await self.send(text_data=json.dumps({'type': 'pong'}))

                elif msg_type == 'cancel':
                    # Forward cancellation request to the Celery task
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'agent_cancel',
                            'requested_by': str(self.scope['user'].id)
                        }
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received on WebSocket: {text_data[:100]}")

    # =========================================================================
    # EVENT HANDLERS — Called when Celery pushes messages to the channel group
    # =========================================================================

    async def agent_progress(self, event):
        """
        Handle progress update from Celery worker.

        Event format:
        {
            'type': 'agent_progress',
            'step': 'Analyzing financial statements...',
            'cluster': 'fundamental',
            'percent': 25,
            'detail': 'Processing Q3 2025 income statement'
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'step': event.get('step', ''),
            'cluster': event.get('cluster', ''),
            'percent': event.get('percent', 0),
            'detail': event.get('detail', ''),
        }))

    async def agent_token(self, event):
        """
        Handle streaming text token from LLM evaluation.

        Event format:
        {
            'type': 'agent_token',
            'token': 'The company shows strong...',
            'cluster': 'fundamental'
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'token',
            'token': event.get('token', ''),
            'cluster': event.get('cluster', ''),
        }))

    async def agent_cluster_complete(self, event):
        """
        Handle completion of an individual cluster.

        Event format:
        {
            'type': 'agent_cluster_complete',
            'cluster': 'fundamental',
            'score': 72.5,
            'summary': 'Strong fundamentals with...'
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'cluster_complete',
            'cluster': event.get('cluster', ''),
            'score': event.get('score', 0),
            'summary': event.get('summary', ''),
        }))

    async def agent_complete(self, event):
        """
        Handle full analysis pipeline completion.

        Event format:
        {
            'type': 'agent_complete',
            'analysis_id': 42,
            'investment_score': 78.5,
            'recommendation': 'BUY',
            'confidence': 0.85,
            'cluster_scores': {'fundamental': 72, 'quant': 81, 'sentiment': 75},
            'top_factors': [{'name': 'ROE', 'impact': 0.15}, ...],
            'predicted_price': 185.50,
            'processing_time': 23.4
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'complete',
            'analysis_id': event.get('analysis_id'),
            'investment_score': event.get('investment_score'),
            'recommendation': event.get('recommendation'),
            'confidence': event.get('confidence'),
            'cluster_scores': event.get('cluster_scores', {}),
            'top_factors': event.get('top_factors', []),
            'predicted_price': event.get('predicted_price'),
            'processing_time': event.get('processing_time'),
        }))

    async def agent_error(self, event):
        """
        Handle error from the analysis pipeline.

        Event format:
        {
            'type': 'agent_error',
            'message': 'Failed to fetch financial data...',
            'cluster': 'fundamental',
            'recoverable': True
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': event.get('message', 'Unknown error'),
            'cluster': event.get('cluster', ''),
            'recoverable': event.get('recoverable', False),
        }))

    async def agent_cancel(self, event):
        """Handle task cancellation acknowledgment."""
        await self.send(text_data=json.dumps({
            'type': 'cancelled',
            'message': 'Analysis cancelled by user',
        }))
