// static/js/dashboard.js

// --- Chart 1: Emotion Distribution (Bar Chart) ---

function getEmotionCounts(data) {
    const counts = {
        "Happy/Engaged": 0,
        "Neutral/Calm": 0,
        "Confused": 0,
        "Bored/Drowsy": 0,
        "Frustrated/Stressed": 0,
    };

    data.forEach(entry => {
        const emotionKey = entry.emotion;
        if (counts.hasOwnProperty(emotionKey)) {
            counts[emotionKey]++;
        }
    });
    return counts;
}

function renderEmotionChart(counts) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    
    // Consistent color mapping with CSS
    const backgroundColors = [
        'rgba(0, 128, 128, 0.7)',  // Happy/Engaged (Teal)
        'rgba(201, 203, 207, 0.7)', // Neutral/Calm (Grey)
        'rgba(255, 159, 64, 0.7)', // Confused (Orange)
        'rgba(54, 162, 235, 0.7)', // Bored/Drowsy (Blue)
        'rgba(217, 83, 79, 0.7)'   // Frustrated/Stressed (Red)
    ];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                label: 'Number of Students',
                data: Object.values(counts),
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
}


// --- Chart 2: Confusion Index Trend (Line Chart) ---

async function fetchAndRenderTrendChart() {
    try {
        const response = await fetch('/api/time_series_data');
        const trendData = await response.json();
        
        if (trendData.length === 0) return;

        const dates = trendData.map(d => d.date);
        const indices = trendData.map(d => d.confusion_index);

        const ctx = document.getElementById('trendChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Daily Confusion Index (0.0 = Low, 1.0 = High)',
                    data: indices,
                    fill: true, // Fill the area under the line
                    backgroundColor: 'rgba(217, 83, 79, 0.2)', // Light red area
                    borderColor: 'rgb(217, 83, 79)', // Red line
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        min: 0,
                        max: 1.0,
                        title: { display: true, text: 'Confusion Index' }
                    },
                    x: {
                        title: { display: true, text: 'Date' }
                    }
                },
                plugins: {
                    title: { display: true, text: 'Learning Difficulty Trend Over Time' }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching trend data:", error);
    }
}


// --- Raw Feedback List Display ---

function displayRawFeedback(data) {
    const list = document.getElementById('feedback-list');
    list.innerHTML = ''; 
    
    if (data.length === 0) {
        list.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-light);"><div style="font-size: 3rem; margin-bottom: 1rem;">📝</div><p>No feedback data available yet. Start by submitting some feedback!</p></div>';
        return;
    }
    
    data.reverse().slice(0, 10).forEach((entry, index) => { 
        const feedbackItem = document.createElement('div');
        feedbackItem.style.cssText = `
            background: rgba(255, 255, 255, 0.8);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid var(--primary-color);
            transition: var(--transition);
            animation: fadeInUp 0.6s ease-out;
            animation-delay: ${index * 0.1}s;
            animation-fill-mode: both;
        `;
        
        // Format timestamp from seconds to a readable string
        const timeStr = new Date(entry.timestamp * 1000).toLocaleString();
        const emotionClass = entry.emotion.toLowerCase().replace(/[\/ ]/g, '-');
        
        feedbackItem.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <span class="emotion-tag emotion-${emotionClass}" style="font-size: 0.9rem; padding: 0.5rem 1rem;">${entry.emotion}</span>
                    <span style="color: var(--text-light); font-size: 0.9rem;">${timeStr}</span>
                </div>
            </div>
            <div style="margin-bottom: 1rem;">
                <strong style="color: var(--text-color);">Feedback:</strong>
                <p style="margin: 0.5rem 0; color: var(--text-light); font-style: italic; background: rgba(255, 255, 255, 0.5); padding: 1rem; border-radius: 8px;">"${entry.feedback}"</p>
            </div>
            <div style="background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 8px; border-left: 3px solid var(--primary-color);">
                <strong style="color: var(--text-color);">AI Analysis:</strong>
                <p style="margin: 0.5rem 0; color: var(--text-light);">${entry.reasoning}</p>
            </div>
        `;
        
        feedbackItem.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = 'var(--shadow-hover)';
        });
        
        feedbackItem.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
        
        list.appendChild(feedbackItem);
    });
}


// --- Main Execution ---
document.addEventListener('DOMContentLoaded', () => {
    // 1. Render Bar Chart
    const counts = getEmotionCounts(rawFeedbackData);
    renderEmotionChart(counts);

    // 2. Fetch and Render Line Chart
    fetchAndRenderTrendChart();

    // 3. Display Raw Data
    displayRawFeedback(rawFeedbackData);
});