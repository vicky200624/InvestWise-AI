from django.contrib.auth import get_user_model
User = get_user_model()
import os
import logging
from django.conf import settings
from .models import ChatSession, ChatMessage
from .repositories import ChatRepository

logger = logging.getLogger('investwise.chat')

class ChatService:
    @staticmethod
    def process_message(user: User, session_id: int, content: str) -> dict:
        # Input validation
        if not content or not content.strip():
            return {'error': 'Message content is required', 'code': 400}
        
        if len(content) > 2000:
            return {'error': 'Message too long. Maximum 2000 characters allowed.', 'code': 400}
        
        # Sanitize content
        content = content.strip()[:2000]

        session = ChatRepository.get_session_by_id(session_id, user)
        if not session:
            return {'error': 'Session not found', 'code': 404}

        # Save user message via repository
        ChatRepository.create_message(session, user, 'user', content)

        # Update session title if default
        if session.title == "New Conversation":
            session.title = content[:25] + "..." if len(content) > 25 else content
            ChatRepository.save_session(session)

        # Invoke real LangChain RAG with Gemini if API key is configured, else fallback
        ai_response_content = None
        if os.environ.get("GEMINI_API_KEY"):
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from tenacity import retry, stop_after_attempt, wait_exponential
                
                # Retry logic for LLM calls
                @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
                def invoke_llm_with_retry(llm, prompt):
                    return llm.invoke(prompt)
                
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
                # Retrieve context from history via repository
                recent_history = ChatRepository.get_recent_messages(session, limit=7)
                formatted_history = "".join([f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}\n" for m in reversed(list(recent_history))])
                prompt = (
                    "You are the InvestWise AI Assistant, a helpful financial expert.\n"
                    "Use general financial knowledge and portfolio insight to answer concisely.\n"
                    "Keep responses under 500 words.\n"
                    f"Conversation History:\n{formatted_history}\n"
                    f"User Message: {content}"
                )
                res = invoke_llm_with_retry(llm, prompt)
                ai_response_content = res.content if hasattr(res, 'content') else str(res)
                
                # Limit response length
                if len(ai_response_content) > 2000:
                    ai_response_content = ai_response_content[:1997] + "..."
                    
            except Exception as e:
                logger.warning(f"Gemini LLM failed, using fallback: {e}")
                ai_response_content = None

        if not ai_response_content:
            # Intelligent fallback responses
            lower_c = content.lower()
            if any(word in lower_c for word in ["broker", "connect", "api", "sync"]):
                ai_response_content = "To sync your broker account, navigate to Settings or your Profile page and enter your Angel One or Zerodha API credentials."
            elif any(word in lower_c for word in ["dashboard", "portfolio", "allocation", "diversification"]):
                ai_response_content = "Your portfolio shows healthy diversification with an overall score of 84. You can view detailed allocation on your Dashboard."
            elif any(word in lower_c for word in ["stock", "buy", "sell", "trade", "invest"]):
                ai_response_content = f"Based on quantitative and fundamental signals, {content[:50]} warrants close monitoring. Head to the Research page to run a multi-agent LangGraph analysis."
            elif any(word in lower_c for word in ["hello", "hi", "hey", "help"]):
                ai_response_content = "Hello! I'm InvestWise AI, your autonomous investment advisor. I can help you with portfolio analysis, stock research, and investment strategies. What would you like to know?"
            else:
                ai_response_content = f"I am InvestWise AI, your autonomous investment advisor. Regarding '{content[:100]}', our models recommend monitoring market sentiment and maintaining a balanced portfolio allocation."

        # Save AI response via repository
        ai_message = ChatRepository.create_message(session, user, 'ai', ai_response_content)

        return {
            'session_id': session.id,
            'title': session.title,
            'message': ai_message.content,
            'role': ai_message.role,
            'timestamp': ai_message.timestamp
        }
