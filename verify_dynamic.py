
import urllib.request
import json
import random

BASE = "http://127.0.0.1:5000"

def req(url, method="GET", data=None):
    try:
        if data:
            data = json.dumps(data).encode()
        r = urllib.request.Request(url, data=data, method=method, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def test_dynamic():
    print("Testing Dynamic Recommendations...")
    
    # 1. Create a fresh user to strictly test profile
    name = f"UserRef{random.randint(1000,9999)}"
    reg_data = {"username": name, "email": f"{name}@test.com", "password": "password"}
    c, res = req(f"{BASE}/api/auth/register", "POST", reg_data)
    if c != 200: 
        print(f"Register Failed: {res}")
        return

    # Login to get ID
    c, res = req(f"{BASE}/api/auth/login", "POST", {"email": reg_data['email'], "password": "password"})
    user_id = res['user']['id']
    print(f"Created User ID: {user_id}")

    # 2. Before Interaction: Check Recs (Should be generic)
    c, recs_before = req(f"{BASE}/api/recommendations/{user_id}")
    print(f"Recs Before Count: {len(recs_before)}")
    
    # 3. Simulate Interest: Search for 'Sci-Fi'
    print("Action: Searching for 'Sci-Fi'...")
    req(f"{BASE}/api/track/search", "POST", {"user_id": user_id, "query": "Sci-Fi"})
    
    # 4. Check Recs After
    c, recs_after = req(f"{BASE}/api/recommendations/{user_id}")
    if c == 200:
        top_rec = recs_after[0]
        print(f"Top Recommendation: {top_rec.get('title')}")
        print(f"  Genre: {top_rec.get('genre')}")
        print(f"  Match Score: {top_rec.get('match_score')}")
        print(f"  Reason: {top_rec.get('match_reason')}")
        
        # Validation
        if "Sci-Fi" in top_rec.get('genre', '') and top_rec.get('match_score', 0) > 50:
            print("SUCCESS: Sci-Fi boosted to top!")
        else:
            print("FAILURE: Sci-Fi not boosted correctly.")
    else:
        print(f"Failed to get recs: {recs_after}")

if __name__ == "__main__":
    test_dynamic()
