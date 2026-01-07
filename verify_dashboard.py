
import urllib.request
import json

def test_admin_api():
    url = "http://127.0.0.1:5000/api/admin/summary"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print("\nAdmin API Test: SUCCESS")
                print(f"Total Users: {data.get('total_users')}")
                print(f"Total Interactions: {data.get('total_interactions')}")
                print(f"Recent Searches: {len(data.get('recent_searches'))}")
                print(f"Top Genres: {len(data.get('top_genres'))}")
            else:
                print(f"\nAdmin API Test: FAILED (Status {response.status})")
    except Exception as e:
        print(f"\nAdmin API Test: FAILED ({e})")

if __name__ == "__main__":
    test_admin_api()
