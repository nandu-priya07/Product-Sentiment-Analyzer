import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { ChartPie } from "lucide-react";

const COLORS = {
  Positive: "#22c55e",
  Negative: "#ff5757",
  Neutral: "#ffb11a",
};

export default function SentimentPie({ summary }) {
  if (!summary) return null;

  const data = [
    { name: "Positive", value: summary.positive_count || 0 },
    { name: "Negative", value: summary.negative_count || 0 },
    { name: "Neutral", value: summary.neutral_count || 0 },
  ].filter((item) => item.value > 0);

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const positiveShare = total > 0
    ? Math.round(((summary.positive_count || 0) / total) * 100)
    : 0;

  return (
    <section className="dashboard-panel chart-card">
      <div className="chart-title">
        <ChartPie size={18} />
        Sentiment Distribution
      </div>

      <div className="sentiment-donut-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={88}
              outerRadius={138}
              startAngle={90}
              endAngle={-270}
              strokeWidth={2}
              labelLine={false}
            >
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[entry.name]}
                  stroke="#10203a"
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        <div className="sentiment-donut-center">
          <div className="sentiment-donut-value">{positiveShare}%</div>
        </div>
      </div>

      <div className="sentiment-legend">
        {[
          { label: "Positive", color: COLORS.Positive },
          { label: "Negative", color: COLORS.Negative },
          { label: "Neutral", color: COLORS.Neutral },
        ]
          .filter(({ label }) => data.some((item) => item.name === label))
          .map(({ label, color }) => (
            <div key={label} className="sentiment-legend-item">
              <span className="sentiment-legend-dot" style={{ backgroundColor: color }} />
              <span>{label}</span>
            </div>
          ))}
      </div>
    </section>
  );
}
