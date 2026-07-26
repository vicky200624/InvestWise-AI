import os
import json
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

from .models import BrokerCredentials


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_user_live_holdings(user):
    """Queries DB and routes the fetch to the correct Broker API."""
    try:
        creds = BrokerCredentials.objects.get(user=user)
        
        if not (creds.api_key and creds.client_id):
            return None
        
        # --- Route based on the user's selected broker ---
        
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
                
        elif creds.broker_name == 'ZERODHA':
            print("Zerodha API integration triggered (Placeholder)")
            # You would put the kiteconnect SDK logic here later
            return []
            
        elif creds.broker_name == 'UPSTOX':
            print("Upstox API integration triggered (Placeholder)")
            return []
            
    except BrokerCredentials.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error fetching holdings: {e}")
        return []

@login_required(login_url='login')
def connect_broker_view(request):
    """Allows users to select their broker and input their keys."""
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

def get_live_prices(ticker_list):
    """Fallback fetcher for yfinance (used in individual asset pages)."""
    try:
        data = yf.download(" ".join(ticker_list), period="1d", group_by='ticker', progress=False)
        prices = {}
        for ticker in ticker_list:
            if len(ticker_list) == 1:
                prices[ticker] = round(float(data['Close'].iloc[-1]), 2)
            else:
                prices[ticker] = round(float(data[ticker]['Close'].iloc[-1]), 2)
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
# BROKER SETUP VIEW
# ==============================================================================

# ==============================================================================
# MAIN DASHBOARD VIEW
# ==============================================================================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import BrokerCredentials
from SmartApi import SmartConnect
import pyotp

# ... (Keep your get_user_live_holdings function as it is) ...

@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    
    # 1. Fetch live data from Angel One
    live_holdings = get_user_live_holdings(user)
    has_broker = BrokerCredentials.objects.filter(user=user).exists()
    
    # 2. Calculate the real totals from Angel One
    real_stocks_total = 0.0
    
    if live_holdings:
        for item in live_holdings:
            # Angel One's API uses 'quantity' and 'ltp' (Last Traded Price)
            qty = float(item.get('quantity', 0))
            ltp = float(item.get('ltp', 0))
            real_stocks_total += (qty * ltp)
            
    # 3. IF NO DATA (Empty Account), INJECT DUMMY DATA FOR UI TESTING
    if has_broker and real_stocks_total == 0:
        stocks_total = 145000.50
        mf_total = 65000.00
        gold_total = 24000.00
        reits_total = 12000.00
    else:
        # Otherwise, use the real data
        stocks_total = real_stocks_total
        mf_total = 0.0  # (You can build a DB model for this later!)
        gold_total = 0.0
        reits_total = 0.0
        
    total_net_worth = stocks_total + mf_total + gold_total + reits_total
    
    # 4. Send the formatted numbers to your HTML
    context = {
        'has_broker_connected': has_broker,
        'total_value': f"{total_net_worth:,.2f}",
        'personal_values': {
            'stocks': f"{stocks_total:,.2f}",
            'mutual_funds': f"{mf_total:,.2f}",
            'gold': f"{gold_total:,.2f}",
            'reits': f"{reits_total:,.2f}"
        }
    }
    
    return render(request, 'investwise/dashboard.html', context)


# ==============================================================================
# DETAILED ASSET VIEWS (Using yfinance fallback data)
# ==============================================================================

