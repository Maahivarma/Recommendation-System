import urllib.request
import urllib.parse
import json
import time

BASE_URL = 'http://127.0.0.1:5000'

def make_request(endpoint, method='GET', data=None):
    url = f"{BASE_URL}{endpoint}"
    if data:
        data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))
        
def test_auth():
    print("\nTesting Auth...")
    # Register
    reg_data = {'username': 'Tester', 'email': 'test@example.com', 'password': 'password123'}
    status, res = make_request('/api/auth/register', 'POST', reg_data)
    print(f"Register: {status} - {res}")
    # Handle if already exists (for re-runs)
    if status != 200 and 'already registered' not in str(res):
        print("Register failed unexpected.")

    # Login
    login_data = {'email': 'test@example.com', 'password': 'password123'}
    status, res = make_request('/api/auth/login', 'POST', login_data)
    print(f"Login: {status} - {res}")
    
    if status == 200:
        return res['user']['id']
    return None

def test_tracking(user_id):
    print("Testing Tracking...")
    
    # Track Search
    payload_search = {'user_id': user_id, 'query': 'Verification Test Search'}
    status, res_json = make_request('/api/track/search', 'POST', payload_search)
    print(f"Track Search: {status} - {res_json}")
    assert status == 200

    # Track Watch
    payload_watch = {'user_id': user_id, 'movie_id': 1, 'type': 'watch', 'watch_time': 1234}
    status, res_json = make_request('/api/interact', 'POST', payload_watch)
    print(f"Track Watch: {status} - {res_json}")
    assert status == 200

def test_retrieval(user_id):
    print("\nTesting Retrieval...")

    # History
    status, history = make_request(f'/api/history/{user_id}')
    print(f"History Count: {len(history)}")
    
    # Interests
    status, interests = make_request(f'/api/user/interests/{user_id}')
    print(f"Interests: {interests}")

    # Trending
    status, trending = make_request('/api/trending')
    print(f"Trending Count: {len(trending)}")

if __name__ == "__main__":
    try:
        user_id = test_auth()
        if user_id:
            test_tracking(user_id)
            test_retrieval(user_id)
            print("\nVerification Complete!")
        else:
            print("\nAuth Failed, skipping other tests.")
    except Exception as e:
        print(f"\nVerification Failed: {e}")
