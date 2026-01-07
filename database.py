import sqlite3
import os

DB_NAME = 'netflix_rec.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    conn = get_db_connection()
    c = conn.cursor()

    # Create Tables
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            description TEXT,
            rating REAL,
            year INTEGER,
            image_url TEXT
        )
    ''') 

    c.execute('''
        CREATE TABLE interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            interaction_type TEXT, -- 'watch', 'like', 'dislike'
            watch_time INTEGER DEFAULT 0, -- Duration in seconds
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (movie_id) REFERENCES movies (id)
        )
    ''')

    c.execute('''
        CREATE TABLE search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Seed Data
    # Password for all is 'password' -> pbkdf2:sha256:260000... (just using a placeholder or actually generating one in python would be better, but for init_db let's use a clear placeholder or just run a quick script)
    # Actually, let's just make the 'init_db' function cleaner or handle hashing in app. 
    # For now, I'll insert raw dummy hashes or just clear text for this specific step if we assume the app handles it.
    # BETTER: Let's not seed users, let the user Register. 
    # BUT: We need users for the interaction seed data to make sense.
    # Use a pre-calculated hash for 'password': pbkdf2:sha256:600000$....
    # I'll use a simple placeholder hash that I know works or just empty.
    # Actually, I'll import generate_password_hash here to do it right.
    from werkzeug.security import generate_password_hash
    
    users = [
        ('Alice', 'alice@example.com', generate_password_hash('password')),
        ('Bob', 'bob@example.com', generate_password_hash('password')),
        ('Charlie', 'charlie@example.com', generate_password_hash('password')),
        ('Dave', 'dave@example.com', generate_password_hash('password'))
    ]
    c.executemany('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', users)

    movies = [
        ('Inception', 'Sci-Fi|Action', 'A thief who steals corporate secrets through the use of dream-sharing technology.', 8.8, 2010, 'https://image.tmdb.org/t/p/w500/9gk7admal4zlHkdyDztsoJn7PDE.jpg'),
        ('The Dark Knight', 'Action|Crime', 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham.', 9.0, 2008, 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg'),
        ('Interstellar', 'Sci-Fi|Adventure', 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity''s survival.', 8.6, 2014, 'https://image.tmdb.org/t/p/w500/gEU2QniL6E8ahDaNBAXcOTk477y.jpg'),
        ('Parasite', 'Thriller|Drama', 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.', 8.5, 2019, 'https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg'),
        ('Avengers: Endgame', 'Action|Sci-Fi', 'After the devastating events of Infinity War, the universe is in ruins.', 8.4, 2019, 'https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg'),
        ('The Matrix', 'Sci-Fi|Action', 'A computer hacker learns from mysterious rebels about the true nature of his reality.', 8.7, 1999, 'https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg'),
        ('The GodFather', 'Crime|Drama', 'An organized crime dynasty''s aging patriarch transfers control of his clandestine empire to his reluctant son.', 9.2, 1972, 'https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg'),
        ('Pulp Fiction', 'Crime|Drama', 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine.', 8.9, 1994, 'https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg'),
        ('Spirited Away', 'Animation|Fantasy', 'During her family''s move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits.', 8.6, 2001, 'https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUKGnSxQbUgZ.jpg'),
        ('The Lion King', 'Animation|Drama', 'Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself.', 8.5, 1994, 'https://image.tmdb.org/t/p/w500/sKCr78MXSLixwmZ8DyJLrpMsd15.jpg'),
        ('Schindler''s List', 'History|Drama', 'In German-occupied Poland during World War II, industrialist Oskar Schindler gradually becomes concerned for his Jewish workforce.', 8.9, 1993, 'https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGOtFid.jpg'),
        ('Fight Club', 'Drama', 'An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into something much, much more.', 8.8, 1999, 'https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7Qf4n6a8mi75.jpg'),
        ('Goodfellas', 'Biography|Crime', 'The story of Henry Hill and his life in the mob, covering his relationship with his wife Karen Hill and his mob partners Jimmy Conway and Tommy DeVito.', 8.7, 1990, 'https://image.tmdb.org/t/p/w500/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg'),
        ('Forrest Gump', 'Drama|Romance', 'The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75.', 8.8, 1994, 'https://image.tmdb.org/t/p/w500/saHP97rTPS5eLmrLQEcANmKrsFl.jpg'),
        ('The Shawshank Redemption', 'Drama', 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.', 9.3, 1994, 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg'),
        ('Coco', 'Animation|Fantasy', 'Aspiring musician Miguel, confronted with his family''s ancestral ban on music, enters the Land of the Dead to find his great-great-grandfather, a legendary singer.', 8.4, 2017, 'https://image.tmdb.org/t/p/w500/gGEsBPAijhVUFoiNpgZXqRVWJt2.jpg'),
        ('Dune', 'Sci-Fi|Adventure', 'Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe.', 8.0, 2021, 'https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg'),
        ('Spider-Man: Into the Spider-Verse', 'Animation|Action', 'Teen Miles Morales becomes the Spider-Man of his universe, and must join with five spider-powered individuals from other dimensions to stop a threat for all realities.', 8.4, 2018, 'https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg'),
        ('Joker', 'Crime|Drama', 'In Gotham City, mentally troubled comedian Arthur Fleck is disregarded and mistreated by society. He then embarks on a downward spiral of revolution and bloody crime.', 8.4, 2019, 'https://image.tmdb.org/t/p/w500/udDclJoHjfjb8Ekgsd4FDteOkCU.jpg'),
        ('Stranger Things', 'Sci-Fi|Horror', 'When a young boy disappears, his mother, a police chief and his friends must confront terrifying supernatural forces in order to get him back.', 8.7, 2016, 'https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg')
    ]

    c.executemany('INSERT INTO movies (title, genre, description, rating, year, image_url) VALUES (?, ?, ?, ?, ?, ?)', movies)

    # Fake Interactions for "Alice" (User 1) - Likes Action/Sci-Fi
    interactions = [
        (1, 1, 'watch', 5400), (1, 1, 'like', 0), # Inception (watched 90 mins)
        (1, 2, 'watch', 7200), (1, 2, 'like', 0), # Dark Knight
        (1, 3, 'watch', 3600), # Interstellar
        (1, 4, 'watch', 100), # Parasite (started but stopped)
        (1, 5, 'watch', 9000), (1, 5, 'like', 0), # Avengers
        (2, 6, 'watch', 6000), (2, 6, 'like', 0), # Bob likes Matrix
        (2, 7, 'watch', 8000), # Godfather
    ]
    c.executemany('INSERT INTO interactions (user_id, movie_id, interaction_type, watch_time) VALUES (?, ?, ?, ?)', interactions)
    
    # Fake Search History
    searches = [
        (1, 'Sci-Fi movies'),
        (1, 'Action movies'),
        (2, 'Classic Mob movies')
    ]
    c.executemany('INSERT INTO search_history (user_id, query) VALUES (?, ?)', searches)

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()
