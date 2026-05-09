# backend/main.py  — AuraEgypt API v6.0
"""
Changes from v5.1:
- SSL bypass applied to ALL requests via session (not just some)
- price_per_night passed to build_trip for accurate tier detection
- build_booking_links removed — trip_builder handles it internally now
- budget_warning surfaced in build-trip response
- version bumped to 6.0
"""

import os
import ssl
import urllib3

# Fix 1: Stop HuggingFace update checks (DNS blocked by Egyptian ISP)
# Model is already cached locally — this prevents the retry loop on startup
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE",  "1")
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".model_cache"))

# Fix 2: Egyptian ISP SSL bypass
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import json, time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from matcher         import AuraMatcher
from agent           import PharaonicAgent
from trip_builder    import build_trip
from cache_manager   import CacheManager
from social_reranker import SocialReranker
from emotion_engine  import emotion_engine
from lore_db         import lore_db
from database        import ASWAN_LOCATIONS

try:
    from visual_engine import visual_engine
    VISUAL_OK = True
except Exception:
    VISUAL_OK = False
    print("[startup] visual_engine unavailable — using default score 60")

# ── Resilient HTTP session (SSL bypass + auto-retry) ──────────────────────

def _make_session() -> requests.Session:
    s       = requests.Session()
    s.verify = False   # bypasses ISP SSL injection
    retry   = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://",  adapter)
    return s

session = _make_session()

# ── App setup ──────────────────────────────────────────────────────────────

app = FastAPI(title="AuraEgypt API", version="6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
TMDB_KEY = os.environ.get("TMDB_API_KEY", "")
B2B_KEY  = os.environ.get("B2B_API_KEY",  "aura-demo-key")

matcher  = AuraMatcher()
agent    = PharaonicAgent(GROQ_KEY)
cache    = CacheManager()
reranker = SocialReranker()

GENRE_MAP = {
    28:"Action", 12:"Adventure", 16:"Animation", 35:"Comedy", 80:"Crime",
    99:"Documentary", 18:"Drama", 10751:"Family", 14:"Fantasy", 36:"History",
    27:"Horror", 10402:"Musical", 9648:"Mystery", 10749:"Romance",
    878:"Science Fiction", 53:"Thriller",
}

# ── Helpers ────────────────────────────────────────────────────────────────

def fetch_movie(title: str) -> dict | None:
    """Fetches movie DNA from TMDB using the SSL-bypassed session."""
    try:
        r = session.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_KEY, "query": title},
            timeout=6,
        ).json()
        if not r.get("results"):
            return None
        m = r["results"][0]
        return {
            "title":    m["title"],
            "overview": m.get("overview", ""),
            "genres":   [GENRE_MAP.get(g) for g in m.get("genre_ids", [])],
            "poster":   f"https://image.tmdb.org/t/p/w500{m['poster_path']}"
                        if m.get("poster_path") else None,
        }
    except Exception as e:
        print(f"[TMDB] fetch error: {e}")
        return None


def _format_match(m: dict) -> dict:
    """Shapes a raw match result for the frontend."""
    loc = m["location"]
    return {
        "name":            loc.get("name", ""),
        "description":     loc.get("description", ""),
        "tags":            loc.get("tags", []),
        "image_url":       loc.get("image_url", ""),
        "price_per_night": loc.get("price_per_night", 0),
        "city":            loc.get("city", "Aswan"),
        "social_impact":   loc.get("social_impact", ""),
        "is_rural":        m.get("is_rural", False),
        "social_score":    m.get("social_score", 0),
        "boost_applied":   m.get("boost_applied", False),
        "boost_reason":    m.get("boost_reason", ""),
        "total_score":     m["total_score"],
        "score_breakdown": m.get("score_breakdown", {}),
        "semantic_score":  m.get("semantic_score", 0),
        "budget_score":    m.get("budget_score", 0),
        "persona_score":   m.get("persona_score", 0),
        "visual_score":    m.get("visual_score", 0),
    }


