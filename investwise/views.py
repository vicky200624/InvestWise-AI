import base64
import os
import json
from deepgram import DeepgramClient
from dotenv import load_dotenv

import requests
import yfinance as yf
import pyotp
from SmartApi import SmartConnect
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from google import genai
from .models import (
    BrokerCredentials, AssetHolding, ChatSession, ChatMessage,
    StockAnalysis, AgentTask, InvestmentFeedback,
)

from django.core.files.storage import FileSystemStorage
import google.generativeai as genai
from elevenlabs.client import ElevenLabs

load_dotenv()

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def get_user_live_holdings(user):
    try:
        creds = BrokerCredentials.objects.get(user=user)
        if not (creds.api_key and creds.client_id):
            return []
            
        if creds.broker_name == 'ANGELONE':
            smartApi = SmartConnect(api_key=creds.api_key)
            totp = pyotp.TOTP(creds.totp_secret).now()
            login_res = smartApi.generateSession(creds.client_id, creds.pin, totp)
            if login_res.get('status'):
                holdings = smartApi.holding()
                return holdings.get('data', [])
            else:
                print(f"Angel One Login Failed: {login_res.get('message')}")
                return []
        return []
    except BrokerCredentials.DoesNotExist:
        return []
    except Exception as e:
        print(f"Error fetching holdings: {e}")
        return []

def get_live_prices(ticker_list):
    if not ticker_list:
        return {}
    try:
        data = yf.download(" ".join(ticker_list), period="1d", group_by='ticker', progress=False)
        prices = {}
        for ticker in ticker_list:
            try:
                if len(ticker_list) == 1:
                    prices[ticker] = round(float(data['Close'].iloc[-1]), 2)
                else:
                    prices[ticker] = round(float(data[ticker]['Close'].iloc[-1]), 2)
            except Exception:
                prices[ticker] = 0.0 # Fallback 
        return prices
    except Exception as e:
        print(f"Error fetching yfinance data: {e}")
        return {t: 0 for t in ticker_list}

# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'investwise/login.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('login')
            
        user = User.objects.create_user(username=email, email=email, password=password)
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        user.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'investwise/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ==============================================================================
# BROKER SETUP & DASHBOARD VIEWS
# ==============================================================================
@login_required(login_url='login')
def connect_broker_view(request):
    creds, _ = BrokerCredentials.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        creds.broker_name = request.POST.get('broker_name', 'ANGELONE')
        creds.api_key = request.POST.get('api_key', '').strip()
        creds.client_id = request.POST.get('client_id', '').strip()
        creds.pin = request.POST.get('pin', '').strip()
        creds.totp_secret = request.POST.get('totp_secret', '').strip()
        creds.save()
        messages.success(request, f"{creds.get_broker_name_display()} credentials saved!")
        return redirect('dashboard')
    return render(request, 'investwise/connect_broker.html', {'creds': creds})

