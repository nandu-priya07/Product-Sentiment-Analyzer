import { useOutletContext } from "react-router-dom";
import SentimentTrend from "../../components/Charts/SentimentTrend";

export default function TrendsTab() {
  const { trend } = useOutletContext();
  return (
    <div className="dashboard-chart-grid dashboard-chart-grid-single fade-in">
      <SentimentTrend trend={trend} />
    </div>
  );
}