@login_required(login_url='login')
def stocks_view(request):
    portfolio = [
        {'symbol': 'RELIANCE.NS', 'name': 'Reliance Ind.', 'code': 'RELI', 'qty': 50, 'avg_price': 2400.00},
        {'symbol': 'TCS.NS', 'name': 'TCS', 'code': 'TCS', 'qty': 20, 'avg_price': 3500.00},
        {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank', 'code': 'HDFC', 'qty': 100, 'avg_price': 1600.00},
    ]
    
    live_prices = get_live_prices([item['symbol'] for item in portfolio])
    total_invested = 0
    total_current = 0
    
    for item in portfolio:
        item['ltp'] = live_prices.get(item['symbol'], item['avg_price'])
        item['current_value'] = item['qty'] * item['ltp']
        item['invested_value'] = item['qty'] * item['avg_price']
        item['return_pct'] = round(((item['ltp'] - item['avg_price']) / item['avg_price']) * 100, 2)
        item['is_profit'] = item['return_pct'] >= 0
        
        total_invested += item['invested_value']
        total_current += item['current_value']

    total_profit = total_current - total_invested
    total_profit_pct = round((total_profit / total_invested) * 100, 2) if total_invested > 0 else 0

    context = {
        'portfolio': portfolio,
        'total_current': f"{total_current:,.2f}",
        'total_profit': f"{total_profit:,.2f}",
        'total_profit_pct': total_profit_pct,
        'is_total_profit': total_profit >= 0,
    }
    return render(request, 'investwise/stocks.html', context)

@login_required(login_url='login')
def mf_view(request):
    portfolio = [
        {'symbol': 'MON100.NS', 'name': 'Parag Parikh Proxy', 'code': 'PP', 'qty': 1000, 'avg_price': 120.00},
        {'symbol': 'MID150BEES.NS', 'name': 'SBI Small/Mid Proxy', 'code': 'SBI', 'qty': 500, 'avg_price': 160.00},
        {'symbol': 'NIFTYBEES.NS', 'name': 'UTI Nifty 50 Index', 'code': 'UTI', 'qty': 500, 'avg_price': 250.00},
    ]
    
    live_prices = get_live_prices([item['symbol'] for item in portfolio])
    total_current = sum(item['qty'] * live_prices.get(item['symbol'], 0) for item in portfolio)

    for item in portfolio:
        item['ltp'] = live_prices.get(item['symbol'], 0)
        item['current_value'] = item['qty'] * item['ltp']

    context = {
        'portfolio': portfolio,
        'total_current': f"{total_current:,.2f}"
    }
    return render(request, 'investwise/mutual_funds.html', context)

@login_required(login_url='login')
def gold_view(request):
    live_prices = get_live_prices(['GOLDBEES.NS'])
    goldbees_ltp = live_prices.get('GOLDBEES.NS', 52.40)
    sgb_ltp = goldbees_ltp * 100 

    portfolio = [
        {'name': 'SGB 2023-24 Series I', 'code': 'SGB', 'qty': 25, 'avg_price': 5926.00, 'ltp': sgb_ltp},
        {'name': 'Nippon India Gold BeES', 'code': 'ETF', 'qty': 15, 'avg_price': 52.40, 'ltp': goldbees_ltp},
    ]
    
    total_current = sum(item['qty'] * item['ltp'] for item in portfolio)

    context = {
        'portfolio': portfolio,
        'total_current': f"{total_current:,.2f}"
    }
    return render(request, 'investwise/gold.html', context)

@login_required(login_url='login')
def reits_view(request):
    portfolio = [
        {'symbol': 'EMBASSY.NS', 'name': 'Embassy Office Parks', 'code': 'EMB', 'qty': 200, 'avg_price': 330.00},
        {'symbol': 'MINDSPACE.NS', 'name': 'Mindspace Business Parks', 'code': 'MND', 'qty': 150, 'avg_price': 315.00},
    ]
    
    live_prices = get_live_prices([item['symbol'] for item in portfolio])
    total_current = sum(item['qty'] * live_prices.get(item['symbol'], 0) for item in portfolio)

    for item in portfolio:
        item['ltp'] = live_prices.get(item['symbol'], 0)

    context = {
        'portfolio': portfolio,
        'total_current': f"{total_current:,.2f}"
    }
    return render(request, 'investwise/reits.html', context)


# ==============================================================================
# AI ADVISOR & TTS API ENDPOINTS
# ==============================================================================

@csrf_exempt
def ai_advisor_view(request):
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
                model='gemini-1.5-flash',
                contents=system_context + user_query
            )
            
            return JsonResponse({'status': 'success', 'response': response.text})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def tts_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            if not text:
                return JsonResponse({'error': 'Text cannot be empty'}, status=400)

            elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default Voice ID (Rachel)
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": elevenlabs_key
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return HttpResponse(response.content, content_type="audio/mpeg")
            else:
                return JsonResponse({'error': 'TTS generation failed'}, status=500)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@login_required(login_url='login')
def user_manual_view(request):
    """Renders a clean, print-friendly user manual for PDF export."""
    return render(request, 'investwise/user_manual.html')