# ==============================================================================
# BROKER SETUP & DASHBOARD VIEWS
# ==============================================================================
@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    
    # 1. Fetch live data from Broker
    has_broker = BrokerCredentials.objects.filter(user=user).exists()
    live_holdings = get_user_live_holdings(user) if has_broker else []
    
    # 2. Equity Stocks Calculation
    stocks_current_value = 0.0
    stocks_invested_value = 0.0
    holdings_count = len(live_holdings) if live_holdings else 0
    
    for item in live_holdings:
        qty = float(item.get('quantity', 0))
        ltp = float(item.get('ltp', 0))
        avg_price = float(item.get('averageprice', 0))
        stocks_current_value += (qty * ltp)
        stocks_invested_value += (qty * avg_price)

    # 3. Dynamic Manual Holdings (MF, Gold, REITs)
    manual_holdings = AssetHolding.objects.filter(user=user)
    symbols = [h.symbol for h in manual_holdings if h.symbol]
    live_prices = get_live_prices(symbols) if symbols else {}

    mf_total, gold_total, reits_total = 0.0, 0.0, 0.0
    mf_invested, gold_invested, reits_invested = 0.0, 0.0, 0.0
    mf_count, gold_qty, reits_count = 0, 0.0, 0

    for h in manual_holdings:
        ltp = live_prices.get(h.symbol, h.avg_price)
        current_val = h.qty * ltp
        invested_val = h.qty * h.avg_price
        
        if h.asset_type == 'MF':
            mf_total += current_val
            mf_invested += invested_val
            mf_count += 1
        elif h.asset_type == 'GOLD':
            gold_total += current_val
            gold_invested += invested_val
            gold_qty += h.qty
        elif h.asset_type == 'REIT':
            reits_total += current_val
            reits_invested += invested_val
            reits_count += 1

    total_pnl = stocks_current_value - stocks_invested_value
    pnl_percentage = (total_pnl / stocks_invested_value * 100) if stocks_invested_value > 0 else 0.0
    
    total_net_worth = stocks_current_value + mf_total + gold_total + reits_total
    total_invested_worth = stocks_invested_value + mf_invested + gold_invested + reits_invested

    # Health Score
    health_score = 50 
    if stocks_invested_value > 0: health_score = 70
    if pnl_percentage > 0: health_score += min(20, int(pnl_percentage))
    else: health_score -= min(20, abs(int(pnl_percentage)))
    if mf_total > 0: health_score += 5
    if gold_total > 0: health_score += 5
    health_score = max(0, min(100, health_score))

    context = {
        'has_broker_connected': has_broker,
        'total_value': f"{total_net_worth:,.2f}",
        'total_invested': f"{total_invested_worth:,.2f}",
        'total_pnl': f"{total_pnl:+,.2f}",
        'pnl_percentage': f"{pnl_percentage:+.2f}",
        'is_positive': total_pnl >= 0,
        'holdings_count': holdings_count,
        'mf_count': mf_count,
        'gold_qty': int(gold_qty),
        'reits_count': reits_count,
        'health_score': health_score,
        'personal_values': {
            'stocks': f"{stocks_current_value:,.2f}",
            'stocks_invested': f"{stocks_invested_value:,.2f}",
            'mutual_funds': f"{mf_total:,.2f}",
            'mf_invested': f"{mf_invested:,.2f}",
            'gold': f"{gold_total:,.2f}",
            'gold_invested': f"{gold_invested:,.2f}",
            'reits': f"{reits_total:,.2f}",
            'reits_invested': f"{reits_invested:,.2f}"
        }
    }
    return render(request, 'investwise/dashboard.html', context)

# ==============================================================================
# INDIVIDUAL ASSET VIEWS
# ==============================================================================
@login_required(login_url='login')
def stocks_view(request):
    user = request.user
    has_broker = BrokerCredentials.objects.filter(user=user).exists()
    live_holdings = get_user_live_holdings(user) if has_broker else []
    
    total_current = 0.0
    total_invested = 0.0
    portfolio = []
    
    if live_holdings:
        for item in live_holdings:
            qty = float(item.get('quantity', 0))
            ltp = float(item.get('ltp', 0))
            avg_price = float(item.get('averageprice', 0))
            
            total_current += (qty * ltp)
            total_invested += (qty * avg_price)
            ret_pct = ((ltp - avg_price) / avg_price * 100) if avg_price > 0 else 0
            
            portfolio.append({
                'code': item.get('tradingsymbol', 'NA')[:2],
                'name': item.get('tradingsymbol', 'Unknown'),
                'qty': qty,
                'avg_price': avg_price,
                'ltp': ltp,
                'is_profit': ret_pct >= 0,
                'return_pct': round(ret_pct, 2)
            })
            
    total_profit = total_current - total_invested
    total_profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0.0
    
    context = {
        'portfolio': portfolio,
        'total_current': f"{total_current:,.2f}",
        'total_invested': f"{total_invested:,.2f}",
        'total_profit': f"{abs(total_profit):,.2f}",
        'total_profit_pct': f"{abs(total_profit_pct):.2f}",
        'is_total_profit': total_profit >= 0,
    }
    return render(request, 'investwise/stocks.html', context)

