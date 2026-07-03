import { useOutletContext } from "react-router-dom";
import ReviewList from "../../components/ReviewList";

export default function ReviewsTab() {
  const { reviews } = useOutletContext();
  return (
    <div className="fade-in">
      <ReviewList reviews={reviews} />
    </div>
  );
}
