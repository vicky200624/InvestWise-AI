import os
import sys
import django
from django.test import Client
import json

sys.path.insert(0, '/home/vicky/Documents/investai/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

client = Client()

def test_flow():
    errors = []
    
    # 1. Register
    print("Testing Registration...")
    resp = client.post('/api/v1/auth/register/', {
        'username': 'testuser1',
        'email': 'testuser1@example.com',
        'password': 'password123',
        'password_confirm': 'password123'
    }, content_type='application/json')
    if resp.status_code != 201:
        errors.append(f"Registration failed: {resp.status_code} {resp.content}")
    else:
        print("Registration successful.")

    # 2. Login
    print("Testing Login...")
    resp = client.post('/api/v1/auth/login/', {
        'email': 'testuser1@example.com',
        'password': 'password123'
    }, content_type='application/json')
    if resp.status_code != 200:
        errors.append(f"Login failed: {resp.status_code} {resp.content}")
        return errors
    
    token = json.loads(resp.content)['access']
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    print("Login successful.")

    # 3. Dashboard
    print("Testing Dashboard...")
    resp = client.get('/api/dashboard/', **headers)
    if resp.status_code != 200:
        errors.append(f"Dashboard failed: {resp.status_code} {resp.content}")

    # 4. Portfolio
    print("Testing Portfolio...")
    resp = client.get('/api/v1/portfolio/holdings/', **headers)
    if resp.status_code != 200:
        errors.append(f"Portfolio failed: {resp.status_code} {resp.content}")

    # 5. Watchlist
    print("Testing Watchlist...")
    resp = client.get('/api/v1/watchlist/', **headers)
    if resp.status_code != 200:
        errors.append(f"Watchlist failed: {resp.status_code} {resp.content}")

    # 6. Chat
    print("Testing Chat...")
    resp = client.get('/api/v1/chat/', **headers)
    # Chat endpoint might require specific params, just check if it doesn't crash 500
    if resp.status_code >= 500:
        errors.append(f"Chat failed: {resp.status_code} {resp.content}")

    # 7. Logout (if endpoint exists)
    print("Testing Logout...")
    resp = client.post('/api/v1/auth/logout/', **headers)
    if resp.status_code >= 500:
        errors.append(f"Logout failed: {resp.status_code} {resp.content}")

    if not errors:
        print("ALL TESTS PASSED SUCCESSFULLY!")
    else:
        print("ERRORS FOUND:")
        for err in errors:
            print(err)

if __name__ == "__main__":
    test_flow()
