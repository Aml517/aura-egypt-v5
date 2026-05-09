# backend/emotion_engine.py
"""
Emotional Fingerprint Engine — the core of what makes AuraEgypt
different from text search.

Instead of matching plot summaries to location descriptions,
we extract what a film makes you FEEL and match that to what
a place makes you FEEL.

Dune → not "desert planet hero journey"
     → "loneliness · ancient power · awe · the seeker who needs silence"
"""

import ssl
import json, os, hashlib, sqlite3, time
from groq import Groq
import urllib3
# ── EGYPT ISP CONNECTIVITY BYPASS (CRUCIAL) ─────────────────────────────── # This prevents the "Connection Error" by bypassing the ISP's SSL filtering 
try: 
    ssl._create_default_https_context = ssl._create_unverified_context   
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:   
  pass

GROQ_KEY  = os.environ.get("GROQ_API_KEY", "")
CACHE_DB  = os.path.join(os.path.dirname(__file__), "aura_cache.db")
CACHE_TTL = 60 * 60 * 24 * 30  # 30 days — emotions don't change

EMOTION_PROMPT = """You are a film psychologist and travel therapist combined.

Your job is NOT to describe the plot of the film.
Your job is to extract the EMOTIONAL EXPERIENCE of watching it —
what the viewer feels, needs, and secretly seeks.

Think: if someone watches this film alone at midnight, what are they
processing? What kind of place would complete that emotional journey?

Return ONLY valid JSON, no markdown, no explanation:
{
  "core_emotions": ["emotion1", "emotion2", "emotion3"],
  "psychological_need": "One precise sentence: what deep human need does this film meet?",
  "atmosphere_words": ["word1", "word2", "word3", "word4", "word5"],
  "sensory_profile": {
    "light":   "one of: harsh|golden|dim|neon|grey|dappled|blazing|soft",
    "sound":   "one of: silent|vast|chaotic|intimate|thunderous|whispering|rhythmic",
    "texture": "one of: rough|smooth|ancient|sterile|organic|mechanical|granular",
    "pace":    "one of: slow|urgent|contemplative|frantic|rhythmic|meditative"
  },
  "traveller_archetype": "The [type] who needs [specific thing]",
  "what_they_escape": "What the viewer is running FROM in real life",
  "place_must_have": ["physical or atmospheric quality the destination MUST have"],
  "place_must_not_have": ["what would ruin the experience for this person"],
  "mbti_emotional_match": ["TYPE1", "TYPE2"],
  "intensity": 0.8
}

Rules:
- core_emotions: real human emotions, not plot descriptions
- atmosphere_words: sensory adjectives, not nouns
- intensity: 0.0 (gentle/comforting) to 1.0 (overwhelming/transformative)
- place_must_have: be specific — "absolute silence" not just "quiet"
- Be honest — a rom-com and an arthouse film need very different places"""


