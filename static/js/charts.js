/**
 * Product Sentiment Analyzer - Charts Module
 * Creates Chart.js visualizations for dashboard
 */

let sentimentChartInstance = null;
let ratingChartInstance = null;
let polarityChartInstance = null;
let neutralChartInstance = null;

// Create Sentiment Distribution Pie Chart
function createSentimentChart(stats) {
    const ctx = document.getElementById('sentimentChart')?.getContext('2d');
    if (!ctx) return;

    if (sentimentChartInstance) {
        sentimentChartInstance.destroy();
    }

    const data = {
        labels: ['Positive', 'Negative', 'Neutral'],
        datasets: [{
            data: [
                stats.positive_count,
                stats.negative_count,
                stats.neutral_count
            ],
            backgroundColor: [
                'rgba(40, 167, 69, 0.8)',
                'rgba(220, 53, 69, 0.8)',
                'rgba(255, 193, 7, 0.8)'
            ],
            borderColor: [
                'rgba(40, 167, 69, 1)',
                'rgba(220, 53, 69, 1)',
                'rgba(255, 193, 7, 1)'
            ],
            borderWidth: 2
        }]
    };

    sentimentChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Create Rating Distribution Bar Chart
function createRatingChart(stats) {
    const ctx = document.getElementById('ratingChart')?.getContext('2d');
    if (!ctx) return;

    if (ratingChartInstance) {
        ratingChartInstance.destroy();
    }

    const distribution = stats.rating_distribution || {};
    const labels = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'];
    const data = [
        distribution[1] || 0,
        distribution[2] || 0,
        distribution[3] || 0,
        distribution[4] || 0,
        distribution[5] || 0
    ];

    ratingChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Reviews',
                data: data,
                backgroundColor: [
                    'rgba(220, 53, 69, 0.7)',
                    'rgba(253, 126, 20, 0.7)',
                    'rgba(255, 193, 7, 0.7)',
                    'rgba(102, 187, 106, 0.7)',
                    'rgba(40, 167, 69, 0.7)'
                ],
                borderColor: [
                    'rgba(220, 53, 69, 1)',
                    'rgba(253, 126, 20, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(102, 187, 106, 1)',
                    'rgba(40, 167, 69, 1)'
                ],
                borderWidth: 2,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'x',
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Create Polarity Distribution Chart
function createPolarityChart(stats) {
    const ctx = document.getElementById('polarityChart')?.getContext('2d');
    if (!ctx) return;

    if (polarityChartInstance) {
        polarityChartInstance.destroy();
    }

    polarityChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive'],
            datasets: [{
                label: 'Polarity Score Distribution',
                data: [
                    (stats.negative_count * 0.2) || 0,
                    (stats.negative_count * 0.8) || 0,
                    (stats.neutral_count) || 0,
                    (stats.positive_count * 0.8) || 0,
                    (stats.positive_count * 0.2) || 0
                ],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#667eea'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Create Neutral Count Chart
function createNeutralChart(stats) {
    const ctx = document.getElementById('neutralChart')?.getContext('2d');
    if (!ctx) return;

    if (neutralChartInstance) {
        neutralChartInstance.destroy();
    }

    const chartData = {
        labels: ['Neutral'],
        datasets: [{
            label: 'Neutral Reviews',
            data: [stats.neutral_count || 0],
            backgroundColor: 'rgba(255, 193, 7, 0.7)',
            borderColor: 'rgba(255, 193, 7, 1)',
            borderWidth: 2
        }]
    };

    neutralChartInstance = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Create custom chart
function createCustomChart(canvasId, type, labels, data, options = {}) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return null;

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };

    return new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: data
        },
        options: { ...defaultOptions, ...options }
    });
}

// Utility: Get chart colors
function getChartColors(type = 'sentiment') {
    const colors = {
        sentiment: {
            positive: 'rgba(40, 167, 69, 0.8)',
            negative: 'rgba(220, 53, 69, 0.8)',
            neutral: 'rgba(255, 193, 7, 0.8)'
        },
        rating: {
            1: 'rgba(220, 53, 69, 0.7)',
            2: 'rgba(253, 126, 20, 0.7)',
            3: 'rgba(255, 193, 7, 0.7)',
            4: 'rgba(102, 187, 106, 0.7)',
            5: 'rgba(40, 167, 69, 0.7)'
        }
    };
    return colors[type] || colors.sentiment;
}

// Format chart tooltip
function formatChartTooltip(value, type = 'count') {
    if (type === 'percentage') {
        return value.toFixed(1) + '%';
    } else if (type === 'polarity') {
        return value.toFixed(3);
    }
    return Math.round(value);
}
