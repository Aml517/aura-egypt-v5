# backend/scout_agent.py
"""
Scout Agent — autonomous Egyptian location discovery.

FIXES vs previous version:
1. Diverse, specific queries so Pinecone gets varied content
2. Name-normalisation before dedup (handles "Karnak" vs "Karnak Temple")
3. Snippet-level dedup to avoid re-extracting same text
4. is_rural + social_impact_score added to metadata for re-ranker
5. Runs until it hits target, not just 10 queries
"""

import os, json, time, hashlib, re, requests
from groq import Groq
from sentence_transformers import SentenceTransformer

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("pinecone not installed — run: pip install pinecone-client")

GROQ_KEY     = os.environ.get("GROQ_API_KEY", "")
PINECONE_KEY = os.environ.get("PINECONE_API_KEY", "")
SERP_KEY     = os.environ.get("SERP_API_KEY", "")
INDEX_NAME   = "aura-egypt-locations"

# ── Diverse, specific seed queries ─────────────────────────────────────────
# Grouped so each batch targets a different region/theme
EGYPT_QUERIES = [
    # Aswan specifics
    "Aswan felucca overnight Nile experience Egypt",
    "Aswan Nubian homestay local family Egypt",
    "Elephantine Island archaeology Aswan",
    "Aswan High Dam Lake Nasser viewpoint",
    "Philae Temple sound light show Aswan",

    # Luxor specifics
    "Valley of the Queens Luxor hidden tombs",
    "Luxor West Bank local village experience",
    "Karnak Temple hypostyle hall Egypt",
    "Luxor hot air balloon sunrise experience",
    "Deir el-Bahari Hatshepsut temple Egypt",

    # Siwa
    "Siwa Oasis Alexander Oracle Egypt",
    "Siwa salt lake fatnas island Egypt",
    "Shali fortress ruins Siwa Egypt",
    "Siwa Great Sand Sea safari Egypt",

    # Fayoum
    "Wadi El Hitan whale fossils Fayoum Egypt",
    "Wadi El Rayan waterfall Fayoum desert",
    "Fayoum pottery village local craft Egypt",
    "Lake Qarun Fayoum birdwatching Egypt",

    # Red Sea & Sinai
    "Dahab Blue Hole diving Egypt",
    "Colored Canyon Sinai hiking Egypt",
    "Saint Catherine monastery Sinai Egypt",
    "Ras Mohammed snorkeling coral Egypt",

    # Cairo surroundings
    "Saqqara step pyramid off the beaten path",
    "Memphis ancient capital Egypt ruins",
    "Dahshur Red Pyramid Egypt lesser known",
    "Wadi Natrun monastery Egypt desert",

    # Western Desert
    "White Desert chalk formations Egypt",
    "Black Desert volcanic landscape Egypt",
    "Bahariya Oasis golden mummies Egypt",
    "Farafra Oasis remote desert Egypt",

    # Nile Delta / Alexandria
    "Alexandria catacombs Kom el-Shoqafa Egypt",
    "Alexandria Bibliotheca modern architecture",
    "Rashid Rosetta Stone city Egypt history",

    # Community / social impact focused
    "Egyptian village sustainable tourism community",
    "Nubian culture handicraft women cooperative Egypt",
    "Bedouin camp authentic experience Egypt",
    "local Egyptian guesthouse budget authentic",
    "Egypt organic farm rural agrotourism",
]

VIBE_PROMPT = """You are a cinematic travel intelligence. Extract the soul of this Egyptian location.
Return ONLY valid JSON, no markdown, no explanation:
{
  "name": "Precise official location name",
  "description": "2-3 sentences of cinematic sensory description — sight, sound, feeling",
  "tags": ["tag1","tag2","tag3","tag4"],
  "mbti_alignment": ["TYPE1","TYPE2","TYPE3"],
  "persona_weights": {"Solo":0.0,"Couple":0.0,"Family":0.0,"Group":0.0},
  "genre_boost": {
    "Science Fiction":0.0,"Fantasy":0.0,"Mystery":0.0,"Adventure":0.0,
    "Romance":0.0,"Drama":0.0,"History":0.0,"Documentary":0.0,
    "Animation":0.0,"Horror":0.0,"Thriller":0.0,"Comedy":0.0,"Action":0.0
  },
  "price_per_night": 0,
  "city": "city name",
  "region": "Upper Egypt|Lower Egypt|Sinai|Western Desert|Red Sea|Nile Delta",
  "social_impact": "One sentence on how visiting helps local community",
  "is_rural": true,
  "social_impact_score": 0.0,
  "image_search_query": "3-5 word photo search query"
}
Rules:
- genre_boost: -0.25 (penalise) to +0.25 (reward). Most should be 0.0
- persona_weights: 0.1 to 1.0, values should reflect real fit
- is_rural: true if community-owned, village, homestay, remote, or off-mainstream
- social_impact_score: 0.0 to 1.0 (1.0 = 100% local benefit e.g. Nubian homestay)
- price_per_night: realistic USD estimate
- Be specific — vague or generic locations get rejected"""