class EmotionEngine:
    """
    Extracts emotional fingerprints from films via Groq LLM.
    Results are cached in SQLite — same film never costs twice.
    """

    def __init__(self):
        self.client = Groq(api_key=GROQ_KEY)
        self._init_cache()

    # ── Cache setup ────────────────────────────────────────────────────────

    def _init_cache(self):
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emotion_cache (
                    id          TEXT PRIMARY KEY,
                    movie_title TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at  REAL NOT NULL
                )
            """)
            conn.commit()

    def _cache_get(self, title: str) -> dict | None:
        key = hashlib.md5(title.lower().strip().encode()).hexdigest()
        with sqlite3.connect(CACHE_DB) as conn:
            row = conn.execute(
                "SELECT result_json FROM emotion_cache WHERE id=? AND created_at>?",
                (key, time.time() - CACHE_TTL)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def _cache_set(self, title: str, data: dict):
        key = hashlib.md5(title.lower().strip().encode()).hexdigest()
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO emotion_cache (id, movie_title, result_json, created_at) VALUES (?,?,?,?)",
                (key, title, json.dumps(data), time.time())
            )
            conn.commit()

    # ── Main extraction ────────────────────────────────────────────────────

    def extract(self, movie_title: str, movie_overview: str) -> dict:
        """
        Returns emotional fingerprint dict.
        Cached per title — never calls Groq twice for the same film.
        """
        cached = self._cache_get(movie_title)
        if cached:
            cached["_cached"] = True
            return cached

        try:
            resp = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": EMOTION_PROMPT},
                    {"role": "user",   "content":
                        f"Film: {movie_title}\n"
                        f"Overview: {movie_overview[:500]}\n\n"
                        f"Extract the complete emotional fingerprint."}
                ],
                temperature=0.45,
                max_tokens=700,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)

            # Validate + fill defaults
            data.setdefault("core_emotions",    ["wonder", "discovery", "seeking"])
            data.setdefault("atmosphere_words", ["cinematic", "vast", "ancient"])
            data.setdefault("place_must_have",  ["authenticity", "depth"])
            data.setdefault("place_must_not_have", ["tourist crowds"])
            data.setdefault("psychological_need", "To feel something real and lasting.")
            data.setdefault("traveller_archetype", "The seeker who needs depth")
            data.setdefault("what_they_escape", "Routine and superficiality")
            data.setdefault("mbti_emotional_match", [])
            data.setdefault("intensity", 0.6)
            data.setdefault("sensory_profile", {
                "light":"golden","sound":"vast","texture":"ancient","pace":"contemplative"
            })
            data["_cached"] = False
            data["movie"]   = movie_title

            self._cache_set(movie_title, data)
            return data

        except Exception as e:
            print(f"EmotionEngine error: {e}")
            return self._fallback(movie_title)

    def to_rich_query(self, emotion_data: dict) -> str:
        """
        Converts emotional fingerprint to a rich semantic query string.
        This REPLACES the raw movie plot overview in the matcher.

        The query combines:
        - Atmosphere words (most important for vibe matching)
        - Core emotions
        - Physical requirements
        - Sensory profile values
        - Psychological need

        Result: "loneliness ancient power awe cosmic isolation
                 vast brutal silent contemplative rough golden
                 silence wilderness the seeker needs cosmic truth"
        """
        parts = []

        # Atmosphere words carry the most semantic weight
        parts.extend(emotion_data.get("atmosphere_words", []))
        parts.extend(emotion_data.get("atmosphere_words", []))  # doubled for weight

        # Core emotions
        parts.extend(emotion_data.get("core_emotions", []))

        # Physical requirements
        parts.extend(emotion_data.get("place_must_have", []))

        # Sensory profile
        sp = emotion_data.get("sensory_profile", {})
        parts.extend([v for v in sp.values() if v])

        # Psychological need (truncated)
        need = emotion_data.get("psychological_need", "")
        if need:
            parts.append(need[:80])

        # Traveller archetype
        arch = emotion_data.get("traveller_archetype", "")
        if arch:
            parts.append(arch)

        return " ".join(p for p in parts if p)

    def genre_boost_from_emotions(self, emotion_data: dict) -> dict:
        """
        Derives genre boost adjustments from emotional profile.
        Used to augment the static genre_boost in database.
        """
        intensity = float(emotion_data.get("intensity", 0.6))
        emotions  = [e.lower() for e in emotion_data.get("core_emotions", [])]
        must_not  = [m.lower() for m in emotion_data.get("place_must_not_have", [])]

        boosts = {}

        # High intensity films need places that can handle it
        if intensity > 0.75:
            boosts["Adventure"]      = 0.05
            boosts["Science Fiction"] = 0.05
            boosts["Comedy"]         = -0.10  # comedy seekers don't want intensity

        # Emotion-specific boosts
        if any(e in emotions for e in ["loneliness","solitude","isolation"]):
            boosts["Documentary"] = 0.05
            boosts["Animation"]   = -0.10
            boosts["Musical"]     = -0.08

        if any(e in emotions for e in ["romance","longing","yearning"]):
            boosts["Romance"] = 0.08
            boosts["Drama"]   = 0.05

        if any(e in emotions for e in ["fear","dread","unease"]):
            boosts["Thriller"] = 0.05
            boosts["Horror"]   = 0.03

        if any(e in emotions for e in ["wonder","awe","transcendence"]):
            boosts["Fantasy"]        = 0.08
            boosts["Science Fiction"] = 0.06

        # Anti-needs
        if "crowds" in " ".join(must_not) or "tourist" in " ".join(must_not):
            # Don't boost highly commercial locations
            boosts["_anti_commercial"] = True

        return boosts

    def _fallback(self, title: str) -> dict:
        return {
            "core_emotions":       ["wonder", "discovery", "seeking"],
            "psychological_need":  "To feel something real and lasting.",
            "atmosphere_words":    ["cinematic", "vast", "ancient", "quiet", "golden"],
            "sensory_profile":     {"light":"golden","sound":"vast","texture":"ancient","pace":"contemplative"},
            "traveller_archetype": "The curious soul who needs depth over comfort",
            "what_they_escape":    "Routine and predictability",
            "place_must_have":     ["authenticity", "history", "silence"],
            "place_must_not_have": ["tourist crowds", "staged experiences"],
            "mbti_emotional_match":[],
            "intensity":           0.6,
            "_cached":             False,
            "_fallback":           True,
            "movie":               title,
        }


# Singleton
emotion_engine = EmotionEngine()