# 🔍 SentiScope — Product Sentiment Analyzer & Review Dashboard

A full-stack web application that scrapes product reviews from **Amazon** and **Flipkart**, performs **AI-powered sentiment analysis**, and visualizes insights through a beautiful interactive dashboard.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ Real-time Scraping | Scrapes Amazon & Flipkart reviews (with smart mock fallback) |
| 🧠 NLP Analysis | VADER + TextBlob sentiment classification (Positive / Negative / Neutral) |
| 📊 Sentiment Distribution | Donut pie chart with color-coded breakdown |
| 📈 Trend Analysis | Area chart showing sentiment score over time |
| 🔤 Word Frequency | Top keywords from all, positive, and negative reviews |
| ⭐ Rating Distribution | Star rating breakdown with visual bars |
| 🗂️ Search History | MongoDB-backed history of all analyzed products |
| 📱 Responsive Design | Mobile-friendly dark mode UI |
| ☁️ Cloud Ready | Render (backend) + Vercel (frontend) deployment configs |

---

## 🛠️ Tech Stack

**Backend:** Python, Flask, VADER Sentiment, TextBlob, BeautifulSoup4, PyMongo  
**Frontend:** React.js (Vite), Recharts, Axios, Lucide-React  
**Database:** MongoDB Atlas (free tier)  
**Deployment:** Render + Vercel

---

## 🚀 Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (Atlas cloud or local)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('stopwords')"

# Configure environment
copy .env.example .env
# Edit .env with your MongoDB URI

# Run Flask server
python app.py
# → Running on http://localhost:5000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies (already done)
npm install

# Run dev server
npm run dev
# → Running on http://localhost:5173
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scrape` | Scrape product + run sentiment analysis |
| `GET`  | `/api/products` | List all analyzed products |
| `GET`  | `/api/products/:id` | Get product + full analytics |
| `DELETE` | `/api/products/:id` | Delete product from history |
| `GET`  | `/api/sentiment/:id` | Get detailed NLP results |
| `GET`  | `/api/health` | Health check |

### Example: Scrape Request
```json
POST /api/scrape
{
  "query": "iPhone 15",
  "source": "both"
}
```

---

## ☁️ Cloud Deployment

### Backend → Render
1. Push to GitHub
2. Create new **Web Service** on [render.com](https://render.com)
3. Connect your GitHub repo, set **Root Directory** to `backend`
4. Set environment variables: `MONGO_URI`, `FLASK_SECRET_KEY`, `CORS_ORIGINS`

### Frontend → Vercel
1. Create new project on [vercel.com](https://vercel.com)
2. Connect GitHub repo, set **Root Directory** to `frontend`
3. Set env var: `VITE_API_URL=https://your-render-app.onrender.com/api`

---

## 📁 Project Structure

```
├── backend/
│   ├── app.py              # Flask entry point
│   ├── config.py           # Environment config
│   ├── requirements.txt
│   ├── routes/             # API endpoints
│   ├── services/
│   │   ├── scraper.py      # Web scraping
│   │   ├── sentiment.py    # NLP analysis
│   │   └── db.py           # MongoDB operations
├── frontend/
│   ├── src/
│   │   ├── components/     # React components + Charts
│   │   ├── pages/          # Home, History, ProductPage
│   │   └── services/api.js # API calls
├── render.yaml             # Render deployment
└── README.md
```

---

## ⚠️ Notes on Scraping

Amazon and Flipkart use aggressive bot detection. The app includes a **rich mock data fallback** so the dashboard always works. For better live scraping success:
- Use the app locally (not cloud)
- Consider Selenium with a real Chrome driver for JavaScript-heavy pages

---

## 📜 License

MIT — For educational and research purposes.