def _run_matching(emotion_query: str, genres: list, persona: str,
                  mbti: str, visual_scores: dict) -> list:
    """
    Runs Pinecone matching with automatic static DB fallback.
    Guarantees a non-empty result as long as the static DB has entries.
    """
    raw = matcher.calculate_scores(
        movie_overview=emotion_query,
        movie_genres=genres,
        budget=400, days=4,
        persona=persona, mbti=mbti,
        visual_scores=visual_scores,
    )
    if not raw:
        raw = matcher.calculate_scores_static(
            movie_overview=emotion_query,
            movie_genres=genres,
            budget=400, days=4,
            persona=persona, mbti=mbti,
            visual_scores=visual_scores,
        )
    return raw

# ── Request models ─────────────────────────────────────────────────────────

class VibeRequest(BaseModel):
    movie_title: str
    mbti:        str
    persona:     str = "Solo"

class TripRequest(BaseModel):
    movie_title:   str
    mbti:          str
    persona:       str   = "Solo"
    location_name: str
    budget:        float
    days:          int
    origin:        str   = "CAI"
    travel_date:   str   = ""

class B2BRequest(BaseModel):
    api_key:     str
    partner_id:  str
    movie_title: str
    mbti:        str
    persona:     str   = "Solo"
    budget:      float = 400
    days:        int   = 4
    origin:      str   = "CAI"

class LoreUpdateRequest(BaseModel):
    name_fragment:       str
    social_impact_score: float
    is_rural:            bool
    methodology:         str
    source:              str
    updated_by:          str
    display_name:        str = ""
    region:              str = ""

# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    cs = cache.stats()
    ls = lore_db.stats()
    return {
        "status":        "online",
        "version":       "6.0",
        "cache_entries": cs["vibe_entries"],
        "cache_hits":    cs["total_hits"],
        "lore_tiers":    ls["total_tiers"],
        "rural_tiers":   ls["rural_tiers"],
        "features": [
            "emotion_engine",
            "social_reranker_v2",
            "lore_db_dynamic",
            "b2b_api",
            "semantic_cache",
            "real_pricing_2026",
            "ssl_bypass",
        ],
    }


