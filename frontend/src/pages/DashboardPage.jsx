import { useLocation, useNavigate } from "react-router-dom";
import Dashboard from "../components/Dashboard";
import { ArrowLeft, LayoutDashboard } from "lucide-react";

export default function DashboardPage() {
  const { state } = useLocation();
  const navigate  = useNavigate();
  const data      = state?.data ?? null;

  return (
    <div className="page">
      <div className="container">
        {/* Back button */}
        <button
          className="btn btn-ghost"
          style={{ marginBottom: "1.5rem" }}
          onClick={() => navigate("/")}
        >
          <ArrowLeft size={16} /> Back to Search
        </button>

        {/* No data state */}
        {!data && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "1.25rem",
              padding: "5rem 1rem",
              textAlign: "center",
            }}
          >
            <div
              style={{
                width: 72,
                height: 72,
                borderRadius: 20,
                background: "rgba(59,130,246,0.12)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--accent-light)",
              }}
            >
              <LayoutDashboard size={34} />
            </div>
            <h2 style={{ fontSize: "1.5rem", color: "var(--text-primary)" }}>No data to display</h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: 420 }}>
              Search for a product on the Home page first — the analysis results will appear here.
            </p>
            <button className="btn btn-primary" onClick={() => navigate("/")}>
              Go to Search
            </button>
          </div>
        )}

        {/* Full Dashboard with all tabs */}
        {data && <Dashboard data={data} />}
      </div>
    </div>
  );
}
