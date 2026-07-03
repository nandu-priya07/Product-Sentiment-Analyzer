export default function Loader({ text = "Analyzing reviews..." }) {
  return (
    <div className="loader-wrapper">
      <div className="spinner" />
      <p className="loading-text">{text}</p>
    </div>
  );
}