@app.post("/api/vibe-match")
async def vibe_match(req: VibeRequest):
    t_start   = time.time()
    agent_log = []

    # 1. TMDB
    agent_log.append({"type":"fetch",
        "message":f"Fetching TMDB data for '{req.movie_title}'"})
    dna = fetch_movie(req.movie_title)
    if not dna:
        raise HTTPException(404, "Movie not found in TMDB.")
    genres = [g for g in dna["genres"] if g]
    agent_log.append({"type":"fetch",
        "message":f"Found: '{dna['title']}' | Genres: {genres}"})

    # 2. Semantic cache
    cached = cache.get_vibe(dna["overview"], req.mbti, req.persona)
    if cached:
        agent_log.append({"type":"cache",
            "message":f"Cache HIT — {cached.get('_cache_sim')}% similar to "
                      f"'{cached.get('_cache_query','')[:40]}'"})
        cached["agent_log"]  = agent_log
        cached["latency_ms"] = round((time.time() - t_start) * 1000)
        return cached
    agent_log.append({"type":"cache","message":"Cache MISS — running full pipeline"})

    # 3. Emotional fingerprint
    agent_log.append({"type":"emotion",
        "message":f"Extracting emotional fingerprint of '{dna['title']}'"})
    emotion_data  = emotion_engine.extract(dna["title"], dna["overview"])
    emotion_query = emotion_engine.to_rich_query(emotion_data)
    agent_log.append({"type":"emotion","message":
        f"Emotions: {emotion_data.get('core_emotions',[])} | "
        f"Archetype: {emotion_data.get('traveller_archetype','')} | "
        f"Intensity: {emotion_data.get('intensity',0.6)}"})
    agent_log.append({"type":"emotion","message":
        f"Must have: {emotion_data.get('place_must_have',[])} | "
        f"Must NOT: {emotion_data.get('place_must_not_have',[])}"})

    # 4. Visual scores
    visual_scores = {}
    if VISUAL_OK:
        agent_log.append({"type":"vision","message":"Running CLIP visual scoring"})
        for loc in ASWAN_LOCATIONS:
            try:
                visual_scores[loc["name"]] = visual_engine.get_visual_score(
                    dna["title"], loc["name"]
                )
            except:
                visual_scores[loc["name"]] = 60.0

    # 5. Hybrid matching
    agent_log.append({"type":"matcher","message":
        "Scoring via emotional fingerprint — "
        "Semantic 35% + Pinecone 20% + Budget 25% + Persona 20%"})
    raw_matches = _run_matching(
        emotion_query, genres, req.persona, req.mbti, visual_scores
    )
    agent_log.append({"type":"matcher",
        "message":f"Found {len(raw_matches)} candidates above threshold"})

    if not raw_matches:
        return {"error":True,
                "message":"No portal found. Try a different film or MBTI.",
                "agent_log":agent_log}

    # 6. Social re-ranking
    agent_log.append({"type":"reranker",
        "message":"Applying social re-ranker v2 (lore_db tiers, deterministic tiebreaker)"})
    matches = reranker.rerank(raw_matches, agent_log)

    # 7. Impact summary
    impact = reranker.impact_summary(matches)
    agent_log.append({"type":"impact","message":impact["impact_statement"]})
    agent_log.append({"type":"impact","message":
        f"Methodology: {impact['methodology'].get('explanation','')[:120]}..."})

    # 8. Cleopatra narrative
    top        = matches[0]
    cached_nar = cache.get_narrative(
        top["location"]["name"], dna["title"], req.mbti
    )
    if cached_nar:
        narrative = cached_nar
        agent_log.append({"type":"agent","message":"Narrative from cache"})
    else:
        agent_log.append({"type":"agent","message":
            f"Groq: generating Cleopatra narrative for '{top['location']['name']}'"})
        narrative = agent.speak(top["location"], dna["title"], req.mbti)
        cache.set_narrative(
            top["location"]["name"], dna["title"], req.mbti, narrative
        )

    # 9. Response
    response = {
        "error":   False,
        "movie":   dna,
        "emotion_profile": {
            "core_emotions":       emotion_data.get("core_emotions", []),
            "atmosphere_words":    emotion_data.get("atmosphere_words", []),
            "traveller_archetype": emotion_data.get("traveller_archetype", ""),
            "psychological_need":  emotion_data.get("psychological_need", ""),
            "what_they_escape":    emotion_data.get("what_they_escape", ""),
            "place_must_have":     emotion_data.get("place_must_have", []),
            "place_must_not_have": emotion_data.get("place_must_not_have", []),
            "intensity":           emotion_data.get("intensity", 0.6),
            "sensory_profile":     emotion_data.get("sensory_profile", {}),
            "_cached":             emotion_data.get("_cached", False),
        },
        "matches":        [_format_match(m) for m in matches],
        "narrative":      narrative,
        "impact_summary": impact,
        "agent_log":      agent_log,
        "latency_ms":     round((time.time() - t_start) * 1000),
        "_cache_hit":     False,
    }
    cache.set_vibe(dna["overview"], response)
    return response


