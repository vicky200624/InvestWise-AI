import os
import sys
import django
from django.test import Client, TestCase
import json
import uuid

sys.path.insert(0, '/home/vicky/Documents/investai/backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()

client = Client()
results = {}

def run_test(name, fn):
    try:
        result = fn()
        results[name] = {'status': 'PASS', 'detail': result}
        print(f"✓ {name}: {result}")
    except Exception as e:
        results[name] = {'status': 'FAIL', 'detail': str(e)}
        print(f"✗ {name}: {e}")

# Unique username to avoid conflicts
UNIQUE_ID = str(uuid.uuid4())[:8]
USERNAME = f"test_{UNIQUE_ID}"
EMAIL = f"test_{UNIQUE_ID}@example.com"
PASSWORD = "TestPass123!"

# 1. Registration
def test_register():
    resp = client.post('/api/v1/auth/register/', {
        'username': USERNAME,
        'email': EMAIL,
        'password': PASSWORD,
        'password_confirm': PASSWORD
    }, content_type='application/json')
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.content}"
    return f"201 Created"

# 2. Login
token_store = {}
def test_login():
    resp = client.post('/api/v1/auth/login/', {
        'email': EMAIL,
        'password': PASSWORD
    }, content_type='application/json')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    data = json.loads(resp.content)
    assert 'access' in data, "No access token in response"
    token_store['access'] = data['access']
    token_store['refresh'] = data.get('refresh', '')
    return "200 OK - tokens received"

def get_headers():
    return {'HTTP_AUTHORIZATION': f"Bearer {token_store.get('access', '')}"}

# 3. JWT Refresh
def test_jwt_refresh():
    resp = client.post('/api/v1/auth/refresh/', {
        'refresh': token_store.get('refresh', '')
    }, content_type='application/json')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    data = json.loads(resp.content)
    assert 'access' in data, "No access token in refresh response"
    return "200 OK - new token received"

# 4. Profile
def test_profile():
    resp = client.get('/api/v1/auth/profile/', **get_headers())
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    data = json.loads(resp.content)
    return f"200 OK - user: {data.get('username', data.get('email', 'unknown'))}"

# 5. Dashboard
def test_dashboard():
    resp = client.get('/api/dashboard/', **get_headers())
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    return "200 OK"

# 6. Portfolio holdings
def test_portfolio():
    resp = client.get('/api/v1/portfolio/holdings/', **get_headers())
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    return "200 OK"

# 7. Watchlist
def test_watchlist():
    resp = client.get('/api/v1/watchlist/', **get_headers())
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    return "200 OK"

# 8. AI Chat - create session and send message
def test_chat():
    # Create session
    resp = client.post('/api/v1/chat/sessions/', {
        'title': 'Test Session'
    }, content_type='application/json', **get_headers())
    assert resp.status_code == 201, f"Session creation: {resp.status_code}: {resp.content}"
    session_id = json.loads(resp.content)['id']
    
    # Send message
    resp2 = client.post('/api/v1/chat/message/', {
        'session_id': session_id,
        'message': 'What is portfolio diversification?'
    }, content_type='application/json', **get_headers())
    assert resp2.status_code == 200, f"Chat message: {resp2.status_code}: {resp2.content}"
    data = json.loads(resp2.content)
    assert 'message' in data, "No 'message' in chat response"
    return f"200 OK - response: {data['message'][:50]}..."

# 9. Research / Stock Analysis
def test_research():
    resp = client.post('/api/v1/research/analyze/', {
        'symbol': 'RELIANCE',
        'time_horizon': 'LONG'
    }, content_type='application/json', **get_headers())
    # Can be 200 or FAILED status if AI engine unavailable but no 5xx
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    return f"200 OK"

# 10. Portfolio Optimizer
def test_portfolio_optimizer():
    resp = client.post('/api/v1/portfolio/optimize/', {
        'symbols': ['AAPL', 'MSFT', 'GOOGL'],
        'method': 'markowitz'
    }, content_type='application/json', **get_headers())
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    return "200 OK"

# 11. Protected route without token
def test_protected_route():
    resp = client.get('/api/v1/auth/profile/')
    assert resp.status_code == 401, f"Expected 401 for no token, got {resp.status_code}"
    return "401 Unauthorized (correct)"

# 12. Logout
def test_logout():
    resp = client.post('/api/v1/auth/logout/', **get_headers())
    assert resp.status_code in (200, 204), f"Expected 200/204, got {resp.status_code}: {resp.content}"
    return f"{resp.status_code} OK"

# Run all tests in order
print("\n" + "="*60)
print("INVESTWISE AI - FULL FUNCTIONAL TEST SUITE")
print("="*60 + "\n")

run_test("1. User Registration", test_register)
run_test("2. Login + JWT", test_login)
run_test("3. JWT Refresh", test_jwt_refresh)
run_test("4. Profile", test_profile)
run_test("5. Dashboard", test_dashboard)
run_test("6. Portfolio Holdings", test_portfolio)
run_test("7. Watchlist", test_watchlist)
run_test("8. AI Chat", test_chat)
run_test("9. Research / Stock Analysis", test_research)
run_test("10. Portfolio Optimizer", test_portfolio_optimizer)
run_test("11. Protected Routes (401)", test_protected_route)
run_test("12. Logout", test_logout)

print("\n" + "="*60)
passed = sum(1 for r in results.values() if r['status'] == 'PASS')
failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
print(f"RESULTS: {passed} passed, {failed} failed out of {len(results)} tests")
print("="*60 + "\n")

if failed == 0:
    print("✅ ALL TESTS PASSED - APPLICATION IS FULLY FUNCTIONAL")
else:
    print("❌ SOME TESTS FAILED - SEE ABOVE FOR DETAILS")
    for name, r in results.items():
        if r['status'] == 'FAIL':
            print(f"  FAIL: {name} - {r['detail']}")
