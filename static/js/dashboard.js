/**
 * Product Sentiment Analyzer - Dashboard Module
 * Handles dashboard functionality and data loading
 */

// Load top reviews (positive and negative)
async function loadTopReviews(productName) {
    try {
        const response = await fetch(`/api/reviews?product=${productName}&sentiment=Positive&per_page=5`);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            const positiveList = document.getElementById('topPositiveList');
            positiveList.innerHTML = '';

            data.data.forEach(review => {
                const reviewElement = document.createElement('div');
                reviewElement.className = 'review-item mb-3 pb-3 border-bottom';
                reviewElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <strong class="text-success">${review.reviewer_name}</strong>
                        <span class="badge bg-success">⭐ ${review.rating}/5</span>
                    </div>
                    <p class="small mb-2">${truncateText(review.review_text, 100)}</p>
                    <small class="text-muted">Polarity: ${review.polarity.toFixed(3)}</small>
                `;
                positiveList.appendChild(reviewElement);
            });
        }

        // Load negative reviews
        const negativeResponse = await fetch(`/api/reviews?product=${productName}&sentiment=Negative&per_page=5`);
        const negativeData = negativeResponse.json();

        if (negativeData.success && negativeData.data.length > 0) {
            const negativeList = document.getElementById('topNegativeList');
            negativeList.innerHTML = '';

            negativeData.data.forEach(review => {
                const reviewElement = document.createElement('div');
                reviewElement.className = 'review-item mb-3 pb-3 border-bottom';
                reviewElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <strong class="text-danger">${review.reviewer_name}</strong>
                        <span class="badge bg-danger">⭐ ${review.rating}/5</span>
                    </div>
                    <p class="small mb-2">${truncateText(review.review_text, 100)}</p>
                    <small class="text-muted">Polarity: ${review.polarity.toFixed(3)}</small>
                `;
                negativeList.appendChild(reviewElement);
            });
        }
    } catch (error) {
        console.error('Error loading top reviews:', error);
    }
}

// Load recent reviews table
async function loadRecentReviews(productName) {
    try {
        const response = await fetch(`/api/reviews?product=${productName}&per_page=10`);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            const tableBody = document.getElementById('recentReviewsTable');
            tableBody.innerHTML = '';

            data.data.forEach(review => {
                const sentimentBadge = `
                    <span class="badge ${review.sentiment === 'Positive' ? 'bg-success' : review.sentiment === 'Negative' ? 'bg-danger' : 'bg-warning'}">
                        ${review.sentiment}
                    </span>
                `;

                const row = `
                    <tr>
                        <td>${review.reviewer_name}</td>
                        <td><small>${truncateText(review.review_text, 50)}</small></td>
                        <td>
                            <span class="badge ${getRatingBadgeClass(review.rating)}">
                                ${'⭐'.repeat(review.rating)}
                            </span>
                        </td>
                        <td>${sentimentBadge}</td>
                        <td>${review.polarity.toFixed(3)}</td>
                        <td><small>${formatDate(review.review_date)}</small></td>
                    </tr>
                `;

                tableBody.innerHTML += row;
            });
        }
    } catch (error) {
        console.error('Error loading recent reviews:', error);
    }
}

// Truncate text helper
function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Get rating badge class
function getRatingBadgeClass(rating) {
    if (rating >= 4) return 'bg-success';
    if (rating >= 3) return 'bg-warning';
    return 'bg-danger';
}

// Format date
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Get sentiment color
function getSentimentColor(sentiment) {
    switch (sentiment) {
        case 'Positive':
            return '#28a745';
        case 'Negative':
            return '#dc3545';
        case 'Neutral':
            return '#ffc107';
        default:
            return '#6c757d';
    }
}

// Get sentiment emoji
function getSentimentEmoji(sentiment) {
    switch (sentiment) {
        case 'Positive':
            return '😊';
        case 'Negative':
            return '😞';
        case 'Neutral':
            return '😐';
        default:
            return '❓';
    }
}

// Create summary card
function createSummaryCard(title, value, subtitle = '', icon = '', color = 'primary') {
    return `
        <div class="col-md-3">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <p class="text-muted small mb-1">${title}</p>
                            <h3 class="mb-0 text-${color}">${value}</h3>
                            ${subtitle ? `<small class="text-muted">${subtitle}</small>` : ''}
                        </div>
                        ${icon ? `<div class="bg-${color} bg-opacity-10 p-3 rounded"><i class="fas ${icon} text-${color} fa-lg"></i></div>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Generate summary statistics HTML
function generateSummaryStats(stats) {
    let html = '<div class="row g-4 mb-4">';

    html += createSummaryCard(
        'Total Reviews',
        stats.total_reviews,
        '',
        'fa-comments',
        'primary'
    );

    html += createSummaryCard(
        'Positive',
        stats.positive_count,
        `${stats.positive_percentage}%`,
        'fa-smile',
        'success'
    );

    html += createSummaryCard(
        'Negative',
        stats.negative_count,
        `${stats.negative_percentage}%`,
        'fa-frown',
        'danger'
    );

    html += createSummaryCard(
        'Average Rating',
        stats.average_rating,
        'out of 5',
        'fa-star',
        'warning'
    );

    html += '</div>';

    return html;
}

// Export data to CSV
async function exportToCSV(productName, sentiment = '') {
    try {
        const params = new URLSearchParams({ product: productName });
        if (sentiment) params.append('sentiment', sentiment);

        const response = await fetch(`/api/export/csv?${params}`);
        if (!response.ok) throw new Error('Export failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reviews_${productName}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast('CSV exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showToast('Error exporting CSV', 'danger');
    }
}

// Export data to JSON
async function exportToJSON(productName, sentiment = '') {
    try {
        const params = new URLSearchParams({ product: productName });
        if (sentiment) params.append('sentiment', sentiment);

        const response = await fetch(`/api/export/json?${params}`);
        const data = await response.json();

        if (!data.success) throw new Error('Export failed');

        const jsonString = JSON.stringify(data.data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reviews_${productName}_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast('JSON exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting JSON:', error);
        showToast('Error exporting JSON', 'danger');
    }
}

// Filter reviews in table
function filterReviewsInTable(filterType, filterValue) {
    const rows = document.querySelectorAll('#recentReviewsTable tr');

    rows.forEach(row => {
        let show = true;

        if (filterType === 'sentiment') {
            const sentimentCell = row.querySelector('td:nth-child(4)');
            show = sentimentCell?.textContent.includes(filterValue);
        } else if (filterType === 'rating') {
            const ratingCell = row.querySelector('td:nth-child(3)');
            show = ratingCell?.textContent.includes(filterValue);
        }

        row.style.display = show ? '' : 'none';
    });
}

// Update dashboard in real-time
function setupAutoRefresh(productName, interval = 60000) {
    setInterval(() => {
        loadDashboard(productName);
    }, interval);
}
