import {
  XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart, Dot
} from "recharts";
import { TrendingUp } from "lucide-react";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const score = payload[0]?.value;
  const color = score >= 0.05 ? "#22c55e" : score <= -0.05 ? "#ef4444" : "#f59e0b";
  const label2 = score >= 0.05 ? "Positive" : score <= -0.05 ? "Negative" : "Neutral";
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 10, padding: "0.6rem 1rem" }}>
      <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginBottom: 4 }}>{label}</div>
      <div style={{ fontWeight: 700, color }}>Score: {score?.toFixed(3)}</div>
      <div style={{ color, fontSize: "0.8rem", marginTop: 2 }}>{label2}</div>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
        {payload[1]?.value} review{payload[1]?.value !== 1 ? "s" : ""}
      </div>
    </div>
  );
};

const CustomDot = (props) => {
  const { cx, cy, payload } = props;
  const color = payload.score >= 0.05 ? "#22c55e" : payload.score <= -0.05 ? "#ef4444" : "#f59e0b";
  return <circle cx={cx} cy={cy} r={4} fill={color} stroke="var(--bg-primary)" strokeWidth={2} />;
};

const CustomActiveDot = (props) => {
  const { cx, cy, payload } = props;
  const color = payload.score >= 0.05 ? "#22c55e" : payload.score <= -0.05 ? "#ef4444" : "#f59e0b";
  return <circle cx={cx} cy={cy} r={6} fill={color} stroke="var(--bg-primary)" strokeWidth={2} />;
};

export default function SentimentTrend({ trend }) {
  if (!trend || trend.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title"><TrendingUp size={18} /> Sentiment Trend Over Time</div>
        <div className="empty-state">
          <div className="empty-state-icon">📈</div>
          <h3>No trend data available</h3>
          <p>Reviews need valid dates to build a trend chart. Try searching again.</p>
        </div>
      </div>
    );
  }

  // Show last 30 data points, format label smartly
  const isWeekly = trend.length <= 26 && trend.some(d => {
    // Weekly data has Monday dates — just check if we have spread data
    return true;
  });

  const data = trend.slice(-30).map((d) => ({
    date: d.date?.slice(5) ?? d.date,  // MM-DD
    score: d.avg_sentiment,
    reviews: d.review_count,
  }));

  // Compute Y-axis domain with some padding
  const scores = data.map(d => d.score);
  const minScore = Math.min(...scores, -0.1);
  const maxScore = Math.max(...scores, 0.1);
  const yMin = Math.max(-1, minScore - 0.1);
  const yMax = Math.min(1, maxScore + 0.1);

  // Determine gradient color based on overall trend
  const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
  const gradColor = avgScore >= 0.05 ? "#22c55e" : avgScore <= -0.05 ? "#ef4444" : "#f59e0b";

  return (
    <div className="chart-card fade-in">
      <div className="chart-title"><TrendingUp size={18} /> Sentiment Trend Over Time</div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={gradColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={gradColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => v.toFixed(2)}
          />
          <ReferenceLine y={0}    stroke="rgba(255,255,255,0.15)" strokeDasharray="4" />
          <ReferenceLine y={0.05}  stroke="rgba(34,197,94,0.3)"   strokeDasharray="4" label={{ value: "+", fill: "#22c55e", fontSize: 10, position: "insideTopRight" }} />
          <ReferenceLine y={-0.05} stroke="rgba(239,68,68,0.3)"   strokeDasharray="4" label={{ value: "−", fill: "#ef4444", fontSize: 10, position: "insideBottomRight" }} />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="score"
            stroke={gradColor}
            strokeWidth={2.5}
            fill="url(#sentGrad)"
            dot={<CustomDot />}
            activeDot={<CustomActiveDot />}
          />
          {/* Hidden line for reviews count — used in tooltip */}
          <Area type="monotone" dataKey="reviews" stroke="transparent" fill="none" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
