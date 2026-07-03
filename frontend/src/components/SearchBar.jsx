import { useState, useRef, useEffect } from "react";
import { Search, Zap } from "lucide-react";

const SUGGESTIONS = [
  "iPhone 15 Pro Max", "iPhone 14", "iPhone 13", "Samsung Galaxy S24 Ultra",
  "Samsung Galaxy S23", "Samsung Galaxy Z Fold 5", "vivo v27 pro", "vivo X90 Pro",
  "vivo T2 Pro", "iQOO Neo 9 Pro", "iQOO 12", "OnePlus 12", "OnePlus 11R",
  "Google Pixel 8 Pro", "Google Pixel 7a", "Sony WH-1000XM5", "Apple AirPods Pro",
  "Dell XPS 15", "MacBook Air M2", "MacBook Pro M3", "Nike Air Force 1", "Puma Sneakers"
];

export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("both");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef(null);
  const wrapperRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    setShowSuggestions(false);
    onSearch(query.trim(), source);
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    onSearch(suggestion, source);
  };

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const quickSearches = ["iPhone 15", "Samsung Galaxy", "Sony Headphones", "Dell Laptop", "Nike Shoes"];

  const filteredSuggestions = SUGGESTIONS.filter(item => 
    item.toLowerCase().includes(query.toLowerCase()) && item.toLowerCase() !== query.toLowerCase()
  ).slice(0, 5);

  return (
    <div style={{ width: "100%", maxWidth: 700, margin: "0 auto" }}>
      <form onSubmit={handleSubmit} className="search-wrapper" style={{ maxWidth: "100%", position: "relative" }} ref={wrapperRef}>
        <div style={{ position: "relative", flex: 1 }}>
          <Search size={18} className="search-icon" style={{ top: "50%", transform: "translateY(-50%)" }} />
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder="Search for a product (e.g. iPhone 15, Sony headphones...)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            disabled={loading}
          />
          
          {showSuggestions && query.trim() && filteredSuggestions.length > 0 && (
            <div style={{
              position: "absolute", top: "100%", left: 0, right: 0,
              background: "var(--bg-card)", border: "1px solid var(--border)",
              borderRadius: "0.5rem", marginTop: "0.5rem", zIndex: 10,
              boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)",
              overflow: "hidden"
            }}>
              {filteredSuggestions.map((suggestion, index) => (
                <div
                  key={index}
                  style={{
                    padding: "0.75rem 1rem", cursor: "pointer",
                    display: "flex", alignItems: "center", gap: "0.5rem",
                    borderBottom: index !== filteredSuggestions.length - 1 ? "1px solid var(--border)" : "none",
                    color: "var(--text)"
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg)"}
                  onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  <Search size={14} style={{ color: "var(--text-muted)" }} />
                  {suggestion}
                </div>
              ))}
            </div>
          )}
        </div>
        <select
          className="source-select"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          disabled={loading}
        >
          <option value="both">Both</option>
          <option value="amazon">Amazon</option>
          <option value="flipkart">Flipkart</option>
        </select>
        <button type="submit" className="btn btn-primary" disabled={loading || !query.trim()}>
          <Zap size={16} />
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {/* Quick search chips */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "1rem", justifyContent: "center" }}>
        {quickSearches.map((q) => (
          <button
            key={q}
            className="pill"
            style={{ cursor: "pointer", border: "1px solid var(--border)", background: "var(--bg-card)" }}
            onClick={() => { setQuery(q); onSearch(q, source); }}
            disabled={loading}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
