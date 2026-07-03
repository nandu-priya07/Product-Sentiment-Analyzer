import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Hash } from "lucide-react";

const COLORS = { all: "#3b82f6", positive: "#22c55e", negative: "#ef4444" };

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 10, padding: "0.6rem 1rem" }}>
      <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 2 }}>"{label}"</div>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>{payload[0].value} occurrences</div>
    </div>
  );
};

export default function WordFrequency({ wordFrequency }) {
  const [mode, setMode] = useState("all");

  if (!wordFrequency) return null;

  const data = (wordFrequency[mode] || []).slice(0, 15);
  const color = COLORS[mode];

  return (
    <div className="chart-card fade-in">
      <div className="chart-title"><Hash size={18} />Word Frequency</div>

      <div className="tabs" style={{ marginBottom: "1rem" }}>
        {["all", "positive", "negative"].map((m) => (
          <button key={m} className={`tab ${mode === m ? "active" : ""}`} onClick={() => setMode(m)}
            style={mode === m ? { color: COLORS[m], borderBottomColor: COLORS[m] } : {}}>
            {m.charAt(0).toUpperCase() + m.slice(1)}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
          <XAxis type="number" tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="word" width={80} tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="count" radius={[0, 6, 6, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={color}
                fillOpacity={1 - i * 0.04}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
