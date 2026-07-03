import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import Loader from "../components/Loader";
import { scrapeProduct } from "../services/api";
import { BarChart2, Shield, Zap, Globe, Brain, TrendingUp } from "lucide-react";

const FEATURES = [
  { icon: Zap,        label: "Real-time Scraping" },
  { icon: Brain,      label: "AI Sentiment Analysis" },
  { icon: BarChart2,  label: "Interactive Charts" },
  { icon: TrendingUp, label: "Historical Trends" },
  { icon: Globe,      label: "Amazon + Flipkart" },
  { icon: Shield,     label: "Secure & Fast" },
];

function getErrorMessage(err) {
  if (!err) return "An unexpected error occurred.";
  const msg = err.response?.data?.error || err.message || "";
  if (!msg || msg.includes("ERR_CONNECTION_REFUSED") || msg.includes("Network Error") || msg.includes("connect")) {
    return "Cannot connect to the backend server. Make sure the Flask server is running on port 5000.";
  }
  if (err.response?.status === 400) return `Bad request: ${msg}`;
  if (err.response?.status === 500) return `Server error: ${msg}`;
  return msg || "Failed to analyze the product. Please try again.";
}

export default function Home() {
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [lastQuery, setLastQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = async (query, source) => {
    setLoading(true);
    setError(null);
    setLastQuery(query);
    try {
      const result = await scrapeProduct(query, source);
      if (!result || (!result.reviews?.length && !result.summary)) {
        throw new Error("The server returned an empty result. Try a different product name.");
      }
      // Navigate to the Dashboard page, passing result as router state
      navigate("/dashboard", { state: { data: result } });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      {/* ── Hero ── */}
      {!loading && (
        <div className="hero">
          <div className="hero-tag">
            <BarChart2 size={14} /> AI-Powered Sentiment Analytics
          </div>
          <h1 className="hero-title">
            Understand What<br />Customers Really Think
          </h1>
          <p className="hero-subtitle">
            Scrape product reviews from Amazon &amp; Flipkart, analyze sentiment with AI,
            and visualize insights through beautiful interactive charts.
          </p>

          <SearchBar onSearch={handleSearch} loading={loading} />

          <div className="feature-pills" style={{ marginTop: "2rem" }}>
            {FEATURES.map(({ icon: Icon, label }) => (
              <div key={label} className="pill">
                <Icon size={13} style={{ color: "var(--accent)" }} />
                {label}
              </div>
            ))}
          </div>

          {/* Decorative gradient orbs */}
          <div style={{
            position: "absolute", top: "10%", left: "5%", width: 300, height: 300,
            background: "radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)",
            borderRadius: "50%", pointerEvents: "none",
          }} />
          <div style={{
            position: "absolute", bottom: "0%", right: "5%", width: 250, height: 250,
            background: "radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)",
            borderRadius: "50%", pointerEvents: "none",
          }} />
        </div>
      )}

      <div className="container">
        {/* Error */}
        {error && (
          <div className="alert alert-error fade-in" style={{ maxWidth: 700, margin: "0 auto 1.5rem" }}>
            <strong>⚠️ Error</strong><br />
            {error}
          </div>
        )}

        {/* Loader */}
        {loading && (
          <Loader text={`Scraping reviews for "${lastQuery}" and running AI sentiment analysis…`} />
        )}

        {/* Stats Footer (only on landing) */}
        {!loading && !error && (
          <div className="container" style={{ marginTop: "4rem" }}>
            <div className="stat-grid" style={{ maxWidth: 900, margin: "0 auto" }}>
              {[
                { label: "Products Analyzed",   value: "10,000+" },
                { label: "Reviews Processed",   value: "2.4M+" },
                { label: "Accuracy Rate",       value: "94.2%" },
                { label: "Supported Platforms", value: "2" },
              ].map(({ label, value }) => (
                <div key={label} className="glass-card" style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "2rem", fontWeight: 800, fontFamily: "'Space Grotesk', sans-serif", color: "var(--accent-light)" }}>{value}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>{label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
