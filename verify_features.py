
import urllib.request
import json

BASE = "http://127.0.0.1:5000"

def req(url):
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}

def test_features():
    print("Testing New Features...")
    
    # 1. Movie Details
    uid = 1
    c, mv = req(f"{BASE}/api/movies/{uid}")
    print(f"GET /api/movies/{uid}: {c}")
    if c == 200:
        print(f"  Title: {mv.get('title')}")
        print(f"  Desc: {mv.get('description')[:50]}...")
    else:
        print("  Failed to fetch details.")

    # 2. Genre Filter
    genre = "Action"
    c, movies = req(f"{BASE}/api/movies?genre={genre}")
    print(f"GET /api/movies?genre={genre}: {c}")
    if c == 200:
        print(f"  Count: {len(movies)}")
        if len(movies) > 0:
            print(f"  First: {movies[0]['title']} ({movies[0]['genre']})")
            if genre in movies[0]['genre']:
                print("  SUCCESS: Genre filtered correctly.")
            else:
                print("  FAILURE: Movie does not match genre.")
    else:
        print("  Failed to fetch genre.")

if __name__ == "__main__":
    test_features()
