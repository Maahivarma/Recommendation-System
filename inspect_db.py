import sqlite3
import pandas as pd

DB_NAME = 'netflix_rec.db'

def inspect():
    conn = sqlite3.connect(DB_NAME)
    
    print("=== USERS ===")
    print(pd.read_sql('SELECT * FROM users', conn))
    print("\n")

    print("=== INTERACTIONS (Last 10) ===")
    print(pd.read_sql('SELECT * FROM interactions ORDER BY id DESC LIMIT 10', conn))
    print("\n")

    print("=== SEARCH HISTORY (Last 10) ===")
    print(pd.read_sql('SELECT * FROM search_history ORDER BY id DESC LIMIT 10', conn))
    print("\n")

    conn.close()

if __name__ == "__main__":
    inspect()
