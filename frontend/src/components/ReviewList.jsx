import { useMemo, useState } from "react";
import SentimentBadge from "./SentimentBadge";
import { CheckCircle, Search, SlidersHorizontal, ThumbsUp } from "lucide-react";

function Stars({ rating }) {
  return (
    <div className="star-display">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`star${i > rating ? " empty" : ""}`}>★</span>
      ))}
    </div>
  );
}

function scoreColor(sentiment) {
  if (sentiment === "Positive") return "var(--positive)";
  if (sentiment === "Negative") return "var(--negative)";
  return "var(--neutral)";
}

export default function ReviewList({ reviews }) {
  const [visibleCount, setVisibleCount] = useState(10);
  const [query, setQuery] = useState("");
  const [sentimentFilter, setSentimentFilter] = useState("all");
  const [ratingFilter, setRatingFilter] = useState("all");
  const [sortBy, setSortBy] = useState("helpful");

  const filteredReviews = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    const next = reviews.filter((review) => {
      const matchesQuery = !normalizedQuery || [
        review.reviewer,
        review.text,
        review.date,
      ].some((value) => String(value ?? "").toLowerCase().includes(normalizedQuery));

      const matchesSentiment = sentimentFilter === "all" || review.sentiment === sentimentFilter;
      const matchesRating = ratingFilter === "all" || Number(review.rating ?? 0) === Number(ratingFilter);

      return matchesQuery && matchesSentiment && matchesRating;
    });

    next.sort((a, b) => {
      if (sortBy === "latest") return String(b.date ?? "").localeCompare(String(a.date ?? ""));
      if (sortBy === "highest") return Number(b.rating ?? 0) - Number(a.rating ?? 0);
      if (sortBy === "lowest") return Number(a.rating ?? 0) - Number(b.rating ?? 0);
      return Number(b.helpful_votes ?? 0) - Number(a.helpful_votes ?? 0);
    });

    return next;
  }, [query, ratingFilter, reviews, sentimentFilter, sortBy]);

  const visible = filteredReviews.slice(0, visibleCount);

  if (!reviews || reviews.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">💬</div>
        <h3>No reviews yet</h3>
        <p>Search for a product to see its reviews here.</p>
      </div>
    );
  }

  return (
    <div className="reviews-panel">
      <div className="reviews-toolbar">
        <div className="reviews-search">
          <Search size={16} />
          <input
            type="text"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setVisibleCount(10);
            }}
            placeholder="Search reviews, reviewer, or date"
          />
        </div>

        <div className="reviews-filters">
          <div className="reviews-filter">
            <SlidersHorizontal size={14} />
            <select
              value={sentimentFilter}
              onChange={(event) => {
                setSentimentFilter(event.target.value);
                setVisibleCount(10);
              }}
            >
              <option value="all">All sentiments</option>
              <option value="Positive">Positive</option>
              <option value="Neutral">Neutral</option>
              <option value="Negative">Negative</option>
            </select>
          </div>

          <div className="reviews-filter">
            <select
              value={ratingFilter}
              onChange={(event) => {
                setRatingFilter(event.target.value);
                setVisibleCount(10);
              }}
            >
              <option value="all">All ratings</option>
              <option value="5">5 stars</option>
              <option value="4">4 stars</option>
              <option value="3">3 stars</option>
              <option value="2">2 stars</option>
              <option value="1">1 star</option>
            </select>
          </div>

          <div className="reviews-filter">
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value)}
            >
              <option value="helpful">Most helpful</option>
              <option value="latest">Latest</option>
              <option value="highest">Highest rating</option>
              <option value="lowest">Lowest rating</option>
            </select>
          </div>
        </div>
      </div>

      <div className="reviews-summary">
        Showing {visible.length} of {filteredReviews.length} filtered reviews from {reviews.length} total
      </div>

      {filteredReviews.length === 0 ? (
        <div className="empty-state chart-card">
          <div className="empty-state-icon">🔎</div>
          <h3>No reviews match these filters</h3>
          <p>Broaden the search text or clear one of the filters.</p>
        </div>
      ) : (
        <>
          <div className="review-list">
            {visible.map((review, i) => (
              <div key={i} className="review-item fade-in" style={{ animationDelay: `${i * 0.04}s` }}>
                <div className="review-meta">
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: "50%",
                        background: `hsl(${((review.reviewer?.charCodeAt(0) ?? 0) * 17) % 360}, 60%, 40%)`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.82rem",
                        fontWeight: 700,
                        color: "#fff",
                        flexShrink: 0,
                      }}
                    >
                      {(review.reviewer ?? "A")[0].toUpperCase()}
                    </div>
                    <div>
                      <div className="review-author">
                        {review.reviewer ?? "Anonymous"}
                        {review.verified && (
                          <CheckCircle size={12} style={{ marginLeft: 4, color: "var(--positive)", verticalAlign: "middle" }} />
                        )}
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                        <Stars rating={review.rating ?? 3} />
                        <span className="review-date">{review.date}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <SentimentBadge sentiment={review.sentiment} />
                    {(review.helpful_votes ?? 0) > 0 && (
                      <span className="review-helpful">
                        <ThumbsUp size={11} />
                        {review.helpful_votes}
                      </span>
                    )}
                  </div>
                </div>

                <p className="review-text">{review.text}</p>

                {review.compound_score !== undefined && (
                  <div className="review-score-row">
                    <div className="review-score-track">
                      <div
                        className="review-score-fill"
                        style={{
                          width: `${Math.min(100, Math.abs(review.compound_score) * 100)}%`,
                          background: scoreColor(review.sentiment),
                        }}
                      />
                    </div>
                    <span className="review-score-value">
                      {review.compound_score?.toFixed(3)}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {visibleCount < filteredReviews.length && (
            <button
              type="button"
              className="btn btn-ghost reviews-load-more"
              onClick={() => setVisibleCount((count) => count + 10)}
            >
              Load more ({filteredReviews.length - visibleCount} remaining)
            </button>
          )}
        </>
      )}
    </div>
  );
}