@login_required(login_url='login')
def mf_view(request):
    holdings = AssetHolding.objects.filter(user=request.user, asset_type='MF')
    portfolio = [{'symbol': h.symbol, 'name': h.name, 'code': h.code, 'qty': h.qty, 'avg_price': h.avg_price} for h in holdings]
    
    live_prices = get_live_prices([item['symbol'] for item in portfolio])
    total_current = 0.0
    total_invested = 0.0
    
    for item in portfolio:
        item['ltp'] = live_prices.get(item['symbol'], item['avg_price'])
        item['current_value'] = item['qty'] * item['ltp']
        item['invested_value'] = item['qty'] * item['avg_price']
        total_current += item['current_value']
        total_invested += item['invested_value']

    context = {
        'portfolio': portfolio, 
        'total_current': f"{total_current:,.2f}",
        'total_invested': f"{total_invested:,.2f}"
    }
    return render(request, 'investwise/mutual_funds.html', context)

@login_required(login_url='login')
def gold_view(request):
    holdings = AssetHolding.objects.filter(user=request.user, asset_type='GOLD')
    portfolio = [{'symbol': h.symbol, 'name': h.name, 'code': h.code, 'qty': h.qty, 'avg_price': h.avg_price} for h in holdings]
    
    live_prices = get_live_prices([item['symbol'] for item in portfolio])
    total_current = 0.0
    total_invested = 0.0
    
    for item in portfolio:
        item['ltp'] = live_prices.get(item['symbol'], item['avg_price'])
        total_current += item['qty'] * item['ltp']
        total_invested += item['qty'] * item['avg_price']

    context = {
        'portfolio': portfolio, 
        'total_current': f"{total_current:,.2f}",
        'total_invested': f"{total_invested:,.2f}"
    }
    return render(request, 'investwise/gold.html', context)

@login_required(login_url='login')
def reits_view(request):
    holdings = AssetHolding.objects.filter(user=request.user, asset_type='REIT')
    portfolio = [{'symbol': h.symbol, 'name': h.name, 'code': h.code, 'qty': h.qty, 'avg_price': h.avg_price} for h in holdings]
    
    live_prices = get_live_prices([item['symbol'] for item in portfolio])
    total_current = 0.0
    total_invested = 0.0
    
    for item in portfolio:
        item['ltp'] = live_prices.get(item['symbol'], item['avg_price'])
        total_current += item['qty'] * item['ltp']
        total_invested += item['qty'] * item['avg_price']

    context = {
        'portfolio': portfolio, 
        'total_current': f"{total_current:,.2f}",
        'total_invested': f"{total_invested:,.2f}"
    }
    return render(request, 'investwise/reits.html', context)

# ==============================================================================
# AI ADVISOR & TTS API ENDPOINTS
# ==============================================================================
# (Your AI endpoints remain identical here)