@app.post("/api/build-trip")
async def build_trip_endpoint(req: TripRequest):
    t_start   = time.time()
    agent_log = []

    dna = fetch_movie(req.movie_title)
    if not dna:
        raise HTTPException(404, "Movie not found.")

    # Find location in static DB, else build minimal dict
    location = next(
        (l for l in ASWAN_LOCATIONS if l["name"] == req.location_name), None
    ) or {
        "name":            req.location_name,
        "description":     "A destination in Aswan, Egypt.",
        "price_per_night": 80,
        "activities":      [],
        "social_impact":   "",
        "is_rural":        False,
        "city":            "Aswan",
        "tags":            [],
    }

    # Enrich with lore_db if not already classified
    if not location.get("is_rural"):
        text = (
            f"{location['name']} "
            f"{location.get('description','')} "
            f"{' '.join(location.get('tags',[]))}"
        )
        score, is_rural = lore_db.lookup(text)
        location = {**location,
                    "is_rural":            is_rural,
                    "social_impact_score": score}

    emotion_data = emotion_engine.extract(dna["title"], dna["overview"])
    agent_log.append({"type":"emotion","message":
        f"Trip context: {emotion_data.get('core_emotions',[][:3])}"})
    agent_log.append({"type":"trip","message":
        f"Building {req.days}-day trip to '{req.location_name}' | "
        f"budget ${req.budget} | tier will be auto-detected from price_per_night"})

    # ── KEY CHANGE: pass price_per_night so trip_builder detects tier ─────
    trip = build_trip(
        location     = location,       # includes price_per_night
        movie_title  = dna["title"],
        mbti         = req.mbti,
        budget       = req.budget,
        days         = req.days,
        origin       = req.origin,
        travel_date  = req.travel_date,
        groq_api_key = GROQ_KEY,
    )

    # Attach emotion context for frontend display
    trip["emotion_context"] = {
        "archetype":     emotion_data.get("traveller_archetype", ""),
        "escape_from":   emotion_data.get("what_they_escape", ""),
        "core_emotions": emotion_data.get("core_emotions", []),
    }

    agent_log.append({"type":"trip","message":
        f"Tier detected: {trip.get('tier','unknown')} | "
        f"Hotel: ${trip['budget_breakdown']['hotel']['cost_per_night']}/night | "
        f"Flight: ${trip['budget_breakdown']['flight']['cost']} | "
        f"Price sources: {trip.get('price_sources',{})}"})
    agent_log.append({"type":"trip","message":
        f"${trip['budget_spent']} of ${trip['budget_total']} planned | "
        f"${trip['budget_remaining']} remaining"})

    # Surface budget warning if generated
    if trip.get("budget_warning"):
        agent_log.append({"type":"trip",
            "message":f"WARNING: {trip['budget_warning']}"})

    if location.get("is_rural"):
        agent_log.append({"type":"impact",
            "message":"Rural destination — direct community booking (100% stays local)"})

    return {
        "error":      False,
        "trip":       trip,
        "agent_log":  agent_log,
        "latency_ms": round((time.time() - t_start) * 1000),
    }


# ── Lore DB endpoints ──────────────────────────────────────────────────────

@app.get("/api/lore/tiers")
def lore_get_all():
    return {"tiers": lore_db.get_all(), "stats": lore_db.stats()}

@app.get("/api/lore/audit")
def lore_audit():
    return {"audit_log": lore_db.get_audit_log(limit=50)}

@app.post("/api/lore/update")
def lore_update(req: LoreUpdateRequest):
    if not (0.0 <= req.social_impact_score <= 1.0):
        raise HTTPException(400, "social_impact_score must be 0.0–1.0")
    result = lore_db.upsert({
        "name_fragment":       req.name_fragment,
        "display_name":        req.display_name or req.name_fragment,
        "social_impact_score": req.social_impact_score,
        "is_rural":            req.is_rural,
        "methodology":         req.methodology,
        "source":              req.source,
        "region":              req.region,
    }, updated_by=req.updated_by)
    return {"success": True, "result": result}

@app.get("/api/lore/lookup")
def lore_lookup(text: str):
    score, is_rural = lore_db.lookup(text)
    return {"text": text, "social_impact_score": score, "is_rural": is_rural}


# ── B2B licensing endpoint ─────────────────────────────────────────────────

@app.post("/api/b2b/match")
async def b2b_match(req: B2BRequest):
    if req.api_key != B2B_KEY:
        raise HTTPException(403,
            "Invalid API key. Contact AuraEgypt at team@auraegypt.com.")

    dna = fetch_movie(req.movie_title)
    if not dna:
        raise HTTPException(404, "Movie not found.")

    emotion_data  = emotion_engine.extract(dna["title"], dna["overview"])
    emotion_query = emotion_engine.to_rich_query(emotion_data)
    genres        = [g for g in dna["genres"] if g]

    raw_matches = _run_matching(emotion_query, genres, req.persona, req.mbti, {})
    log     = []
    matches = reranker.rerank(raw_matches, log)
    impact  = reranker.impact_summary(matches)

    return {
        "partner":      req.partner_id,
        "movie":        dna["title"],
        "top_match":    _format_match(matches[0]) if matches else None,
        "alternatives": [_format_match(m) for m in matches[1:3]],
        "impact":       impact,
        "emotion":      emotion_data.get("traveller_archetype", ""),
        "embed_url":    f"https://auraegypt.com/embed/{req.partner_id}",
        "powered_by":   "AuraEgypt Matching Engine v6.0",
    }


# ── Scout management ───────────────────────────────────────────────────────

