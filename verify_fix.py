
import urllib.request
import json

def make_full_request(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.reason
    except Exception as e:
        return 0, str(e)

def verify():
    base = "http://127.0.0.1:5000"
    user_id = 1 # Assuming user 1 exists from seed/previous tests

    print("Verifying Fixes...")

    # 1. Recommendations (Fixed route)
    code, res = make_full_request(f"{base}/api/recommendations/{user_id}")
    print(f"GET /api/recommendations/{user_id}: {code}")
    if code != 200: print(f"  Error: {res}")

    # 2. Recommendations (Query param)
    code, res = make_full_request(f"{base}/api/recommendations?user_id={user_id}")
    print(f"GET /api/recommendations?user_id={user_id}: {code}")

    # 3. Interests (Query param)
    code, res = make_full_request(f"{base}/api/user/interests?user_id={user_id}")
    print(f"GET /api/user/interests?user_id={user_id}: {code}")

    # 4. Profile (New)
    code, res = make_full_request(f"{base}/api/user/profile?user_id={user_id}")
    print(f"GET /api/user/profile?user_id={user_id}: {code}")
    print(f"  Profile Data: {res}")

    # 5. Trending
    code, res = make_full_request(f"{base}/api/trending")
    print(f"GET /api/trending: {code}")

if __name__ == "__main__":
    verify()
