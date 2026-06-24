# 🏛️ AuraEgypt — AI-Powered Travel Matching Platform

> **Match your movie mood to an Egyptian destination.**
> 🌐 Live → [project-z8foo.vercel.app](https://project-z8foo.vercel.app)

AuraEgypt takes a movie title and your MBTI personality type, extracts an emotional fingerprint from the film, and matches you to real destinations across Upper Egypt and the Red Sea using a multi-signal AI scoring pipeline.

---

## ✨ How It Works

```
Movie Title + MBTI
       ↓
TMDB API — plot, genres, poster
       ↓
Emotion Engine (LLM) — core emotions, traveller archetype, atmosphere words
       ↓
Hybrid Scorer
  ├── Semantic similarity  (Sentence-Transformers + Pinecone)   35%
  ├── Budget fit                                                 25%
  ├── Persona matching (MBTI engine)                            20%
  └── CLIP visual scoring                                       20%
       ↓
Social Re-ranker — boosts rural & community destinations
       ↓
Cleopatra Narrative — Groq LLM storytelling
       ↓
Trip Builder — flights, hotels, activities, booking links
```

---

## 🏗️ Backend Modules (`/backend`)

| Module | Role |
|---|---|
| `main.py` | FastAPI app — all endpoints |
| `emotion_engine.py` | LLM-based emotional fingerprinting of movies |
| `matcher.py` | Pinecone vector search + static DB fallback |
| `mbti_engine.py` | MBTI persona scoring |
| `social_reranker.py` | Rural/community destination boost |
| `lore_db.py` | Dynamic social-impact tier database |
| `trip_builder.py` | Full budget breakdown + booking link assembly |
| `booking_engine.py` | Hotel, flight & activity booking logic |
| `travelpayouts.py` | TravelPayouts affiliate API integration |
| `cache_manager.py` | Semantic cache — avoids redundant LLM calls |
| `visual_engine.py` | CLIP image–text visual scoring |
| `agent.py` | Cleopatra narrative generation (Groq) |
| `cleopatra.py` | Narrative formatting & persona |
| `scout_agent.py` | Pinecone enrichment agent |
| `auto_data_pipeline.py` | Automated location data ingestion |
| `database.py` | Static Aswan location DB |
| `production_data.py` | Production-ready location dataset |
| `golden_map.py` | Golden-tier destination mapping |
| `itineraries.py` | Pre-built itinerary templates |
| `logistics.py` | Transfer & logistics planning |
| `affiliate_tracker.py` | Affiliate link tracking |
| `stripe_handler.py` | Stripe payment integration |
| `admin.py` | Admin panel endpoints |

---

## 🖥️ Frontend (`/frontend`)

Built with **Next.js + Tailwind CSS**

| File | Purpose |
|---|---|
| `pages/index.jsx` | Landing page — movie + MBTI input |
| `pages/[movie].jsx` | Results page — matches, narrative, trip |
| `pages/admin.jsx` | Admin dashboard |
| `components/Chat.jsx` | Cleopatra chat interface |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/vibe-match` | Movie → ranked destination matches |
| `POST` | `/api/build-trip` | Generate full trip itinerary |
| `POST` | `/api/b2b/match` | B2B partner matching endpoint |
| `GET` | `/api/health` | System health + cache stats |
| `GET` | `/api/lore/tiers` | Social impact tier database |
| `POST` | `/api/lore/update` | Update destination social score |
| `GET` | `/api/links/verify` | Verify all booking links are live |
| `GET` | `/api/metadata/audit` | Flag locations missing metadata |
| `POST` | `/api/scout/run` | Run Pinecone enrichment scout |

---

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| AI / ML | Sentence-Transformers, CLIP, Groq LLM, Pinecone |
| Data | Supabase (PostgreSQL), Pinecone vector DB |
| Frontend | Next.js, React, Tailwind CSS |
| Payments | Stripe |
| Deployment | Docker, Vercel |
| APIs | TMDB, TravelPayouts, SerpAPI |

---

## ⚙️ Setup

```bash
git clone https://github.com/Aml517/aura-egypt-v5
cd aura-egypt-v5

# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in your keys
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

**Or run both with Docker:**
```bash
cp .env.example .env   # fill in your keys
docker-compose up
```

---

## 🔑 Environment Variables

```env
GROQ_API_KEY=           # groq.com
PINECONE_API_KEY=       # pinecone.io
SUPABASE_URL=           # supabase.com project URL
SUPABASE_SERVICE_KEY=   # supabase.com service role key
TMDB_API_KEY=           # themoviedb.org
```

---

## 👩‍💻 Author

**Aml Abdelrhman Ahmed Mohamed**
B.Sc. Computer Science — AASTMT Aswan, Egypt
GPA: 3.67 / 4.0 (Excellence)

