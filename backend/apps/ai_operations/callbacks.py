import time
from langchain_core.callbacks import BaseCallbackHandler
from .models import LLMTelemetry

class DjangoTelemetryCallback(BaseCallbackHandler):
    def __init__(self, agent_name="General Agent"):
        self.agent_name = agent_name
        self.start_time = None

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.start_time = time.time()

    def on_llm_end(self, response, **kwargs):
        latency = (time.time() - self.start_time) * 1000 if self.start_time else 0
        
        token_usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        total_tokens = token_usage.get("total_tokens", 0)
        
        # Approximate Cost Calculation for Gemini 1.5 Pro
        cost = (prompt_tokens / 1_000_000 * 1.25) + (completion_tokens / 1_000_000 * 5.00)

        LLMTelemetry.objects.create(
            agent_name=self.agent_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency,
            cost=cost,
            status="Success"
        )

    def on_llm_error(self, error, **kwargs):
        latency = (time.time() - self.start_time) * 1000 if self.start_time else 0
        LLMTelemetry.objects.create(
            agent_name=self.agent_name,
            latency_ms=latency,
            status="Failed",
            error_message=str(error)
        )