# ==============================================================================
# AI ADVISOR & TTS API ENDPOINTS
@csrf_exempt
def ai_advisor_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '')

            if not user_query:
                return JsonResponse({'error': 'Query cannot be empty'}, status=400)

            # 1. PASTE YOUR NEW KEY DIRECTLY HERE FOR TESTING
            client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
            
            system_context = (
                "You are the InvestWise AI Advisor. Provide smart, safe, "
                "and SEBI-compliant investment guidance for retail investors. "
                "Keep answers highly concise (under 2 sentences) for speech synthesis. User query: "
            )
            
            # --- USE THE 2.5 FLASH MODEL FROM YOUR LIST ---
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=system_context + user_query
            )
            # ----------------------------------------------
            return JsonResponse({'status': 'success', 'response': response.text})

        except Exception as e:
            error_message = str(e)
            
            # 2. PRINT THE ERROR TO THE TERMINAL SO WE CAN SEE IT
            print("\n=== GEMINI API ERROR ===")
            print(error_message)
            print("========================\n")
            
            if '429' in error_message or 'RESOURCE_EXHAUSTED' in error_message:
                fallback_text = (
                    "InvestWise AI is currently experiencing high traffic. "
                    "However, looking at your current allocation, consider diversifying into Sovereign Gold Bonds to balance your equity exposure."
                )
                return JsonResponse({'status': 'success', 'response': fallback_text})
                
            return JsonResponse({'error': error_message}, status=500)
            
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '')

            if not user_query:
                return JsonResponse({'error': 'Query cannot be empty'}, status=400)

            client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
            
            system_context = (
                "You are the InvestWise AI Advisor. Provide smart, safe, "
                "and SEBI-compliant investment guidance for retail investors. "
                "Keep answers highly concise (under 2 sentences) for speech synthesis. User query: "
            )
            
            response = client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=system_context + user_query
            )
            
            return JsonResponse({'status': 'success', 'response': response.text})

        except Exception as e:
            error_message = str(e)
            
            # If we hit a Rate Limit (429), return a graceful fallback response
            if '429' in error_message or 'RESOURCE_EXHAUSTED' in error_message:
                fallback_text = (
                    "InvestWise AI is currently experiencing high traffic. "
                    "However, looking at your current allocation, consider diversifying into Sovereign Gold Bonds to balance your equity exposure."
                )
                return JsonResponse({'status': 'success', 'response': fallback_text})
                
            # If it's a 404 or other error, return the actual error
            return JsonResponse({'error': error_message}, status=500)
            
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
from gtts import gTTS
import io
@csrf_exempt
def tts_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            if not text:
                return JsonResponse({'error': 'Text cannot be empty'}, status=400)
                
            # Generate Speech using free Google TTS
            tts = gTTS(text=text, lang='en')
            
            # Save to an in-memory file instead of a real file
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)

            # Return the audio file directly to the browser
            return HttpResponse(audio_fp.read(), content_type='audio/mpeg')
            
        except Exception as e:
            print(f"TTS Error: {str(e)}") # Prints the exact error in your terminal if it fails
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@login_required(login_url='login')
def user_manual_view(request):
    """Renders a clean, print-friendly user manual for PDF export."""
    return render(request, 'investwise/user_manual.html')

import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
# Global variable to cache the vector database in memory
_VECTOR_STORE = None

def get_vector_store():
    """Initializes and caches the local FAISS vector database."""
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        documents = [
            Document(page_content="InvestWise strongly recommends Sovereign Gold Bonds (SGBs) because they offer a 2.5% annual interest rate on top of capital appreciation, and they are tax-free if held to maturity."),
            Document(page_content="Angel One is the primary broker for InvestWise. To sync it, users must generate a TOTP secret using a third-party authenticator application."),
            Document(page_content="For Equity portfolios with a Health Score below 60, InvestWise algorithms suggest rebalancing into Midcap Mutual Funds to distribute risk.")
        ]
        
        # --- CHANGE THE MODEL NAME RIGHT HERE ---
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        # ----------------------------------------
        
        _VECTOR_STORE = FAISS.from_documents(documents, embeddings)
        
    return _VECTOR_STORE
from django.db.models import Q
from .models import BrokerCredentials, ChatSession, ChatMessage


@login_required(login_url='login')
def chat_ui_view(request, session_id=None):
    """Renders the chat UI. If no session is provided, it stays completely blank."""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    
    current_session = None
    messages_list = []

    if session_id:
        try:
            current_session = ChatSession.objects.get(id=session_id, user=request.user)
            messages_list = ChatMessage.objects.filter(session=current_session).order_by('timestamp')
        except ChatSession.DoesNotExist:
            return redirect('chat')
            
    # WE REMOVED the 'elif' block here so it doesn't auto-load old chats!

    context = {
        'sessions': sessions,
        'current_session': current_session,
        'chat_messages': messages_list,
    }
    return render(request, 'investwise/chat.html', context)

