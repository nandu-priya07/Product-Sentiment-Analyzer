import { useOutletContext } from "react-router-dom";
import WordFrequency from "../../components/Charts/WordFrequency";

export default function WordsTab() {
  const { wordFrequency } = useOutletContext();
  return (
    <div className="dashboard-chart-grid dashboard-chart-grid-single fade-in">
      <WordFrequency wordFrequency={wordFrequency} />
    </div>
  );
}
