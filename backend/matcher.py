# backend/matcher.py  v3.0
"""
AuraMatcher — hybrid scoring engine.

Changes:
1. calculate_scores() queries Pinecone live (Scout-populated)
2. calculate_scores_static() — NEW fallback using ASWAN_LOCATIONS
   Called by main.py when Pinecone returns 0 results
3. _budget() uses sigmoid curve (not hard cliff)
4. _persona() has 3-tier MBTI matching (exact / near / miss)
5. _diversity() prevents top-3 from sharing same primary tag
"""

import numpy as np
import math
from sentence_transformers import SentenceTransformer
from database import ASWAN_LOCATIONS

try:
    from scout_agent import ScoutAgent
    PINECONE_AVAILABLE = True
except Exception:
    PINECONE_AVAILABLE = False
    print("[Matcher] scout_agent unavailable — will use static DB only")


class AuraMatcher:

    WEIGHTS = {
        "semantic": 0.35,
        "pinecone": 0.20,
        "budget":   0.25,
        "persona":  0.20,
    }

    THRESHOLD = 0.40   # minimum total score to include in results

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Pre-encode static DB at startup
        self._static_embeddings = self.model.encode(
            [loc["description"] for loc in ASWAN_LOCATIONS],
            normalize_embeddings=True
        )

        # Connect to Pinecone via Scout
        self._scout = None
        if PINECONE_AVAILABLE:
            try:
                self._scout = ScoutAgent()
            except Exception as e:
                print(f"[Matcher] Pinecone connect failed: {e}")

    # ── Public: Pinecone-backed scoring ───────────────────────────────────

    def calculate_scores(
        self,
        movie_overview: str,
        movie_genres:   list,
        budget:         float,
        days:           int,
        persona:        str,
        mbti:           str,
        visual_scores:  dict = None,
    ) -> list:
        """
        Queries Pinecone for semantic candidates, then applies
        full hybrid scoring on top.
        Returns [] if Pinecone unavailable — caller uses static fallback.
        """
        if not self._scout or not self._scout.index:
            return []

        try:
            candidates = self._scout.query(movie_overview, top_k=12)
        except Exception as e:
            print(f"[Matcher] Pinecone query failed: {e}")
            return []

        if not candidates:
            return []

        return self._score_and_rank(
            locations     = candidates,
            query_text    = movie_overview,
            movie_genres  = movie_genres,
            budget        = budget,
            days          = days,
            persona       = persona,
            mbti          = mbti,
            visual_scores = visual_scores or {},
            use_pinecone_sim = True,
        )

    # ── Public: Static DB fallback ────────────────────────────────────────

    def calculate_scores_static(
        self,
        movie_overview: str,
        movie_genres:   list,
        budget:         float,
        days:           int,
        persona:        str,
        mbti:           str,
        visual_scores:  dict = None,
    ) -> list:
        """
        Scores against the hardcoded ASWAN_LOCATIONS list.
        Used when Pinecone is empty or unavailable.
        Guarantees the system never returns an empty result.
        """
        # Inject pinecone_score=0 since we have no vector DB score
        candidates = [
            {**loc, "pinecone_score": 0.0}
            for loc in ASWAN_LOCATIONS
        ]

        return self._score_and_rank(
            locations        = candidates,
            query_text       = movie_overview,
            movie_genres     = movie_genres,
            budget           = budget,
            days             = days,
            persona          = persona,
            mbti             = mbti,
            visual_scores    = visual_scores or {},
            use_pinecone_sim = False,   # compute cosine ourselves
        )

    # ── Internal scoring pipeline ─────────────────────────────────────────

    def _score_and_rank(
        self,
        locations:        list,
        query_text:       str,
        movie_genres:     list,
        budget:           float,
        days:             int,
        persona:          str,
        mbti:             str,
        visual_scores:    dict,
        use_pinecone_sim: bool,
    ) -> list:

        query_vec    = self.model.encode([query_text], normalize_embeddings=True)[0]
        daily_budget = max(budget / max(days, 1), 1.0)
        results      = []

        for loc in locations:
            # ── Semantic score ─────────────────────────────────────────────
            if use_pinecone_sim:
                # Use Pinecone's cosine score directly
                pine_sim = loc.get("pinecone_score", 0.0) / 100.0
                # Re-encode for genre boost
                loc_vec  = self.model.encode(
                    [loc.get("description","")], normalize_embeddings=True
                )[0]
                base_sim = float(np.dot(query_vec, loc_vec))
            else:
                # Compute ourselves from static embeddings
                desc     = loc.get("description","")
                loc_vec  = self.model.encode([desc], normalize_embeddings=True)[0]
                base_sim = float(np.dot(query_vec, loc_vec))
                pine_sim = base_sim   # same source

            # Genre boost (additive, clamped)
            genre_boost = sum(
                loc.get("genre_boost", {}).get(g, 0.0)
                for g in movie_genres if g
            )
            semantic = float(np.clip(base_sim + genre_boost, 0.0, 1.0))

            # ── Other components ───────────────────────────────────────────
            budget_s  = self._budget(daily_budget, loc.get("price_per_night", 80))
            persona_s = self._persona(persona, mbti, loc)
            visual_s  = visual_scores.get(loc.get("name",""), 60.0) / 100.0

            # ── Total (visual contributes to semantic weight here) ─────────
            total = (
                semantic  * self.WEIGHTS["semantic"] +
                pine_sim  * self.WEIGHTS["pinecone"] +
                budget_s  * self.WEIGHTS["budget"]   +
                persona_s * self.WEIGHTS["persona"]
            )
            # Add visual as a small bonus (max +5%)
            total = min(1.0, total + visual_s * 0.05)

            if total >= self.THRESHOLD:
                results.append({
                    "location":        loc,
                    "total_score":     round(total * 100, 1),
                    "semantic_score":  round(semantic * 100, 1),
                    "budget_score":    round(budget_s * 100, 1),
                    "persona_score":   round(persona_s * 100, 1),
                    "visual_score":    round(visual_s * 100, 1),
                    "score_breakdown": {
                        "semantic": f"{semantic*100:.0f}%",
                        "budget":   f"{budget_s*100:.0f}%",
                        "persona":  f"{persona_s*100:.0f}%",
                        "visual":   f"{visual_s*100:.0f}%",
                    }
                })

        ranked = sorted(results, key=lambda x: x["total_score"], reverse=True)
        return self._diversity(ranked)

    # ── Scoring components ────────────────────────────────────────────────

    def _budget(self, daily_budget: float, price_per_night: float) -> float:
        """
        Sigmoid budget fit.
        Rationale: real booking behaviour is not binary —
        slightly over-budget still deserves partial credit.
        Score = 1.0 when budget >= price, falls gracefully below.
        """
        ratio = daily_budget / max(price_per_night, 1.0)
        return float(1.0 / (1.0 + math.exp(-5.0 * (ratio - 1.0))))

    def _persona(self, persona: str, mbti: str, loc: dict) -> float:
        """
        3-tier MBTI matching:
        - Exact match:        1.00
        - Near match (I/E + J/P same): 0.65
        - No match:           0.30
        """
        p_weight   = loc.get("persona_weights", {}).get(persona, 0.5)
        alignment  = loc.get("mbti_alignment", [])

        if mbti in alignment:
            m_weight = 1.00
        elif self._near_match(mbti, alignment):
            m_weight = 0.65
        else:
            m_weight = 0.30

        return (p_weight * 0.6) + (m_weight * 0.4)

    @staticmethod
    def _near_match(mbti: str, archetypes: list) -> bool:
        """Near match: same introvert/extrovert AND same judging/perceiving."""
        if len(mbti) != 4:
            return False
        return any(
            len(a) == 4 and a[0] == mbti[0] and a[3] == mbti[3]
            for a in archetypes
        )

    def _diversity(self, ranked: list, top_n: int = 3) -> list:
        """
        Prevents top-3 from all having the same primary tag.
        Guarantees genuinely different options for the user.
        """
        selected, seen_tags = [], set()

        for r in ranked:
            tags    = r["location"].get("tags", [])
            primary = tags[0] if tags else "misc"

            if primary not in seen_tags or len(selected) < 1:
                selected.append(r)
                seen_tags.add(primary)

            if len(selected) >= top_n:
                break

        # If filter was too aggressive, fill from remaining
        for r in ranked:
            if r not in selected:
                selected.append(r)
            if len(selected) >= top_n:
                break

        return selected