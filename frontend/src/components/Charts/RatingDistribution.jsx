import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  Tooltip,
} from "recharts";
import { Star } from "lucide-react";

const STAR_COLORS = {
  5: "#29c75f",
  4: "#8ad40f",
  3: "#ffb11a",
  2: "#ff8a1f",
  1: "#ff4d4d",
};

const tooltipStyle = {
  background: "#0f1c34",
  border: "1px solid rgba(75, 112, 180, 0.35)",
  borderRadius: 12,
  padding: "10px 12px",
};

function DistributionTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div style={tooltipStyle}>
      <div style={{ color: "#f3f7ff", fontWeight: 700 }}>{label} star</div>
      <div style={{ color: "#8ca6cf", fontSize: "0.9rem" }}>{payload[0].value} reviews</div>
    </div>
  );
}

export default function RatingDistribution({ ratingDistribution }) {
  if (!ratingDistribution?.length) return null;

  const sorted = [...ratingDistribution].sort((a, b) => b.stars - a.stars);
  const total = sorted.reduce((sum, item) => sum + item.count, 0);

  return (
    <section className="dashboard-panel chart-card">
      <div className="chart-title">
        <Star size={18} />
        Rating Distribution
      </div>

      <div className="rating-breakdown">
        {sorted.map(({ stars, count }) => {
          const pct = total > 0 ? (count / total) * 100 : 0;

          return (
            <div key={stars} className="rating-breakdown-row">
              <div className="rating-breakdown-label">{stars}★</div>
              <div className="rating-breakdown-track">
                <div
                  className="rating-breakdown-fill"
                  style={{ width: `${pct}%`, backgroundColor: STAR_COLORS[stars] }}
                />
              </div>
              <div className="rating-breakdown-count">{count}</div>
            </div>
          );
        })}
      </div>

      <div className="rating-chart">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={[...sorted].reverse()} margin={{ top: 10, right: 10, left: -24, bottom: 0 }}>
            <XAxis
              dataKey="stars"
              tick={{ fill: "#5b769d", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => `${value}★`}
            />
            <YAxis
              tick={{ fill: "#5b769d", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<DistributionTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
            <Bar dataKey="count" radius={[8, 8, 0, 0]}>
              {[...sorted].reverse().map(({ stars }) => (
                <Cell key={stars} fill={STAR_COLORS[stars]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