RURAL_SIGNALS = [
    "village","homestay","nubian","bedouin","cooperative","craft","community",
    "local family","remote","oasis","off the beaten","hidden","artisan","farm"
]

class ScoutAgent:
    def __init__(self):
        self.groq  = Groq(api_key=GROQ_KEY)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._seen_snippets: set[str] = set()
        self._seen_names:    set[str] = set()

        if PINECONE_AVAILABLE and PINECONE_KEY:
            self.pc = Pinecone(api_key=PINECONE_KEY)
            self._ensure_index()
            self._load_existing_names()
        else:
            self.pc    = None
            self.index = None
            print("Pinecone not configured — running in dry-run mode")

    # ── Setup ──────────────────────────────────────────────────────────────

    def _ensure_index(self):
        existing = [i.name for i in self.pc.list_indexes()]
        if INDEX_NAME not in existing:
            self.pc.create_index(
                name=INDEX_NAME, dimension=384, metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"Created Pinecone index: {INDEX_NAME}")
        self.index = self.pc.Index(INDEX_NAME)

    def _load_existing_names(self):
        """Pre-load all existing location names to enable smarter dedup."""
        try:
            stats = self.index.describe_index_stats()
            total = stats.get("total_vector_count", 0)
            print(f"  Pinecone: {total} existing locations")
            # We can't list all names from Pinecone cheaply,
            # so we track within-session only for the run.
        except Exception as e:
            print(f"  Could not get index stats: {e}")

    # ── Main run ───────────────────────────────────────────────────────────

    def run(self, target: int = 50) -> dict:
        print(f"\nScout Agent starting. Target: {target} new locations.\n")
        log      = []
        upserted = 0
        skipped  = 0
        errors   = 0

        for query in EGYPT_QUERIES:
            if upserted >= target:
                break

            print(f"Searching: {query}")
            log.append({"type": "search", "query": query})

            snippets = self._search(query)
            if not snippets:
                print("  No results")
                continue

            for snippet in snippets:
                if upserted >= target:
                    break

                # Deduplicate at snippet level
                snip_hash = hashlib.md5(snippet[:120].encode()).hexdigest()
                if snip_hash in self._seen_snippets:
                    continue
                self._seen_snippets.add(snip_hash)

                loc = self._extract(snippet)
                if not loc:
                    errors += 1
                    continue

                norm_name = self._normalise(loc["name"])

                # Deduplicate at name level
                if norm_name in self._seen_names:
                    print(f"  Skip (name dup): {loc['name']}")
                    skipped += 1
                    continue

                # Check Pinecone for near-duplicate
                if self.index and self._pinecone_exists(loc["name"]):
                    print(f"  Skip (in DB): {loc['name']}")
                    self._seen_names.add(norm_name)
                    skipped += 1
                    continue

                self._seen_names.add(norm_name)
                self._upsert(loc)
                upserted += 1
                print(f"  [{upserted}/{target}] Added: {loc['name']} "
                      f"({'rural' if loc.get('is_rural') else 'mainstream'}) "
                      f"— {loc.get('city','?')}")
                log.append({
                    "type":     "upsert",
                    "name":     loc["name"],
                    "city":     loc.get("city"),
                    "is_rural": loc.get("is_rural", False),
                })
                time.sleep(0.4)

        rural_count = sum(1 for e in log if e.get("type")=="upsert" and e.get("is_rural"))
        summary = {
            "upserted":    upserted,
            "skipped":     skipped,
            "errors":      errors,
            "rural_added": rural_count,
            "log":         log,
        }
        print(f"\nScout done: {upserted} added ({rural_count} rural), "
              f"{skipped} skipped, {errors} errors")
        return summary

    # ── Web search ─────────────────────────────────────────────────────────

    def _search(self, query: str) -> list[str]:
        if not SERP_KEY:
            return []

        try:
            r = requests.get("https://serpapi.com/search", params={
                "q":       f"{query} travel guide",
                "api_key": SERP_KEY,
                "num":     5,
                "hl":      "en",
                "gl":      "eg",
            }, timeout=10).json()

            snippets = []
            for result in r.get("organic_results", []):
                title   = result.get("title", "")
                snippet = result.get("snippet", "")
                source  = result.get("source", "")
                if len(snippet) > 50:
                    snippets.append(f"{title}. {snippet}. Source: {source}")
            return snippets[:4]
        except Exception as e:
            print(f"  SerpAPI error: {e}")
            return []

    # ── Vibe extraction ────────────────────────────────────────────────────

    def _extract(self, raw: str) -> dict | None:
        try:
            resp = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": VIBE_PROMPT},
                    {"role": "user",   "content": f"Extract vibe from:\n{raw[:600]}"}
                ],
                temperature=0.35,
                max_tokens=700,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)

            # Validate
            if not data.get("name") or not data.get("description"):
                return None
            if len(data["description"]) < 40:
                return None

            # Auto-detect rural if LLM missed it
            text = (data["name"] + data["description"] + str(data.get("tags",""))).lower()
            if any(sig in text for sig in RURAL_SIGNALS):
                data["is_rural"] = True
                if not data.get("social_impact_score") or data["social_impact_score"] < 0.5:
                    data["social_impact_score"] = 0.7

            data["social_impact_score"] = float(data.get("social_impact_score", 0.3))
            data["is_rural"]            = bool(data.get("is_rural", False))
            return data

        except Exception as e:
            print(f"  Extraction error: {e}")
            return None

    # ── Pinecone operations ────────────────────────────────────────────────

    def _pinecone_exists(self, name: str) -> bool:
        try:
            result = self.index.fetch(ids=[self._make_id(name)])
            return bool(result.get("vectors"))
        except:
            return False

    def _upsert(self, loc: dict):
        if not self.index:
            return
        text = f"{loc['description']} {' '.join(loc.get('tags',[]))}"
        vec  = self.model.encode([text], normalize_embeddings=True)[0].tolist()

        self.index.upsert(vectors=[{
            "id":     self._make_id(loc["name"]),
            "values": vec,
            "metadata": {
                "name":                loc.get("name",""),
                "description":         loc.get("description",""),
                "tags":                loc.get("tags",[]),
                "mbti_alignment":      loc.get("mbti_alignment",[]),
                "persona_weights":     json.dumps(loc.get("persona_weights",{})),
                "genre_boost":         json.dumps(loc.get("genre_boost",{})),
                "price_per_night":     float(loc.get("price_per_night",60)),
                "city":                loc.get("city","Egypt"),
                "region":              loc.get("region",""),
                "social_impact":       loc.get("social_impact",""),
                "is_rural":            loc.get("is_rural",False),
                "social_impact_score": loc.get("social_impact_score",0.3),
                "image_search_query":  loc.get("image_search_query",""),
            }
        }])

    def query(self, text: str, top_k: int = 12) -> list[dict]:
        """Called by AuraMatcher — retrieves live locations from Pinecone."""
        if not self.index:
            return []
        vec     = self.model.encode([text], normalize_embeddings=True)[0].tolist()
        results = self.index.query(vector=vec, top_k=top_k, include_metadata=True)
        locs    = []
        for match in results.get("matches", []):
            m = match["metadata"]
            locs.append({
                "name":                m.get("name",""),
                "description":         m.get("description",""),
                "tags":                m.get("tags",[]),
                "mbti_alignment":      m.get("mbti_alignment",[]),
                "persona_weights":     json.loads(m.get("persona_weights","{}")),
                "genre_boost":         json.loads(m.get("genre_boost","{}")),
                "price_per_night":     float(m.get("price_per_night",60)),
                "city":                m.get("city","Egypt"),
                "social_impact":       m.get("social_impact",""),
                "is_rural":            bool(m.get("is_rural",False)),
                "social_impact_score": float(m.get("social_impact_score",0.3)),
                "pinecone_score":      round(match["score"]*100,1),
            })
        return locs

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(name: str) -> str:
        """Lowercase, strip common suffixes for better dedup."""
        n = name.lower().strip()
        for suffix in [" egypt"," temple"," complex"," ruins"," site"," area"]:
            n = n.replace(suffix,"")
        return re.sub(r'\s+', ' ', n).strip()

    @staticmethod
    def _make_id(name: str) -> str:
        return hashlib.md5(name.lower().strip().encode()).hexdigest()[:16]