@app.get("/api/scout/status")
def scout_status():
    try:
        from scout_agent import ScoutAgent
        scout = ScoutAgent()
        stats = scout.index.describe_index_stats() if scout.index else {}
        return {
            "total_locations": stats.get("total_vector_count", 0),
            "status": "online" if scout.index else "offline",
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/api/scout/run")
async def scout_run(target: int = 20):
    try:
        from scout_agent import ScoutAgent
        scout   = ScoutAgent()
        summary = scout.run(target=target)
        return {"success": True, "summary": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}




# ── Utility: Link verification + metadata audit ────────────────────────────

@app.get("/api/links/verify")
async def verify_links():
    """
    Tests that all booking links resolve (not 404 or homepage redirect).
    Called by frontend to show live/broken status on each booking button.
    """
    from travelpayouts import flight_link, hotel_link, activity_link, transfer_link
    from datetime import datetime, timedelta

    test_date    = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    test_checkout= (datetime.now() + timedelta(days=33)).strftime("%Y-%m-%d")

    links_to_test = {
        "flight_CAI":   flight_link("CAI", "ASW", test_date)["url"],
        "flight_JFK":   flight_link("JFK", "ASW", test_date)["url"],
        "hotel_aswan":  hotel_link("Aswan", test_date, test_checkout)["url"],
        "hotel_luxor":  hotel_link("Luxor", test_date, test_checkout)["url"],
        "transfer":     transfer_link("Aswan Airport", "Aswan")["url"],
        "activity":     activity_link("Aswan", "Philae Temple tour")["url"],
    }

    results = {}
    for name, url in links_to_test.items():
        if not url:
            results[name] = {"status": "community_direct", "url": None}
            continue
        try:
            r = session.head(url, allow_redirects=True, timeout=5)
            results[name] = {
                "status":       "ok" if r.status_code < 400 else "broken",
                "status_code":  r.status_code,
                "final_url":    r.url,
                "url":          url,
                "is_homepage":  _is_homepage(r.url, url),
            }
        except Exception as e:
            results[name] = {"status": "error", "error": str(e), "url": url}

    all_ok = all(
        v.get("status") in ("ok", "community_direct")
        and not v.get("is_homepage", False)
        for v in results.values()
    )
    return {"all_ok": all_ok, "links": results, "tested_at": datetime.now().isoformat()}


def _is_homepage(final_url: str, original_url: str) -> bool:
    """Detects if a link redirected back to the site homepage."""
    from urllib.parse import urlparse
    try:
        orig_path  = urlparse(original_url).path
        final_path = urlparse(final_url).path
        # If final path is "/" or "" but original had a real path, it's a homepage redirect
        return final_path in ("/", "") and orig_path not in ("/", "")
    except:
        return False


@app.get("/api/metadata/audit")
async def metadata_audit():
    """
    Audits all Pinecone + static DB locations for missing metadata.
    Flags entries that need the Scout Agent to enrich them.
    Returns actionable list: which locations need image_url, description, price.
    """
    from travelpayouts import verify_location_metadata

    all_locations = list(ASWAN_LOCATIONS)

    # Also pull from Pinecone if available
    try:
        from scout_agent import ScoutAgent
        scout    = ScoutAgent()
        pinecone_locs = scout.query("egypt travel destination", top_k=50)
        all_locations += pinecone_locs
    except Exception as e:
        print(f"[Audit] Pinecone unavailable: {e}")

    verified  = verify_location_metadata(all_locations)
    flagged   = [v for v in verified if not v["metadata_ok"]]
    ok        = [v for v in verified if v["metadata_ok"]]

    return {
        "total":           len(verified),
        "ok":              len(ok),
        "flagged":         len(flagged),
        "flagged_locations": [
            {
                "name":   f.get("name", "unknown"),
                "issues": f["metadata_issues"],
                "city":   f.get("city", ""),
            }
            for f in flagged
        ],
        "recommendation": (
            f"Run POST /api/scout/run to enrich {len(flagged)} flagged locations."
            if flagged else "All locations have complete metadata."
        ),
    }

# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("AuraEgypt API v6.0 starting on port 8005...")
    uvicorn.run(app, host="0.0.0.0", port=8005)