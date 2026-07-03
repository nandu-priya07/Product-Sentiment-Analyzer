import { useMemo, useState } from "react";
import SentimentPie from "./Charts/SentimentPie";
import SentimentTrend from "./Charts/SentimentTrend";
import WordFrequency from "./Charts/WordFrequency";
import RatingDistribution from "./Charts/RatingDistribution";
import ReviewList from "./ReviewList";
import {
  MessageSquareText,
  ChartColumn,
  TrendingUp,
  Star,
  Package2,
  ExternalLink,
  ShoppingBag,
  Download,
  FileJson,
  Sparkles,
  ShieldCheck,
  ClipboardList,
} from "lucide-react";

function formatCount(value) {
  if (value === undefined || value === null) return "0";
  return typeof value === "number" ? value.toLocaleString() : value;
}

function formatPercent(value) {
  if (value === undefined || value === null) return "0%";
  return `${value}%`;
}

function StatCard({ label, value, sub, tone = "default" }) {
  return (
    <div className={`dashboard-stat dashboard-stat-${tone}`}>
      <div className="dashboard-stat-label">{label}</div>
      <div className="dashboard-stat-value">{value}</div>
      <div className="dashboard-stat-sub">{sub}</div>
    </div>
  );
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function Dashboard({ data }) {
  const [activeTab, setActiveTab] = useState("overview");
  if (!data) return null;

  const product = data.product ?? {};
  const summary = data.summary ?? {};
  const reviews = data.reviews ?? [];
  const wordFrequency = data.word_frequency ?? null;
  const trend = data.trend ?? [];
  const ratingDistribution = data.rating_distribution ?? [];

  const analyzedCount = summary.analysis_review_count ?? summary.total_reviews ?? reviews.length;
  const marketplaceReviewCount = summary.marketplace_review_count ?? product.review_count ?? null;
  const siteRating = summary.marketplace_rating ?? product.rating ?? summary.avg_rating ?? null;
  const sourceReviewCount = marketplaceReviewCount ?? analyzedCount;

  const overallSentiment = summary.overall_sentiment ?? "Neutral";
  const sentimentTone =
    overallSentiment === "Positive" ? "positive" :
    overallSentiment === "Negative" ? "negative" :
    "neutral";

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const overviewStats = useMemo(() => ([
    {
      label: "Overall Sentiment",
      value: overallSentiment,
      sub: `Score: ${summary.avg_compound?.toFixed?.(3) ?? "0.000"}`,
      tone: sentimentTone,
    },
    {
      label: "Total Reviews",
      value: formatCount(analyzedCount),
      sub: "analyzed",
    },
    {
      label: "Positive",
      value: formatPercent(summary.positive_pct ?? 0),
      sub: `${formatCount(summary.positive_count ?? 0)} reviews`,
      tone: "positive",
    },
    {
      label: "Negative",
      value: formatPercent(summary.negative_pct ?? 0),
      sub: `${formatCount(summary.negative_count ?? 0)} reviews`,
      tone: "negative",
    },
    {
      label: "Neutral",
      value: formatPercent(summary.neutral_pct ?? 0),
      sub: `${formatCount(summary.neutral_count ?? 0)} reviews`,
      tone: "neutral",
    },
    {
      label: "Site Rating",
      value: siteRating != null ? `★ ${Number(siteRating).toFixed(1)}` : "—",
      sub: marketplaceReviewCount != null
        ? `${formatCount(marketplaceReviewCount)} source-site reviews`
        : "out of 5",
      tone: "rating",
    },
  ]), [
    analyzedCount,
    marketplaceReviewCount,
    overallSentiment,
    sentimentTone,
    siteRating,
    summary.avg_compound,
    summary.negative_count,
    summary.negative_pct,
    summary.neutral_count,
    summary.neutral_pct,
    summary.positive_count,
    summary.positive_pct,
  ]);

  const tabs = [
    { id: "overview", label: "Overview",                    icon: ChartColumn },
    { id: "reviews",  label: `Reviews (${reviews.length})`, icon: MessageSquareText },
    { id: "trends",   label: "Trends",                      icon: TrendingUp },
    { id: "words",    label: "Word Analysis",               icon: Star },
  ];

  const hasData = reviews.length > 0 || summary.total_reviews > 0;
  const coveragePct = sourceReviewCount > 0
    ? Math.min(100, Math.round((analyzedCount / sourceReviewCount) * 100))
    : 100;
  const strongestSentiment = [
    { label: "Positive", count: summary.positive_count ?? 0 },
    { label: "Negative", count: summary.negative_count ?? 0 },
    { label: "Neutral",  count: summary.neutral_count ?? 0 },
  ].sort((a, b) => b.count - a.count)[0]?.label ?? "Neutral";

  const exportBaseName = (product.title ?? "product-analysis")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

  const handleExportJson = () => {
    downloadFile(
      `${exportBaseName || "product-analysis"}.json`,
      JSON.stringify(data, null, 2),
      "application/json",
    );
  };

  const handleExportCsv = () => {
    const headers = ["reviewer", "rating", "sentiment", "compound_score", "date", "verified", "helpful_votes", "text"];
    const rows = reviews.map((review) => headers.map((key) => {
      const value = review[key] ?? "";
      const safe = String(value).replace(/"/g, "\"\"");
      return `"${safe}"`;
    }).join(","));
    const csv = [headers.join(","), ...rows].join("\n");
    downloadFile(`${exportBaseName || "product-analysis"}-reviews.csv`, csv, "text/csv;charset=utf-8");
  };

  const insights = [
    {
      icon: Sparkles,
      label: "Dominant sentiment",
      value: strongestSentiment,
    },
    {
      icon: ClipboardList,
      label: "Review coverage",
      value: `${coveragePct}%`,
    },
    {
      icon: ShieldCheck,
      label: "Data source",
      value: product.source ? String(product.source) : "Combined",
    },
  ];

  return (
    <section className="dashboard-shell fade-in">
      {/* ── Header ── */}
      <div className="dashboard-header">
        <div className="dashboard-product">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.title ?? "Product"}
              className="dashboard-product-image"
              onError={(event) => {
                event.currentTarget.style.display = "none";
              }}
            />
          ) : (
            <div className="dashboard-product-image dashboard-product-fallback">
              <Package2 size={30} />
            </div>
          )}

          <div className="dashboard-product-copy">
            <h1 className="dashboard-product-title">{product.title ?? "Product Analysis"}</h1>
            <div className="dashboard-product-meta">
              {product.price && <span className="dashboard-product-price">{product.price}</span>}
              {product.source && (
                <span className="dashboard-product-chip">
                  <ShoppingBag size={13} />
                  {product.source}
                </span>
              )}
              {product.url && (
                <a
                  href={product.url}
                  target="_blank"
                  rel="noreferrer"
                  className="dashboard-product-link"
                >
                  Open listing
                  <ExternalLink size={14} />
                </a>
              )}
            </div>
          </div>
        </div>

        {hasData && (
          <div className="dashboard-actions">
            <button type="button" className="btn btn-ghost dashboard-action-btn" onClick={handleExportCsv}>
              <Download size={16} />
              <span>CSV</span>
            </button>
            <button type="button" className="btn btn-ghost dashboard-action-btn" onClick={handleExportJson}>
              <FileJson size={16} />
              <span>JSON</span>
            </button>
          </div>
        )}
      </div>

      {!hasData && (
        <div className="alert alert-error" style={{ marginBottom: "1.5rem" }}>
          No reviews were found for analysis. Try a different search.
        </div>
      )}

      {hasData && (
        <>
          {/* ── Stat Cards ── */}
          <div className="dashboard-stats">
            {overviewStats.map((stat) => (
              <StatCard key={stat.label} {...stat} />
            ))}
          </div>

          {/* ── Insights Row ── */}
          <div className="dashboard-insights">
            {insights.map(({ icon: Icon, label, value }) => (
              <div key={label} className="dashboard-insight-card">
                <div className="dashboard-insight-icon">
                  <Icon size={16} />
                </div>
                <div className="dashboard-insight-copy">
                  <div className="dashboard-insight-label">{label}</div>
                  <div className="dashboard-insight-value">{value}</div>
                </div>
              </div>
            ))}
          </div>

          {/* ── Tab Nav ── */}
          <div className="dashboard-tabs" role="tablist" aria-label="Dashboard sections">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                id={`tab-${id}`}
                type="button"
                className={`dashboard-tab${activeTab === id ? " active" : ""}`}
                onClick={() => setActiveTab(id)}
                aria-current={activeTab === id ? "page" : undefined}
              >
                <Icon size={16} />
                <span>{label}</span>
              </button>
            ))}
          </div>

          {/* ── Tab Panels ── */}
          {activeTab === "overview" && (
            <div className="dashboard-chart-grid fade-in">
              <SentimentPie summary={summary} />
              <RatingDistribution ratingDistribution={ratingDistribution} />
            </div>
          )}

          {activeTab === "reviews" && (
            <div className="fade-in">
              <ReviewList reviews={reviews} />
            </div>
          )}

          {activeTab === "trends" && (
            <div className="dashboard-chart-grid dashboard-chart-grid-single fade-in">
              <SentimentTrend trend={trend} />
            </div>
          )}

          {activeTab === "words" && (
            <div className="dashboard-chart-grid dashboard-chart-grid-single fade-in">
              <WordFrequency wordFrequency={wordFrequency} />
            </div>
          )}
        </>
      )}
    </section>
  );
}
