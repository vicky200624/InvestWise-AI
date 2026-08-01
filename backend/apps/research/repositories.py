from django.contrib.auth import get_user_model
User = get_user_model()
from .models import StockAnalysis, AgentTask, InvestmentFeedback

class ResearchRepository:
    @staticmethod
    def get_analyses_by_user(user: User):
        return StockAnalysis.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_tasks_by_user(user: User):
        return AgentTask.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def create_agent_task(user: User, task_type: str, **kwargs) -> AgentTask:
        return AgentTask.objects.create(user=user, task_type=task_type, **kwargs)
    
    @staticmethod
    def save_task(task: AgentTask):
        task.save()
        return task
    
    @staticmethod
    def create_analysis(user: User, **kwargs) -> StockAnalysis:
        return StockAnalysis.objects.create(user=user, **kwargs)
    
    @staticmethod
    def get_analysis_by_id(analysis_id: int) -> StockAnalysis:
        return StockAnalysis.objects.get(id=analysis_id)
    
    @staticmethod
    def create_feedback(user: User, **kwargs) -> InvestmentFeedback:
        return InvestmentFeedback.objects.create(user=user, **kwargs)
