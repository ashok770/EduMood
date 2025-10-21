// static/js/dashboard.js

// Function to process raw data and count emotions
function getEmotionCounts(data) {
    const counts = {
        "Happy/Engaged": 0,
        "Neutral/Calm": 0,
        "Confused": 0,
        "Bored/Drowsy": 0,
        "Frustrated/Stressed": 0,
    };

    data.forEach(entry => {
        if (counts.hasOwnProperty(entry.emotion)) {
            counts[entry.emotion]++;
        }
    });
    return counts;
}

// Function to render the Chart.js visualization
function renderEmotionChart(counts) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    
    // Define a set of colors for consistency
    const backgroundColors = [
        'rgba(75, 192, 192, 0.7)', // Happy/Engaged (Teal)
        'rgba(201, 203, 207, 0.7)', // Neutral/Calm (Grey)
        'rgba(255, 159, 64, 0.7)', // Confused (Orange)
        'rgba(54, 162, 235, 0.7)', // Bored/Drowsy (Blue)
        'rgba(255, 99, 132, 0.7)'  // Frustrated/Stressed (Red)
    ];

    new Chart(ctx, {
        type: 'bar', // Using a bar chart is a good, clear start
        data: {
            labels: Object.keys(counts),
            datasets: [{
                label: 'Number of Students',
                data: Object.values(counts),
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count of Feedback'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Class Emotion Distribution'
                }
            }
        }
    });
}

// Function to display the raw list of feedback
function displayRawFeedback(data) {
    const list = document.getElementById('feedback-list');
    data.reverse().slice(0, 10).forEach(entry => { // Show last 10 entries
        const listItem = document.createElement('li');
        listItem.innerHTML = `
            <strong>Emotion:</strong> <span class="emotion-tag">${entry.emotion}</span><br>
            <strong>Feedback:</strong> "${entry.feedback}"<br>
            <span class="reasoning-text">Reasoning: ${entry.reasoning}</span>
            <hr>
        `;
        list.appendChild(listItem);
    });
}


// --- Main Execution ---
document.addEventListener('DOMContentLoaded', () => {
    // The rawFeedbackData variable is defined in teacher_dashboard.html
    const counts = getEmotionCounts(rawFeedbackData);
    renderEmotionChart(counts);
    displayRawFeedback(rawFeedbackData);
});