import { useOutletContext } from "react-router-dom";
import SentimentPie from "../../components/Charts/SentimentPie";
import RatingDistribution from "../../components/Charts/RatingDistribution";

export default function OverviewTab() {
  const { summary, ratingDistribution } = useOutletContext();
  return (
    <div className="dashboard-chart-grid fade-in">
      <SentimentPie summary={summary} />
      <RatingDistribution ratingDistribution={ratingDistribution} />
    </div>
  );
}
