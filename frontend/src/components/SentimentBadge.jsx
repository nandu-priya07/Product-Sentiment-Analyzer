import { TrendingUp, TrendingDown, Minus } from "lucide-react";

const MAP = {
  Positive: { cls: "badge-positive", icon: TrendingUp },
  Negative: { cls: "badge-negative", icon: TrendingDown },
  Neutral:  { cls: "badge-neutral",  icon: Minus },
};

export default function SentimentBadge({ sentiment }) {
  const { cls, icon: Icon } = MAP[sentiment] || MAP.Neutral;
  return (
    <span className={`badge ${cls}`}>
      <Icon size={11} />
      {sentiment}
    </span>
  );
}
