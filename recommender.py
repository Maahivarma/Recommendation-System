import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

DB_NAME = 'netflix_rec.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

class Recommender:
    def __init__(self):
        self.refresh_data()

    def refresh_data(self):
        conn = get_db_connection()
        self.movies = pd.read_sql('SELECT * FROM movies', conn)
        self.interactions = pd.read_sql('SELECT * FROM interactions', conn)
        conn.close()
        
        # Prepare Content-Based Matrix
        # Combine genre and description
        self.movies['content'] = self.movies['genre'].str.replace('|', ' ') + ' ' + self.movies['description']
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf.fit_transform(self.movies['content'])
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
        
        # Map movie titles to indices
        self.indices = pd.Series(self.movies.index, index=self.movies['id'])

    def get_content_recommendations(self, movie_ids, top_n=5):
        """Recommend movies similar to the list of movie_ids"""
        if not movie_ids:
            return []
            
        # Get average similarity scores for the input movies
        sim_scores = None
        for movie_id in movie_ids:
            if movie_id not in self.indices:
                continue
            idx = self.indices[movie_id]
            scores = list(enumerate(self.cosine_sim[idx]))
            if sim_scores is None:
                sim_scores = scores
            else:
                # Add scores element-wise (simple aggregate)
                sim_scores = [(i, sim_scores[i][1] + scores[i][1]) for i in range(len(scores))]
        
        if not sim_scores:
             # Random fallback if IDs invalid
            return self.movies.sample(top_n).to_dict('records')

        # Sort
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Exclude input movies
        sim_scores = [x for x in sim_scores if self.movies.iloc[x[0]]['id'] not in movie_ids]
        
        sim_scores = sim_scores[:top_n]
        movie_indices = [i[0] for i in sim_scores]
        
        return self.movies.iloc[movie_indices].to_dict('records')

    def get_collaborative_recommendations(self, user_id, top_n=5):
        """Simple item-based collaborative filtering based on what others who liked X also liked."""
        # For this prototype, we'll do a simplified approach since dataset is small.
        # Find movies user watched/liked
        user_inter = self.interactions[self.interactions['user_id'] == int(user_id)]
        watched_ids = user_inter['movie_id'].tolist()
        
        if not watched_ids:
            return []

        # Find other users who watched the same movies
        similar_users = self.interactions[
            (self.interactions['movie_id'].isin(watched_ids)) & 
            (self.interactions['user_id'] != int(user_id))
        ]['user_id'].unique()
        
        # Find movies those users watched that THIS user hasn't
        recs = self.interactions[
            (self.interactions['user_id'].isin(similar_users)) & 
            (~self.interactions['movie_id'].isin(watched_ids))
        ]['movie_id'].value_counts()
        
        rec_ids = recs.head(top_n).index.tolist()
        return self.movies[self.movies['id'].isin(rec_ids)].to_dict('records')

    def calculate_genre_profile(self, user_id):
        conn = get_db_connection()
        
        # Initialize scores
        scores = {}
        
        # 1. Watch Time & Likes
        interactions = pd.read_sql('SELECT * FROM interactions WHERE user_id = ?', conn, params=(user_id,))
        for _, row in interactions.iterrows():
            movie = self.movies[self.movies['id'] == row['movie_id']]
            if movie.empty: continue
            
            genres = movie.iloc[0]['genre'].split('|')
            points = 0
            
            if row['interaction_type'] == 'like':
                points += 10
            elif row['interaction_type'] == 'watch':
                # +3 points for every minute watched, up to max 30
                minutes = row['watch_time'] / 60
                if minutes > 1:
                    points += min(int(minutes * 3), 30)
            
            for g in genres:
                scores[g] = scores.get(g, 0) + points

        # 2. Search History
        searches = pd.read_sql('SELECT * FROM search_history WHERE user_id = ?', conn, params=(user_id,))
        # Simple keyword matching against known genres
        all_genres = set()
        for g_str in self.movies['genre'].unique():
            all_genres.update(g_str.split('|'))
            
        for _, row in searches.iterrows():
            query = row['query'].lower()
            for genre in all_genres:
                if genre.lower() in query:
                    scores[genre] = scores.get(genre, 0) + 5
        
        conn.close()
        return scores

    def get_hybrid_recommendations(self, user_id, top_n=10):
        self.refresh_data() 
        
        # 1. Get Base Candidates (Content + Collaborative)
        # Reuse existing logic to get a pool of candidates
        user_inter = self.interactions[
             (self.interactions['user_id'] == int(user_id))
        ]
        
        if user_inter.empty:
            candidates = self.movies.sort_values('rating', ascending=False).head(20).to_dict('records')
        else:
            strong_interest = user_inter[
                 (user_inter['interaction_type'] == 'like') | 
                 ((user_inter['interaction_type'] == 'watch') & (user_inter['watch_time'] > 300))
            ]['movie_id'].tolist()
            
            watched_ids = user_inter['movie_id'].tolist()
            
            content_recs = []
            if strong_interest:
                content_recs = self.get_content_recommendations(strong_interest, top_n=15) # Get more for re-ranking
            
            collab_recs = self.get_collaborative_recommendations(user_id, top_n=15)
            
            # Combine
            combined = {m['id']: m for m in content_recs + collab_recs}
            candidates = list(combined.values())
            
            # Fill if low
            if len(candidates) < 10:
                 more = self.movies[~self.movies['id'].isin(watched_ids + [m['id'] for m in candidates])]
                 candidates.extend(more.sort_values('rating', ascending=False).head(20 - len(candidates)).to_dict('records'))

        # 2. Calculate User Genre Profile
        profile = self.calculate_genre_profile(user_id)
        if not profile:
             return candidates[:top_n] # No profile, return standard
             
        max_score = max(profile.values()) if profile.values() else 1

        # 3. Re-Rank Candidates
        scored_candidates = []
        for movie in candidates:
            movie_genres = movie['genre'].split('|')
            match_score = 0
            # Sum scores of matching genres
            for g in movie_genres:
                match_score += profile.get(g, 0)
            
            # Normalize to 0-100 scale relative to max profile score
            # A perfect match would contain the user's favorite genres
            final_percent = min(int((match_score / max_score) * 100), 100)
            
            # Heuristic: Boost by rating slightly
            final_percent += int(movie['rating'])
            final_percent = min(final_percent, 99)
            
            movie['match_score'] = final_percent
            
            # Determine "Reason"
            top_genre = max(movie_genres, key=lambda g: profile.get(g, 0))
            if profile.get(top_genre, 0) > 0:
                movie['match_reason'] = f"Because you watch {top_genre}"
            else:
                movie['match_reason'] = "Popular on Netflix"
                
            scored_candidates.append(movie)
            
        # Sort by Match Score
        scored_candidates.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return scored_candidates[:top_n]
