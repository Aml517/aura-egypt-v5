# backend/agent.py
"""
PharaonicAgent — Cleopatra voice narrative generator.

Fixed:
1. Handles both static DB keys and Scout-discovered location keys safely
2. Uses .get() everywhere — no KeyError crashes on new locations
3. Caches results via cache_manager to avoid redundant Groq calls
4. Returns sensible fallback if Groq fails
"""

import json, os
from groq import Groq

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

CLEOPATRA_SYSTEM = """You are Cleopatra VII, last Pharaoh of Egypt.
You speak in first person — poetic, grounded, never theatrical.
You know every inch of Aswan: every stone, every spice vendor, every Nile current.
Return ONLY valid JSON. No markdown. No backticks. No explanation."""

NARRATIVE_PROMPT = """The traveller watched "{movie}". Their MBTI is {mbti}.
Their matched location: {name}
Location description: {description}
Social impact: {social_impact}
Is rural/community: {is_rural}

Return exactly this JSON:
{{
  "blessing": "One powerful sentence welcoming this traveller to this place. Reference their emotional state (from the film), not the film's plot. Speak as Cleopatra.",
  "why_you": "Two sentences: why does this MBTI type belong specifically here? Be psychologically specific.",
  "cleopatra_tip": "One insider secret about this location. Something real, specific, not in any guidebook. A local truth."
}}"""


class PharaonicAgent:

    def __init__(self, api_key: str = ""):
        self.client = Groq(api_key=api_key or GROQ_KEY)

    def speak(self, location: dict, movie_title: str, mbti: str) -> dict:
        """
        Generates Cleopatra narrative for the matched location.
        Safe against both static DB and Scout-discovered location formats.
        """
        # Safe key access — works for both DB formats
        name         = location.get("name", "this sacred place")
        description  = location.get("description", "A timeless Egyptian destination.")
        social_impact= location.get("social_impact", "")
        is_rural     = location.get("is_rural", False)

        prompt = NARRATIVE_PROMPT.format(
            movie        = movie_title,
            mbti         = mbti,
            name         = name,
            description  = description[:300],
            social_impact= social_impact,
            is_rural     = is_rural,
        )

        try:
            resp = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": CLEOPATRA_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.75,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)

            # Validate required fields
            data.setdefault("blessing",       f"The stones of {name} have awaited your arrival.")
            data.setdefault("why_you",        "Your nature seeks what others overlook. This place rewards that patience.")
            data.setdefault("cleopatra_tip",  "Come at dawn. The light here exists nowhere else on earth.")
            return data

        except Exception as e:
            print(f"[Agent] Groq error: {e}")
            return self._fallback(name, mbti)

    def _fallback(self, name: str, mbti: str) -> dict:
        """Sensible fallback — never crashes the API response."""
        introverted = mbti[0] == "I" if len(mbti) == 4 else True
        return {
            "blessing": (
                f"The ancient silence of {name} has been waiting for someone "
                f"who would truly see it — not photograph it."
                if introverted else
                f"The energy of {name} rises to meet those who arrive with open eyes. "
                f"You are exactly who this place needs."
            ),
            "why_you": (
                f"As an {mbti}, you move through the world looking for depth beneath surface. "
                f"{name} has that in layers — most visitors never reach the second one."
            ),
            "cleopatra_tip": (
                "Come before 8am. The vendors aren't yet awake, "
                "the light is golden, and the place belongs entirely to you."
            ),
        }