import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getProduct } from "../services/api";
import Dashboard from "../components/Dashboard";
import Loader from "../components/Loader";
import { ArrowLeft } from "lucide-react";

export default function ProductPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const result = await getProduct(id);
        setData(result);
      } catch {
        setError("Product not found or could not be loaded.");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [id]);

  if (loading) return <div className="page"><Loader text="Loading product analysis…" /></div>;

  return (
    <div className="page">
      <div className="container">
        <button className="btn btn-ghost" style={{ marginBottom: "1.5rem" }} onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Back
        </button>

        {error && <div className="alert alert-error">{error}</div>}
        {data && <Dashboard data={data} />}
      </div>
    </div>
  );
}
