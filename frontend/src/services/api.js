import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

export const scrapeProduct = (query, source = "both") =>
  api.post("/scrape", { query, source }).then((r) => r.data);

export const getAllProducts = () =>
  api.get("/products").then((r) => r.data);

export const getProduct = (id) =>
  api.get(`/products/${id}`).then((r) => r.data);

export const deleteProduct = (id) =>
  api.delete(`/products/${id}`).then((r) => r.data);

export const getSentiment = (id) =>
  api.get(`/sentiment/${id}`).then((r) => r.data);

export const healthCheck = () =>
  api.get("/health").then((r) => r.data);

export default api;
