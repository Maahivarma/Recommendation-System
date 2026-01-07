document.addEventListener('DOMContentLoaded', () => {
    const apiBase = '/api';

    // Check Auth
    const storedUser = localStorage.getItem('currentUser');
    if (!storedUser) {
        window.location.href = '/login';
        return;
    }

    const currentUserObj = JSON.parse(storedUser);
    const currentUser = currentUserObj.id;

    // UI Elements
    const heroTitle = document.getElementById('hero-title');
    const heroDesc = document.getElementById('hero-desc');
    const heroSec = document.querySelector('.hero');
    const recList = document.getElementById('recommendations-list');
    const trendList = document.getElementById('trending-list');
    const histList = document.getElementById('history-list');
    const interestsList = document.getElementById('interests-list');

    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const welcomeMsg = document.getElementById('welcome-msg');

    // Initialize
    welcomeMsg.textContent = `Hi, ${currentUserObj.username}`;
    loadDashboard(currentUser);

    // Event Listeners
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('currentUser');
        window.location.href = '/login';
    });

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value;
        if (query) trackSearch(query);
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value;
            if (query) trackSearch(query);
        }
    });

    // Removed fetchUsers() as we no longer select user manually

    async function loadDashboard(userId) {
        // Clear Lists
        recList.innerHTML = '<p class="loading-msg">Loading recommendations...</p>';
        trendList.innerHTML = '<p class="loading-msg">Loading trending...</p>';
        histList.innerHTML = '<p class="loading-msg">Loading history...</p>';
        interestsList.innerHTML = '...';

        // 1. Get Recommendations
        try {
            const recRes = await fetch(`${apiBase}/recommendations/${userId}`);
            if (recRes.ok) {
                const recs = await recRes.json();
                renderList(recList, recs);
            } else {
                recList.innerHTML = '<p class="error-msg">Failed to load recommendations.</p>';
            }
        } catch (e) {
            console.error("Recs error:", e);
            recList.innerHTML = '<p class="error-msg">Available after you watch (5m+) some content.</p>';
        }

        // 2. Get Interests
        try {
            const intRes = await fetch(`${apiBase}/user/interests/${userId}`);
            if (intRes.ok) {
                const interests = await intRes.json();
                renderInterests(interests);
            } else {
                interestsList.innerHTML = '';
            }
        } catch (e) {
            console.error("Interests error:", e);
        }

        // 3. Get Trending (Real data)
        try {
            const trendRes = await fetch(`${apiBase}/trending`);
            if (trendRes.ok) {
                const movies = await trendRes.json();
                renderList(trendList, movies);

                // Randomize Hero from top movies
                if (movies.length > 0) {
                    const heroMovie = movies[Math.floor(Math.random() * Math.min(5, movies.length))];
                    updateHero(heroMovie);
                }
            } else {
                trendList.innerHTML = '<p class="error-msg">Failed to load trending content.</p>';
            }
        } catch (e) {
            console.error("Trending error:", e);
            trendList.innerHTML = '<p class="error-msg">Could not reach the server.</p>';
        }

        // 4. Get History
        try {
            // Check if profile is needed (requested by user, but mostly for header)
            // fetch(`${apiBase}/user/profile?user_id=${userId}`); 

            const histRes = await fetch(`${apiBase}/history/${userId}`);
            if (histRes.ok) {
                const history = await histRes.json();
                renderList(histList, history);
            } else {
                histList.innerHTML = '<p>No history yet.</p>';
            }
        } catch (e) {
            console.error("History error:", e);
            histList.innerHTML = '<p>No history yet.</p>';
        }
    }

    // Modal Elements
    const modal = document.getElementById('movie-modal');
    const modalImg = document.getElementById('modal-img');
    const modalTitle = document.getElementById('modal-title');
    const modalDesc = document.getElementById('modal-desc');
    const modalYear = document.getElementById('modal-year');
    const modalRating = document.getElementById('modal-rating');
    const modalGenre = document.getElementById('modal-genre');
    const closeModalBtn = document.querySelector('.close-modal');

    // Genre View Elements
    const dashView = document.getElementById('dashboard-view');
    const genreView = document.getElementById('genre-view');
    const genreTitle = document.getElementById('genre-title');
    const genreList = document.getElementById('genre-list');
    const closeGenreBtn = document.getElementById('close-genre-btn');

    // Close Modal
    closeModalBtn.onclick = () => { modal.style.display = "none"; };
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    // Close Genre View
    closeGenreBtn.onclick = () => {
        genreView.style.display = "none";
        dashView.style.display = "block";
    };

    function openModal(movie) {
        modalImg.src = movie.image_url;
        modalTitle.textContent = movie.title;
        modalDesc.textContent = movie.description;
        modalYear.textContent = movie.year;
        modalRating.textContent = movie.rating + ' ★';
        // Just take first genre for tag
        modalGenre.textContent = movie.genre ? movie.genre.split('|')[0] : 'Movie';

        modal.style.display = "block";

        // Wire up Modal buttons
        const playBtn = document.getElementById('modal-play-btn');
        playBtn.onclick = () => {
            alert(`Playing ${movie.title}...`);
            trackInteraction(movie.id, 'watch', 600);
        };
    }

    async function loadGenre(genre) {
        // Switch Views
        dashView.style.display = "none";
        genreView.style.display = "block";

        genreTitle.textContent = `${genre} Movies`;
        genreList.innerHTML = '<p class="loading-msg">Loading...</p>';

        try {
            const res = await fetch(`${apiBase}/movies?genre=${encodeURIComponent(genre)}`);
            const movies = await res.json();

            genreList.innerHTML = '';
            if (movies.length === 0) {
                genreList.innerHTML = '<p>No movies found for this genre.</p>';
                return;
            }

            movies.forEach(movie => {
                const card = createCard(movie);
                currentMovies[movie.id] = movie; // Cache for modal
                genreList.appendChild(card);
            });

        } catch (e) {
            console.error("Genre load error", e);
            genreList.innerHTML = '<p class="error-msg">Failed to load genre.</p>';
        }
    }

    // Cache movies globally for modal lookup since card click passes ID or object?
    // Let's modify renderList to attach the object to the element or use ID lookup.
    // Easier: Store all fetched movies in a map.
    let currentMovies = {};

    function renderInterests(interests) {
        interestsList.innerHTML = '';
        if (interests.length === 0) {
            interestsList.innerHTML = '<span class="tag">No interests yet</span>';
            return;
        }
        interests.forEach(interest => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = interest;
            span.style.cssText = 'background: #333; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; cursor: pointer; border: 1px solid #777; transition: all 0.2s;';

            // Hover effect managed by CSS .tag

            span.onclick = () => loadGenre(interest);

            interestsList.appendChild(span);
        });
    }

    function createCard(movie) {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <img src="${movie.image_url}" alt="${movie.title}" loading="lazy">
            <div class="card-overlay">
                ${movie.match_score ? `<div style="color: #46d369; font-weight: bold; margin-bottom: 4px;">${movie.match_score}% Match</div>` : ''}
                ${movie.match_reason ? `<div style="color: #fff; font-size: 0.7em; margin-bottom: 8px;">${movie.match_reason}</div>` : ''}
                <div class="card-title">${movie.title}</div>
                <div class="card-meta">
                    <span>${movie.year}</span>
                    <span>${movie.rating} ★</span>
                </div>
                <div class="action-buttons">
                    <button class="icon-btn play-btn" title="Play"><i class="fas fa-play"></i></button>
                    <button class="icon-btn like-btn" title="Like"><i class="fas fa-thumbs-up"></i></button>
                    <button class="icon-btn info-btn" title="Info"><i class="fas fa-info-circle"></i></button>
                </div>
            </div>
        `;

        // Open Modal on Card Click (except buttons)
        card.onclick = (e) => {
            openModal(movie);
        };

        // Prevent bubble up for buttons
        const playBtn = card.querySelector('.play-btn');
        playBtn.onclick = (e) => {
            e.stopPropagation();
            alert(`Playing ${movie.title}...`);
            trackInteraction(movie.id, 'watch', 600);
        };

        const likeBtn = card.querySelector('.like-btn');
        likeBtn.onclick = (e) => {
            e.stopPropagation();
            alert(`Liked ${movie.title}`);
            trackInteraction(movie.id, 'like');
        };

        return card;
    }

    function updateHero(movie) {
        heroTitle.textContent = movie.title;
        heroDesc.textContent = movie.description;
        heroSec.style.backgroundImage = `linear-gradient(to bottom, rgba(20,20,20,0.3), rgba(20,20,20,1)), url('${movie.image_url}')`;

        // Update Play button to track "watch"
        const playBtn = heroSec.querySelector('.btn-primary');
        // Remove old listeners (clone node trick)
        const newBtn = playBtn.cloneNode(true);
        playBtn.parentNode.replaceChild(newBtn, playBtn);

        newBtn.onclick = () => {
            alert(`Playing ${movie.title}...`);
            trackInteraction(movie.id, 'watch', 300); // Simulate 5 mins watch
        };
    }

    function renderList(container, movies) {
        container.innerHTML = '';
        if (movies.length === 0) {
            container.innerHTML = '<p class="empty-msg">No movies found.</p>';
            return;
        }

        movies.forEach(movie => {
            currentMovies[movie.id] = movie; // Cache
            const card = createCard(movie);
            container.appendChild(card);
        });
    }

    async function trackSearch(query) {
        if (!currentUser) return;
        try {
            await fetch(`${apiBase}/track/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser, query: query })
            });
            alert(`Search tracked: "${query}"`);
        } catch (e) { console.error(e); }
    }

    async function trackInteraction(movieId, type, watchTime = 0) {
        if (!currentUser) return;

        try {
            await fetch(`${apiBase}/interact`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: currentUser,
                    movie_id: movieId,
                    type: type,
                    watch_time: watchTime
                })
            });

            // Allow a small delay for DB commit then reload to show impact
            setTimeout(() => {
                loadDashboard(currentUser);
            }, 500);

        } catch (err) {
            console.error(err);
        }
    }
});
