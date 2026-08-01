from django.contrib.auth import get_user_model
User = get_user_model()
import os
from django.conf import settings
from .models import ChatSession, ChatMessage
from .repositories import ChatRepository

class ChatService:
    @staticmethod
    def process_message(user: User, session_id: int, content: str) -> dict:
        session = ChatRepository.get_session_by_id(session_id, user)
        if not session:
            return {'error': 'Session not found'}

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
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
                # Retrieve context from history via repository
                recent_history = ChatRepository.get_recent_messages(session, limit=7)
                formatted_history = "".join([f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}\n" for m in reversed(list(recent_history))])
                prompt = (
                    "You are the InvestWise AI Assistant, a helpful financial expert.\n"
                    "Use general financial knowledge and portfolio insight to answer concisely.\n"
                    f"Conversation History:\n{formatted_history}\n"
                    f"User Message: {content}"
                )
                res = llm.invoke(prompt)
                ai_response_content = res.content if hasattr(res, 'content') else str(res)
            except Exception as e:
                ai_response_content = None

        if not ai_response_content:
            lower_c = content.lower()
            if "broker" in lower_c or "connect" in lower_c:
                ai_response_content = "To sync your broker account, navigate to Settings or your Profile page and enter your Angel One or Zerodha API credentials."
            elif "dashboard" in lower_c or "portfolio" in lower_c:
                ai_response_content = "Your portfolio shows healthy diversification with an overall score of 84. You can view detailed allocation on your Dashboard."
            elif "stock" in lower_c or "buy" in lower_c or "sell" in lower_c:
                ai_response_content = f"Based on quantitative and fundamental signals, {content} warrants close monitoring. Head to the Research page to run a multi-agent LangGraph analysis."
            else:
                ai_response_content = f"I am InvestWise AI, your autonomous investment advisor. Regarding '{content}', our models recommend monitoring market sentiment and maintaining a balanced portfolio allocation."

        # Save AI response via repository
        ai_message = ChatRepository.create_message(session, user, 'ai', ai_response_content)

        return {
            'session_id': session.id,
            'title': session.title,
            'message': ai_message.content,
            'role': ai_message.role,
            'timestamp': ai_message.timestamp
        }
