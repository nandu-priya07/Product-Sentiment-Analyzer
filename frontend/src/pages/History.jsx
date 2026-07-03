import { useState, useEffect } from "react";
import { getAllProducts, deleteProduct, scrapeProduct } from "../services/api";
import { useNavigate } from "react-router-dom";
import Loader from "../components/Loader";
import SentimentBadge from "../components/SentimentBadge";
import { Trash2, RefreshCw, Clock, Search, History as HistoryIcon } from "lucide-react";

export default function History() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [deleting, setDeleting] = useState(null);
  const navigate = useNavigate();

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getAllProducts();
      setProducts(data.products || []);
    } catch {
      setError("Could not load history. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHistory(); }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    setDeleting(id);
    try {
      await deleteProduct(id);
      setProducts((prev) => prev.filter((p) => p._id !== id));
    } catch {
      alert("Failed to delete product.");
    } finally {
      setDeleting(null);
    }
  };

  const handleRowClick = (id) => {
    navigate(`/product/${id}`);
  };

  if (loading) return <div className="page"><Loader text="Loading search history…" /></div>;

  return (
    <div className="page">
      <div className="container">
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2rem" }}>
          <div>
            <h1 style={{ fontSize: "1.8rem", display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <HistoryIcon size={28} style={{ color: "var(--accent)" }} />
              Search History
            </h1>
            <p style={{ color: "var(--text-secondary)", marginTop: "0.25rem" }}>
              All previously analyzed products
            </p>
          </div>
          <button className="btn btn-ghost" onClick={fetchHistory}>
            <RefreshCw size={15} /> Refresh
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {!error && products.length === 0 && (
          <div className="empty-state card">
            <div className="empty-state-icon">🔍</div>
            <h3>No search history yet</h3>
            <p>Start by searching for a product on the home page.</p>
            <button className="btn btn-primary" style={{ marginTop: "1rem" }} onClick={() => navigate("/")}>
              <Search size={15} /> Search Products
            </button>
          </div>
        )}

        {products.length > 0 && (
          <div className="card" style={{ padding: 0, overflow: "hidden" }}>
            <table className="history-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Sentiment</th>
                  <th>Reviews</th>
                  <th>Source</th>
                  <th>Scraped</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr
                    key={p._id}
                    onClick={() => handleRowClick(p._id)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>
                      <div style={{ fontWeight: 600, color: "var(--text-primary)", maxWidth: 280 }}>
                        {p.title ?? p.search_query}
                      </div>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 2 }}>
                        "{p.search_query}"
                      </div>
                    </td>
                    <td>
                      {p.sentiment_summary?.overall_sentiment ? (
                        <div>
                          <SentimentBadge sentiment={p.sentiment_summary.overall_sentiment} />
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 3 }}>
                            Score: {p.sentiment_summary.avg_compound?.toFixed(3)}
                          </div>
                        </div>
                      ) : "—"}
                    </td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {p.sentiment_summary?.total_reviews ?? "—"}
                    </td>
                    <td>
                      <span style={{
                        fontSize: "0.78rem", padding: "0.2rem 0.6rem",
                        borderRadius: 999, background: "var(--bg-secondary)",
                        color: "var(--text-muted)", textTransform: "capitalize"
                      }}>
                        {p.source}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--text-muted)", fontSize: "0.78rem" }}>
                        <Clock size={12} />
                        {p.scraped_at
                          ? new Date(p.scraped_at).toLocaleDateString()
                          : "N/A"}
                      </div>
                    </td>
                    <td>
                      <button
                        className="btn btn-danger"
                        style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                        onClick={(e) => handleDelete(p._id, e)}
                        disabled={deleting === p._id}
                      >
                        <Trash2 size={13} />
                        {deleting === p._id ? "…" : ""}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