@login_required(login_url='login')
def delete_chat_session(request, session_id):
    """Deletes the specific chat and returns to a blank screen."""
    ChatSession.objects.filter(id=session_id, user=request.user).delete()
    return redirect('chat')
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    
    current_session = None
    messages_list = []

    if session_id:
        try:
            current_session = ChatSession.objects.get(id=session_id, user=request.user)
            messages_list = ChatMessage.objects.filter(session=current_session).order_by('timestamp')
        except ChatSession.DoesNotExist:
            return redirect('chat')
    elif sessions.exists():
        current_session = sessions.first()
        messages_list = ChatMessage.objects.filter(session=current_session).order_by('timestamp')

    context = {
        'sessions': sessions,
        'current_session': current_session,
        'chat_messages': messages_list,
    }
    return render(request, 'investwise/chat.html', context)

@login_required(login_url='login')
def new_chat_session(request):
    """Redirects to a clean, empty chat interface."""
    return redirect('chat')
@csrf_exempt
@login_required(login_url='login')
def langchain_chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            session_id = data.get('session_id')

            if not user_message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            # Get or create session
            if session_id:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            else:
                session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
                if not session:
                    session = ChatSession.objects.create(user=request.user, title="New Conversation")

            # Update session title if it's the first message
            if session.title == "New Conversation":
                session.title = user_message[:25] + "..." if len(user_message) > 25 else user_message
                session.save()

            ChatMessage.objects.create(session=session, user=request.user, role='user', content=user_message)

            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
            vector_store = get_vector_store()
            retriever = vector_store.as_retriever(search_kwargs={"k": 2})

            recent_history = ChatMessage.objects.filter(session=session).order_by('-timestamp')[1:7]
            formatted_history = "".join([f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}\n" for m in reversed(recent_history)])

            system_prompt = (
                "You are the InvestWise AI Assistant, a helpful financial expert.\n"
                "Use the retrieved context or general knowledge to answer. Keep answers concise.\n"
                "If the user asks to connect a broker, include: <a href='/connect-broker/' class='text-purple-400 font-bold underline'>Click here to Connect Broker</a>\n"
                "If the user asks to see their dashboard, include: <a href='/dashboard/' class='text-purple-400 font-bold underline'>Go to Dashboard</a>\n\n"
                "Conversation History:\n{history}\n\nContext: {context}"
            )
            
            prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
            rag_chain = (
                {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)), "history": lambda x: formatted_history, "input": RunnablePassthrough()}
                | prompt | llm | StrOutputParser()
            )

            response = rag_chain.invoke(user_message)
            ChatMessage.objects.create(session=session, user=request.user, role='ai', content=response)

            return JsonResponse({'status': 'success', 'response': response, 'session_id': session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)


    """Processes RAG requests, integrates long-term DB memory, and saves history."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            # 1. Save User Message to Database
            ChatMessage.objects.create(user=request.user, role='user', content=user_message)

            # 2. Setup Model & Retriever
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
            vector_store = get_vector_store()
            retriever = vector_store.as_retriever(search_kwargs={"k": 2})

            # 3. Fetch past context from Database for Memory
            recent_history = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[1:7]
            formatted_history = ""
            for msg in reversed(recent_history):
                role = "User" if msg.role == 'user' else "Assistant"
                formatted_history += f"{role}: {msg.content}\n"

            # 4. System Prompt with Smart Routing Links
            system_prompt = (
                "You are the InvestWise AI Assistant, a helpful financial expert.\n"
                "Use the retrieved context or general knowledge to answer. Keep answers concise.\n"
                "If the user asks to connect a broker, include: <a href='/connect-broker/' class='text-purple-600 font-bold underline'>Click here to Connect Broker</a>\n"
                "If the user asks to see their dashboard, include: <a href='/dashboard/' class='text-purple-600 font-bold underline'>Go to Dashboard</a>\n"
                "If the user asks to see their stocks, include: <a href='/stocks/' class='text-purple-600 font-bold underline'>View My Stocks</a>\n\n"
                "Conversation History:\n{history}\n\n"
                "Context: {context}"
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])

            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            rag_chain = (
                {
                    "context": retriever | format_docs, 
                    "history": lambda x: formatted_history, 
                    "input": RunnablePassthrough()
                }
                | prompt
                | llm
                | StrOutputParser()
            )

            response = rag_chain.invoke(user_message)
            
            # 5. Save AI Response to Database
            ChatMessage.objects.create(user=request.user, role='ai', content=response)

            return JsonResponse({'status': 'success', 'response': response})

        except Exception as e:
            print(f"LangChain Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

@login_required(login_url='login')
def clear_chat_history(request):
    """Deletes all chat history for the logged-in user."""
    ChatMessage.objects.filter(user=request.user).delete()
    return redirect('chat')
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.5-flash') 
eleven_client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
deepgram_client = DeepgramClient(api_key=os.environ.get("DEEPGRAM_API_KEY")) # ADD THIS CLIENT
import os
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai  # Reverted to old import
from elevenlabs.client import ElevenLabs
from deepgram import DeepgramClient

@csrf_exempt
def voice_chat_api(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        try:
            # 1. Initialize Clients (Using your hardcoded keys)
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            gemini_model = genai.GenerativeModel('gemini-2.5-flash') # Old model initialization
            
            eleven_client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
            deepgram_client = DeepgramClient(api_key=os.environ.get("DEEPGRAM_API_KEY"))

            # 2. Read audio from RAM
            audio_bytes = request.FILES['audio'].read()
            
            # 3. Deepgram STT
            stt_response = deepgram_client.listen.v1.media.transcribe_file(
                request=audio_bytes,
                model="nova-3"
            )
            user_text = stt_response.results.channels[0].alternatives[0].transcript
            
            if not user_text.strip():
                return JsonResponse({"error": "No speech detected."}, status=400)
            
            # 4. Gemini LLM (Old generation syntax)
            llm_response = gemini_model.generate_content(user_text)
            ai_text = llm_response.text
            
            # 5. ElevenLabs TTS
            audio_generator = eleven_client.text_to_speech.convert(
                text=ai_text,
                voice_id="JBFqnCBsd6RMkjVDRZzb", 
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            
            # 6. Convert audio stream to base64
            audio_data = b"".join(chunk for chunk in audio_generator if chunk)
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return JsonResponse({
                "user_text": user_text,
                "ai_text": ai_text,
                "audio_base64": audio_base64
            })
            
        except Exception as e:
            print(f"Server Error: {str(e)}") 
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid request"}, status=400)


# ==============================================================================
# INVESTWISE AI 3.0 — ANALYSIS ENGINE VIEWS
# ==============================================================================
import logging

ai_logger = logging.getLogger('investwise')


@login_required(login_url='login')
def analysis_view(request):
    """
    Renders the AI Stock Analysis dashboard page.

    Shows:
    - Stock search with time horizon selector
    - Real-time WebSocket-driven progress indicator
    - Investment Score gauge, SHAP waterfall, cluster scores
    - Past analysis history for the user
    """
    recent_analyses = StockAnalysis.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    # Get any in-progress tasks
    pending_tasks = AgentTask.objects.filter(
        user=request.user,
        status__in=['PENDING', 'RUNNING']
    ).order_by('-created_at')[:5]

    context = {
        'recent_analyses': recent_analyses,
        'pending_tasks': pending_tasks,
    }
    return render(request, 'investwise/analysis.html', context)


@csrf_exempt
@login_required(login_url='login')
def run_analysis_api(request):
    """
    API endpoint to initiate a full AI stock analysis.

    POST /api/analysis/run/
    Body: {"symbol": "AAPL", "time_horizon": "SHORT"}

    Creates an AgentTask record and dispatches the analysis pipeline
    as a Celery async task. Returns immediately with the task_id so
    the frontend can connect via WebSocket for real-time updates.

    Returns:
        201: {"task_id": "uuid", "status": "PENDING", "ws_url": "/ws/agent/uuid/"}
        400: {"error": "..."}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').strip().upper()
        time_horizon = data.get('time_horizon', 'SHORT').upper()

        # --- Validation ---
        if not symbol:
            return JsonResponse({'error': 'Stock symbol is required'}, status=400)

        if time_horizon not in ('SHORT', 'LONG'):
            return JsonResponse(
                {'error': 'time_horizon must be SHORT or LONG'}, status=400
            )

        # --- Create AgentTask record ---
        agent_task = AgentTask.objects.create(
            user=request.user,
            task_type='full_analysis',
            input_data={
                'symbol': symbol,
                'time_horizon': time_horizon,
            },
            status='PENDING',
            current_step='Queued for analysis...',
        )

        # --- Dispatch Celery Task ---
        from investwise.tasks import run_full_analysis
        celery_result = run_full_analysis.delay(
            user_id=request.user.id,
            symbol=symbol,
            time_horizon=time_horizon,
            task_id=str(agent_task.id),
        )

        # Update with Celery task ID
        agent_task.celery_task_id = celery_result.id
        agent_task.save()

        ai_logger.info(
            f"Analysis queued: {symbol} ({time_horizon}) by {request.user.username} "
            f"| task_id={agent_task.id}"
        )

        return JsonResponse({
            'task_id': str(agent_task.id),
            'status': 'PENDING',
            'ws_url': f'/ws/agent/{agent_task.id}/',
            'symbol': symbol,
            'time_horizon': time_horizon,
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        ai_logger.error(f"Run analysis error: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required(login_url='login')
def analysis_status_api(request, task_id):
    """
    API endpoint to check the status of an analysis task.

    GET /api/analysis/status/<task_id>/

    Returns current status, progress percentage, and current step name.
    Used as a fallback for clients that can't use WebSocket.
    """
    try:
        task = AgentTask.objects.get(id=task_id, user=request.user)
        response = {
            'task_id': str(task.id),
            'status': task.status,
            'progress_percent': task.progress_percent,
            'current_step': task.current_step,
        }

        if task.status == 'COMPLETED' and task.result_data:
            response['result'] = task.result_data

        if task.status == 'FAILED':
            response['error'] = task.error_message

        return JsonResponse(response)

    except AgentTask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)


@login_required(login_url='login')
def analysis_result_api(request, analysis_id):
    """
    API endpoint to get the full result of a completed analysis.

    GET /api/analysis/result/<analysis_id>/

    Returns the complete StockAnalysis data including cluster scores,
    SHAP values, neural network prediction, and portfolio suggestion.
    """
    try:
        analysis = StockAnalysis.objects.get(id=analysis_id, user=request.user)
        return JsonResponse({
            'id': analysis.id,
            'stock_symbol': analysis.stock_symbol,
            'stock_name': analysis.stock_name,
            'time_horizon': analysis.time_horizon,
            'investment_score': analysis.investment_score,
            'confidence': analysis.confidence,
            'recommendation': analysis.recommendation,
            'cluster_scores': {
                'fundamental': analysis.fundamental_score,
                'quant': analysis.quant_score,
                'sentiment': analysis.sentiment_score,
            },
            'fundamental_data': analysis.fundamental_data,
            'quant_data': analysis.quant_data,
            'sentiment_data': analysis.sentiment_data,
            'shap_values': analysis.shap_values,
            'top_factors': analysis.top_factors,
            'nn_model_used': analysis.nn_model_used,
            'predicted_price': analysis.predicted_price,
            'current_price': analysis.current_price,
            'prediction_horizon_days': analysis.prediction_horizon_days,
            'portfolio_suggestion': analysis.portfolio_suggestion,
            'processing_time': analysis.processing_time_seconds,
            'created_at': analysis.created_at.isoformat(),
        })

    except StockAnalysis.DoesNotExist:
        return JsonResponse({'error': 'Analysis not found'}, status=404)


@csrf_exempt
@login_required(login_url='login')
def investment_feedback_api(request):
    """
    API endpoint for submitting RLHF feedback on an AI recommendation.

    POST /api/feedback/
    Body: {"analysis_id": 42, "feedback_type": "BUY_AGREE", "comment": "..."}

    Creates an InvestmentFeedback record and dispatches RLHF processing.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)
        analysis_id = data.get('analysis_id')
        feedback_type = data.get('feedback_type', '').upper()
        comment = data.get('comment', '')

        # --- Validation ---
        if not analysis_id:
            return JsonResponse({'error': 'analysis_id is required'}, status=400)

        valid_types = ['BUY_AGREE', 'HOLD_AGREE', 'SELL_AGREE', 'REJECT']
        if feedback_type not in valid_types:
            return JsonResponse(
                {'error': f'feedback_type must be one of: {valid_types}'},
                status=400
            )

        # Verify analysis belongs to user
        try:
            analysis = StockAnalysis.objects.get(
                id=analysis_id, user=request.user
            )
        except StockAnalysis.DoesNotExist:
            return JsonResponse({'error': 'Analysis not found'}, status=404)

        # Check for duplicate feedback
        existing = InvestmentFeedback.objects.filter(
            user=request.user, analysis=analysis
        ).first()
        if existing:
            return JsonResponse(
                {'error': 'Feedback already submitted for this analysis'},
                status=409
            )

        # --- Create feedback ---
        feedback = InvestmentFeedback.objects.create(
            user=request.user,
            analysis=analysis,
            feedback_type=feedback_type,
            comment=comment,
        )

        # Dispatch RLHF processing
        from investwise.tasks import process_rlhf_feedback
        process_rlhf_feedback.delay(feedback.id)

        ai_logger.info(
            f"Feedback received: {analysis.stock_symbol} | "
            f"{feedback_type} by {request.user.username}"
        )

        return JsonResponse({
            'status': 'success',
            'feedback_id': feedback.id,
            'message': 'Thank you for your feedback!',
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        ai_logger.error(f"Feedback error: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required(login_url='login')
def portfolio_optimize_api(request):
    """
    API endpoint for portfolio optimization.

    POST /api/portfolio/optimize/
    Body: {"symbols": ["AAPL", "MSFT", "GOOGL"], "method": "markowitz"}

    Runs Markowitz Mean-Variance or Black-Litterman optimization
    on the given stock symbols and returns optimal weights.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)
        symbols = data.get('symbols', [])
        method = data.get('method', 'markowitz').lower()

        if not symbols or len(symbols) < 2:
            return JsonResponse(
                {'error': 'At least 2 stock symbols are required'}, status=400
            )

        from investwise.ml.portfolio_optimizer import (
            markowitz_optimize, black_litterman_optimize
        )

        if method == 'markowitz':
            result = markowitz_optimize(symbols)
        elif method == 'black_litterman':
            views = data.get('views', {})
            confidences = data.get('confidences', [])
            market_caps = data.get('market_caps', {})
            result = black_litterman_optimize(
                symbols, market_caps, views, confidences
            )
        else:
            return JsonResponse(
                {'error': 'method must be markowitz or black_litterman'},
                status=400
            )

        if 'error' in result:
            return JsonResponse(result, status=500)

        return JsonResponse({
            'status': 'success',
            'method': method,
            **result
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        ai_logger.error(f"Portfolio optimize error: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required(login_url='login')
def analysis_history_api(request):
    """
    API endpoint for fetching past analysis results.

    GET /api/analysis/history/?symbol=AAPL&limit=10

    Returns a list of past analyses for the user, optionally filtered by symbol.
    """
    symbol = request.GET.get('symbol', '').strip().upper()
    limit = min(int(request.GET.get('limit', 20)), 50)

    analyses = StockAnalysis.objects.filter(user=request.user)
    if symbol:
        analyses = analyses.filter(stock_symbol=symbol)

    analyses = analyses.order_by('-created_at')[:limit]

    results = []
    for a in analyses:
        results.append({
            'id': a.id,
            'stock_symbol': a.stock_symbol,
            'stock_name': a.stock_name,
            'investment_score': a.investment_score,
            'recommendation': a.recommendation,
            'time_horizon': a.time_horizon,
            'confidence': a.confidence,
            'created_at': a.created_at.isoformat(),
        })

    return JsonResponse({'analyses': results})