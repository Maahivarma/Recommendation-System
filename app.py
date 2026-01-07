from flask import Flask, render_template, jsonify, request, g
import sqlite3
from database import DB_NAME, get_db_connection
from recommender import Recommender

app = Flask(__name__)
recommender = Recommender()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = get_db_connection()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/backend')
def backend_dashboard():
    return render_template('backend.html')

@app.route('/api/admin/summary')
def admin_summary():
    db = get_db()
    
    # Total Users
    cur = db.execute('SELECT COUNT(*) FROM users')
    total_users = cur.fetchone()[0]
    
    # Total Interactions
    cur = db.execute('SELECT COUNT(*) FROM interactions')
    total_interactions = cur.fetchone()[0]
    
    # Total Watch Time (minutes)
    cur = db.execute('SELECT SUM(watch_time) FROM interactions WHERE interaction_type="watch"')
    res = cur.fetchone()[0]
    total_watch_time = round(res / 60, 1) if res else 0

    # Recent Searches
    cur = db.execute('SELECT s.query, s.timestamp, u.username FROM search_history s JOIN users u ON s.user_id = u.id ORDER BY s.timestamp DESC LIMIT 10')
    recent_searches = [dict(row) for row in cur.fetchall()]
    
    # Recent Interactions
    cur = db.execute('''
        SELECT i.interaction_type, i.timestamp, u.username, m.title 
        FROM interactions i 
        JOIN users u ON i.user_id = u.id 
        JOIN movies m ON i.movie_id = m.id 
        ORDER BY i.timestamp DESC 
        LIMIT 10
    ''')
    recent_interactions = [dict(row) for row in cur.fetchall()]

    # Top Genres (Simple count from movies watched)
    cur = db.execute('''
        SELECT m.genre, COUNT(*) as count 
        FROM interactions i 
        JOIN movies m ON i.movie_id = m.id 
        WHERE i.interaction_type='watch' 
        GROUP BY m.genre 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    # Flatten genres if they are piped? For simplified View, just take raw group.
    # To do it properly we'd split in python, but let's just return what we have.
    top_genres = [dict(row) for row in cur.fetchall()]

    return jsonify({
        'total_users': total_users,
        'total_interactions': total_interactions,
        'total_watch_time': total_watch_time,
        'recent_searches': recent_searches,
        'recent_interactions': recent_interactions,
        'top_genres': top_genres
    })


@app.route('/api/users')
def get_users():
    cur = get_db().execute('SELECT * FROM users')
    users = [dict(row) for row in cur.fetchall()]
    return jsonify(users)

@app.route('/api/movies')
def get_movies():
    genre = request.args.get('genre')
    db = get_db()
    
    if genre:
        # Simple LIKE query for genre filtering
        cur = db.execute('SELECT * FROM movies WHERE genre LIKE ? ORDER BY rating DESC', (f'%{genre}%',))
    else:
        # Return all movies
        cur = db.execute('SELECT * FROM movies ORDER BY rating DESC')
        
    movies = [dict(row) for row in cur.fetchall()]
    return jsonify(movies)

@app.route('/api/movies/<int:movie_id>')
def get_movie_details(movie_id):
    db = get_db()
    cur = db.execute('SELECT * FROM movies WHERE id = ?', (movie_id,))
    movie = cur.fetchone()
    if movie:
        return jsonify(dict(movie))
    return jsonify({'error': 'Movie not found'}), 404

@app.route('/api/recommendations/<int:user_id>')
def get_recommendations(user_id):
    # Get hybrid recommendations
    if not user_id:
        return jsonify([])
    recs = recommender.get_hybrid_recommendations(user_id)
    return jsonify(recs)

# Support for /api/recommendations?user_id=1
@app.route('/api/recommendations')
def get_recommendations_query():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id param'}), 400
    return get_recommendations(int(user_id))

# Support for /api/user/interests?user_id=1
@app.route('/api/user/interests')
def get_user_interests_query():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id param'}), 400
    # Process interests for this user
    return get_user_interests(int(user_id))

@app.route('/api/user/profile')
def get_user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id param'}), 400
    
    db = get_db()
    cur = db.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    if not user:
         return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(user))

# --- AUTH API ---
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'Missing fields'}), 400
        
    db = get_db()
    # Check exists
    cur = db.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cur.fetchone():
        return jsonify({'error': 'Email already registered'}), 400
        
    pwd_hash = generate_password_hash(password)
    db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
               (username, email, pwd_hash))
    db.commit()
    
    return jsonify({'status': 'success'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'error': 'Missing fields'}), 400
        
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cur.fetchone()
    
    if user and check_password_hash(user['password_hash'], password):
        return jsonify({
            'status': 'success',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
        
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    user_id = data.get('user_id')
    movie_id = data.get('movie_id')
    interaction_type = data.get('type') # 'watch', 'like'
    watch_time = data.get('watch_time', 0)

    if not all([user_id, movie_id, interaction_type]):
        return jsonify({'error': 'Missing data'}), 400

    db = get_db()
    # If it's a 'watch' interaction, we might want to update an existing record logic or just insert new. 
    # For simplicity, we just insert.
    db.execute('INSERT INTO interactions (user_id, movie_id, interaction_type, watch_time) VALUES (?, ?, ?, ?)',
               (user_id, movie_id, interaction_type, watch_time))
    db.commit()
    
    return jsonify({'status': 'success'})

@app.route('/api/track/search', methods=['POST'])
def track_search():
    data = request.json
    user_id = data.get('user_id')
    query = data.get('query')

    if not all([user_id, query]):
         return jsonify({'error': 'Missing data'}), 400
    
    db = get_db()
    db.execute('INSERT INTO search_history (user_id, query) VALUES (?, ?)', (user_id, query))
    db.commit()

    return jsonify({'status': 'success'})

@app.route('/api/history/<int:user_id>')
def get_history(user_id):
    db = get_db()
    cur = db.execute('''
        SELECT m.*, i.interaction_type, i.timestamp, i.watch_time
        FROM interactions i 
        JOIN movies m ON i.movie_id = m.id 
        WHERE i.user_id = ? 
        ORDER BY i.timestamp DESC
    ''', (user_id,))
    history = [dict(row) for row in cur.fetchall()]
    return jsonify(history)

@app.route('/api/user/interests/<int:user_id>')
def get_user_interests(user_id):
    db = get_db()
    # Simple logic: derived from genres of movies watched or liked
    cur = db.execute('''
        SELECT m.genre
        FROM interactions i
        JOIN movies m ON i.movie_id = m.id
        WHERE i.user_id = ? AND i.interaction_type IN ('watch', 'like')
    ''', (user_id,))
    
    genres = []
    for row in cur.fetchall():
        genres.extend(row['genre'].split('|'))
    
    # Count frequency
    from collections import Counter
    if not genres:
        return jsonify([])
        
    counts = Counter(genres)
    # Return top 5
    top_interests = [g for g, c in counts.most_common(5)]
    return jsonify(top_interests)

@app.route('/api/trending')
def get_trending():
    db = get_db()
    # Trending: movies with most interactions in the last X period (or just most interactions total for simplicity)
    cur = db.execute('''
        SELECT m.*, COUNT(i.id) as interaction_count
        FROM movies m
        JOIN interactions i ON m.id = i.movie_id
        GROUP BY m.id
        ORDER BY interaction_count DESC
        LIMIT 10
    ''')
    trending = [dict(row) for row in cur.fetchall()]
    return jsonify(trending)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
