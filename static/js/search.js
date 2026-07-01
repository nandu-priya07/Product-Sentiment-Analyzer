/**
 * Product Sentiment Analyzer - Search Module
 * Handles search page functionality
 */

// Initialize search filters
function initializeSearchFilters() {
    const sentimentFilter = document.getElementById('searchSentiment');
    const ratingFilter = document.getElementById('searchRating');
    const searchInput = document.getElementById('searchFilter');

    if (sentimentFilter) {
        sentimentFilter.addEventListener('change', () => {
            filterSearchResults();
        });
    }

    if (ratingFilter) {
        ratingFilter.addEventListener('change', () => {
            filterSearchResults();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            filterSearchResults();
        });
    }
}

// Filter search results
function filterSearchResults() {
    const sentiment = document.getElementById('searchSentiment')?.value || '';
    const rating = document.getElementById('searchRating')?.value || '';
    const searchText = document.getElementById('searchFilter')?.value.toLowerCase() || '';

    const results = document.querySelectorAll('.search-result-item');

    results.forEach(result => {
        let show = true;

        // Filter by sentiment
        if (sentiment && !result.dataset.sentiment?.includes(sentiment)) {
            show = false;
        }

        // Filter by rating
        if (rating && parseInt(result.dataset.rating) !== parseInt(rating)) {
            show = false;
        }

        // Filter by search text
        if (searchText && !result.textContent.toLowerCase().includes(searchText)) {
            show = false;
        }

        result.style.display = show ? '' : 'none';
    });

    updateResultsCount();
}

// Update search results count
function updateResultsCount() {
    const results = document.querySelectorAll('.search-result-item:not([style*="display: none"])');
    const countElement = document.getElementById('resultsCount');

    if (countElement) {
        countElement.textContent = results.length + (results.length === 1 ? ' result' : ' results');
    }
}

// Load search suggestions
async function loadSearchSuggestions(query) {
    try {
        const response = await fetch(`/api/reviews?search=${query}&per_page=5`);
        const data = await response.json();

        if (data.success) {
            const suggestionsList = document.getElementById('suggestionsList');
            if (!suggestionsList) return;

            suggestionsList.innerHTML = '';

            if (data.data.length === 0) {
                suggestionsList.innerHTML = '<p class="text-muted small">No suggestions found</p>';
                return;
            }

            data.data.forEach(review => {
                const suggestion = document.createElement('div');
                suggestion.className = 'suggestion-item p-2 cursor-pointer border-bottom small';
                suggestion.innerHTML = `
                    <strong>${review.product_name}</strong><br>
                    <span class="text-muted">${truncateText(review.review_text, 60)}</span>
                `;
                suggestion.addEventListener('click', () => {
                    selectSuggestion(review.product_name);
                });
                suggestionsList.appendChild(suggestion);
            });
        }
    } catch (error) {
        console.error('Error loading suggestions:', error);
    }
}

// Select suggestion
function selectSuggestion(productName) {
    const productInput = document.getElementById('productName');
    if (productInput) {
        productInput.value = productName;
        const suggestionsList = document.getElementById('suggestionsList');
        if (suggestionsList) suggestionsList.innerHTML = '';
    }
}

// Clear search
function clearSearch() {
    document.getElementById('sentimentFilter').value = '';
    document.getElementById('ratingFilter').value = '';
    document.getElementById('searchFilter').value = '';
    filterSearchResults();
}

// Recent searches management
class RecentSearches {
    constructor(storageKey = 'recentSearches', maxItems = 5) {
        this.storageKey = storageKey;
        this.maxItems = maxItems;
    }

    add(productName, platform = 'amazon') {
        const searches = this.getAll();
        const newSearch = { product: productName, platform: platform, timestamp: new Date().toISOString() };

        // Remove duplicate
        searches = searches.filter(s => s.product !== productName || s.platform !== platform);

        // Add new search at beginning
        searches.unshift(newSearch);

        // Keep only max items
        searches = searches.slice(0, this.maxItems);

        localStorage.setItem(this.storageKey, JSON.stringify(searches));
        return searches;
    }

    getAll() {
        try {
            const searches = localStorage.getItem(this.storageKey);
            return searches ? JSON.parse(searches) : [];
        } catch (e) {
            console.error('Error retrieving recent searches:', e);
            return [];
        }
    }

    clear() {
        localStorage.removeItem(this.storageKey);
    }

    display(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const searches = this.getAll();

        if (searches.length === 0) {
            element.innerHTML = '<p class="text-muted">No recent searches</p>';
            return;
        }

        let html = '';
        searches.forEach(search => {
            html += `
                <div class="recent-search-item p-2 border-bottom cursor-pointer small">
                    <strong>${search.product}</strong>
                    <span class="badge bg-secondary ms-2">${search.platform}</span>
                    <small class="text-muted float-end">${formatTimeAgo(search.timestamp)}</small>
                </div>
            `;
        });

        element.innerHTML = html;

        // Add click handlers
        element.querySelectorAll('.recent-search-item').forEach(item => {
            item.addEventListener('click', function() {
                const product = this.querySelector('strong').textContent;
                selectSuggestion(product);
            });
        });
    }
}

// Helper: Format time ago
function formatTimeAgo(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = (now - date) / 1000;

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + 'd ago';

    return date.toLocaleDateString();
}

// Helper: Truncate text
function truncateText(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Validate search input
function validateSearchInput(productName) {
    if (!productName || productName.trim().length === 0) {
        showToast('Please enter a product name', 'warning');
        return false;
    }

    if (productName.length > 500) {
        showToast('Product name is too long (max 500 characters)', 'warning');
        return false;
    }

    return true;
}

// Advanced search
function advancedSearch() {
    const productName = document.getElementById('advancedSearchProduct')?.value || '';
    const sentiment = document.getElementById('advancedSearchSentiment')?.value || '';
    const minRating = document.getElementById('advancedSearchMinRating')?.value || '';
    const maxRating = document.getElementById('advancedSearchMaxRating')?.value || '';

    const params = new URLSearchParams();
    if (productName) params.append('product', productName);
    if (sentiment) params.append('sentiment', sentiment);
    if (minRating) params.append('min_rating', minRating);
    if (maxRating) params.append('max_rating', maxRating);

    window.location.href = `/api/reviews?${params}`;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSearchFilters();

    // Setup recent searches display
    const recentSearches = new RecentSearches();
    recentSearches.display('recentSearchesList');

    // Add search input autocomplete
    const searchInput = document.getElementById('productName');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            if (this.value.length >= 2) {
                loadSearchSuggestions(this.value);
            }
        });
    }
});

// Export for use in other scripts
window.recentSearchesManager = new RecentSearches();
