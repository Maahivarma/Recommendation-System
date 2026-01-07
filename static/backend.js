document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

let genreChartInstance = null;

async function fetchData() {
    try {
        const res = await fetch('/api/admin/summary');
        const data = await res.json();

        // Update Stats
        document.getElementById('stat-users').textContent = data.total_users;
        document.getElementById('stat-interactions').textContent = data.total_interactions;
        document.getElementById('stat-time').textContent = data.total_watch_time;

        // Render Tables
        renderTable('searches-table', data.recent_searches, row => `
            <td>${row.username}</td>
            <td>"${row.query}"</td>
            <td style="color:#aaa">${new Date(row.timestamp).toLocaleTimeString()}</td>
        `);

        renderTable('interactions-table', data.recent_interactions, row => `
            <td>${row.username}</td>
            <td><span class="badge ${row.interaction_type}">${row.interaction_type}</span></td>
            <td>${row.title}</td>
            <td style="color:#aaa">${new Date(row.timestamp).toLocaleTimeString()}</td>
        `);

        // Render Charts
        renderGenreChart(data.top_genres);

    } catch (err) {
        console.error("Failed to fetch dashboard data", err);
    }
}

function renderTable(elementId, data, rowTemplate) {
    const tbody = document.getElementById(elementId);
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px;">No data</td></tr>';
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = rowTemplate(item);
        tbody.appendChild(tr);
    });
}

function renderGenreChart(data) {
    const ctx = document.getElementById('genreChart').getContext('2d');

    // Prepare Data
    const labels = data.map(d => d.genre.split('|')[0]); // Simplify genre label
    const counts = data.map(d => d.count);

    if (genreChartInstance) {
        genreChartInstance.destroy();
    }

    genreChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '# of Watches',
                data: counts,
                backgroundColor: [
                    'rgba(229, 9, 20, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)'
                ],
                borderColor: 'transparent',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#333' },
                    ticks: { color: '#aaa' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#aaa' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}
