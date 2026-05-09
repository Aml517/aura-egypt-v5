# backend/trip_builder.py  v3.0
"""
Trip Builder — AuraEgypt v6.0

What changed from v2:
1. Classifies luxury vs boutique_nubian vs community BEFORE calling Groq
2. Elite concierge prompt — switches to Nubian boutique if budget can't
   support $500/night luxury after flights
3. Cost validation — no $0 on any non-free item
4. Real place names enforced — exact LoreDB names, no metaphors
5. build_real_budget() receives tier + location_name for accurate floors
6. Fallback itinerary uses 2026 real prices
"""

import json, os
from datetime import datetime, timedelta
from groq import Groq

from travelpayouts import (
    build_real_budget,
    inject_links_into_itinerary,
    classify_location_tier,
    get_hotel_floor_price,
    ACTIVITY_COSTS_2026,
    FOOD_COSTS_2026,
    FLIGHT_ESTIMATES_2026,
    HOTEL_TIERS_2026,
    activity_link,
    transfer_link,
)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")


# ── System prompt — grounded, real, no cinematic language ─────────────────

CONCIERGE_SYSTEM = """You are an elite Egyptian travel concierge — the best in Cairo.
You write real, bookable itineraries for discerning travellers visiting Aswan, Egypt.

Your rules — follow every single one:
- Use EXACT real place names: 'Philae Temple', 'Nubian Village Gharb Soheil',
  'Tombs of the Nobles (Qubbet el-Hawa)', 'Corniche el-Nil', 'Sharia el-Souk'
- Costs must be realistic 2026 USD (felucca: $10-15/hr, Philae entry: $18,
  Nubian meal: $8-12, local taxi: $5-10, luxury dinner: $40-60)
- NEVER write $0 for any hotel or flight — those always have real costs
- NEVER use cinematic language: no 'portal', 'Arrakis', 'otherworldly realm'
- Tone: warm, specific, practical — like a knowledgeable Egyptian friend
- If budget tier is 'luxury': recommend Sofitel Legend Old Cataract or Mövenpick
- If budget tier is 'boutique_nubian': recommend Anakato Nubian Houses or Kato Dool
- If budget tier is 'community': recommend Nubian homestays in Gharb Soheil
- Day themes must be practical: 'Arrival & Corniche Walk' not 'Gateway to the Eternal'

Return ONLY valid JSON. No markdown. No explanation. No extra text."""


def _build_concierge_prompt(
    location_name:         str,
    city:                  str,
    movie_title:           str,
    mbti:                  str,
    days:                  int,
    budget_data:           dict,
    is_rural:              bool,
    tier:                  str,
    description:           str,
    activities:            list,
    can_afford_luxury:     bool,
) -> str:
    """
    Builds the user-turn prompt for Groq.
    Key logic: if budget can't cover luxury hotel, switch recommendation.
    """
    flight_cost    = budget_data["flight"]["cost"]
    hotel_ppn      = budget_data["hotel"]["cost_per_night"]
    hotel_total    = budget_data["hotel"]["total"]
    daily_act      = budget_data["daily"]["activity"]
    daily_food     = budget_data["daily"]["food"]
    daily_transport= budget_data["daily"]["transport"]
    remaining      = budget_data["summary"]["remaining"]
    feasible       = budget_data["summary"]["is_feasible"]
    warning        = budget_data.get("budget_warning", "")

    # Accommodation guidance based on tier + affordability
    if tier == "luxury" and can_afford_luxury:
        accommodation_guidance = (
            f"Recommend Sofitel Legend Old Cataract Aswan (from $450/night) "
            f"or Mövenpick Resort Aswan ($250/night). "
            f"The traveller's budget supports this tier."
        )
    elif tier == "luxury" and not can_afford_luxury:
        accommodation_guidance = (
            f"The budget CANNOT support $500/night luxury after flights. "
            f"Recommend Anakato Nubian Houses ($180/night) or "
            f"Kato Dool Nubian Village ($140/night) instead — "
            f"these are the best high-end boutique alternatives in Aswan."
        )
    elif tier == "boutique_nubian":
        accommodation_guidance = (
            f"Recommend Anakato Nubian Houses ($180/night) or "
            f"Kato Dool Nubian Village ($140/night). "
            f"These are authentic, design-forward Nubian boutique stays."
        )
    elif is_rural or tier == "community":
        accommodation_guidance = (
            f"This is a community/rural destination. "
            f"Recommend local Nubian homestays in Gharb Soheil ($25-40/night). "
            f"Show 'Book directly with host family' — no Booking.com link."
        )
    else:
        accommodation_guidance = (
            f"Recommend mid-range hotels in {city} ($60-120/night). "
            f"Good options: Nefertiti Hotel, Orchida St George, Hapi Hotel."
        )

    budget_context = (
        f"BUDGET IS INSUFFICIENT — warn the traveller." if not feasible
        else f"Budget is feasible. ${remaining} will remain after all costs."
    )

    return f"""Create a {days}-day itinerary for {location_name}, Aswan, Egypt.

TRAVELLER PROFILE:
- MBTI: {mbti}
- Film they loved: "{movie_title}" (informs their taste — do NOT use film language in itinerary)
- Travel tier: {tier}

BUDGET BREAKDOWN (already calculated — use these exact numbers):
- Flight cost: ${flight_cost} (from budget, pre-paid)
- Hotel: ${hotel_ppn}/night × {days} nights = ${hotel_total}
- Daily activity budget: ${daily_act}
- Daily food budget: ${daily_food}  
- Daily transport budget: ${daily_transport}
- {budget_context}
{f'- WARNING: {warning}' if warning else ''}

ACCOMMODATION GUIDANCE:
{accommodation_guidance}

LOCATION: {location_name}
Description: {description[:250]}
Available activities: {json.dumps(activities[:6])}

Return this exact JSON:
{{
  "days": [
    {{
      "day_number": 1,
      "theme": "Practical title e.g. 'Arrival & Corniche Walk'",
      "items": [
        {{
          "type": "flight|hotel|activity|food|transport",
          "label": "Real specific name",
          "description": "One practical sentence — what it is and why this traveller will love it",
          "provider": "Real provider (e.g. 'Egypt Ministry of Antiquities', 'Local felucca captain')",
          "cost": 25,
          "booking_type": "travelpayouts|local|free|community_direct",
          "real_location": "Exact Aswan address or landmark name"
        }}
      ]
    }}
  ]
}}

STRICT RULES:
- Day 1: flight first (cost=${flight_cost}), hotel check-in second (cost=${hotel_ppn}), then 1-2 light activities
- Last day: 1 morning activity + airport transfer as final item
- Each middle day: 3-5 items
- Every cost must match 2026 Aswan reality (no $0 for hotels or flights)
- booking_type='free' ONLY for genuinely free items (Corniche walk, sunset viewing)
- booking_type='community_direct' for Nubian village / homestay items
- NEVER write 'portal', 'cinematic', 'vibe', 'otherworldly', or film character names"""


class TripBuilder:

    def __init__(self):
        self.client = Groq(api_key=GROQ_KEY)

    def build(self, location: dict, movie_title: str, mbti: str,
              budget: float, days: int, origin: str,
              travel_date: str) -> dict:

        loc_name    = location.get("name", "Aswan")
        city        = location.get("city", "Aswan")
        is_rural    = location.get("is_rural", False)
        description = location.get("description", "")
        activities  = location.get("activities", [])
        ppn         = float(location.get("price_per_night", 0))

        # ── 1. Classify tier ───────────────────────────────────────────────
        tier = classify_location_tier(loc_name, is_rural, ppn)

        # ── 2. Real budget with live prices ───────────────────────────────
        budget_data = build_real_budget(
            total_budget      = budget,
            days              = days,
            origin            = origin,
            destination_city  = city,
            travel_date       = travel_date,
            is_rural          = is_rural,
            location_name     = loc_name,
            tier              = tier,
            price_per_night   = ppn,
        )

        # ── 3. Can the budget actually support luxury? ────────────────────
        hotel_ppn      = budget_data["hotel"]["cost_per_night"]
        flight_cost    = budget_data["flight"]["cost"]
        hotel_total    = hotel_ppn * days
        can_afford_lux = (budget - flight_cost - hotel_total) >= (days * 40)

        # If luxury but can't afford it → downgrade to boutique_nubian
        effective_tier = tier
        if tier == "luxury" and not can_afford_lux:
            effective_tier = "boutique_nubian"
            # Recalculate budget with correct tier
            budget_data = build_real_budget(
                total_budget      = budget,
                days              = days,
                origin            = origin,
                destination_city  = city,
                travel_date       = travel_date,
                is_rural          = is_rural,
                location_name     = loc_name,
                tier              = effective_tier,
                price_per_night   = ppn,
            )

        # ── 4. Generate itinerary via Groq ────────────────────────────────
        prompt = _build_concierge_prompt(
            location_name      = loc_name,
            city               = city,
            movie_title        = movie_title,
            mbti               = mbti,
            days               = days,
            budget_data        = budget_data,
            is_rural           = is_rural,
            tier               = effective_tier,
            description        = description,
            activities         = activities,
            can_afford_luxury  = can_afford_lux,
        )

        itinerary_days = self._call_groq(prompt, loc_name, days, city,
                                          is_rural, effective_tier, budget_data)

        # ── 5. Validate costs + inject real deep links ────────────────────
        itinerary_days = inject_links_into_itinerary(
            itinerary        = itinerary_days,
            origin           = origin,
            travel_date      = travel_date,
            destination_city = city,
            is_rural         = is_rural,
            tier             = effective_tier,
        )

        # ── 6. Final cost totals ──────────────────────────────────────────
        all_items    = [i for day in itinerary_days for i in day.get("items", [])]
        total_spent  = sum(i.get("cost", 0) for i in all_items)
        total_remaining = round(budget - total_spent)

        return {
            "destination":      loc_name,
            "city":             city,
            "movie":            movie_title,
            "mbti":             mbti,
            "days":             days,
            "origin":           origin,
            "travel_date":      travel_date,
            "is_rural":         is_rural,
            "tier":             effective_tier,
            "budget_total":     round(budget),
            "budget_spent":     total_spent,
            "budget_remaining": total_remaining,
            "budget_breakdown": budget_data,
            "price_sources":    budget_data.get("price_sources", {}),
            "budget_warning":   budget_data.get("budget_warning"),
            "itinerary":        itinerary_days,
            "booking_links":    budget_data.get("links", {}),
            "social_note": (
                "100% of your accommodation revenue goes directly to the host family."
                if is_rural else
                "Your trip supports local guides, drivers, and artisans across Aswan."
            ),
        }

    def _call_groq(self, prompt: str, loc_name: str, days: int,
                   city: str, is_rural: bool, tier: str,
                   budget_data: dict) -> list:
        try:
            resp = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": CONCIERGE_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.35,    # low = factual, not hallucinated
                max_tokens=3000,
                response_format={"type": "json_object"},
            )
            raw  = resp.choices[0].message.content
            data = json.loads(raw)
            days_list = data.get("days", [])

            if not days_list:
                raise ValueError("Groq returned empty days list")

            # Validate each item has required fields
            for day in days_list:
                day.setdefault("theme", f"Day {day.get('day_number',1)}")
                for item in day.get("items", []):
                    item.setdefault("type",         "activity")
                    item.setdefault("cost",         0)
                    item.setdefault("provider",     "Local")
                    item.setdefault("booking_type", "local")
                    item.setdefault("description",  "")
                    item.setdefault("real_location","Aswan, Egypt")

            return days_list

        except Exception as e:
            print(f"[TripBuilder] Groq error: {e}")
            return self._fallback(loc_name, days, city, is_rural, tier, budget_data)

    def _fallback(self, loc_name: str, days: int, city: str,
                  is_rural: bool, tier: str, budget_data: dict) -> list:
        """
        Real Aswan itinerary with 2026 prices.
        Used when Groq fails — never shows $0.
        """
        flight_cost = budget_data["flight"]["cost"]
        hotel_ppn   = budget_data["hotel"]["cost_per_night"]
        daily_food  = budget_data["daily"]["food"]
        daily_act   = budget_data["daily"]["activity"]
        daily_trans = budget_data["daily"]["transport"]

        # Hotel label based on tier
        hotel_labels = {
            "luxury":         "Sofitel Legend Old Cataract Aswan",
            "boutique_nubian":"Anakato Nubian Houses",
            "midrange":       "Nefertiti Hotel Aswan",
            "community":      "Nubian homestay — Gharb Soheil",
            "budget":         "Budget guesthouse Aswan",
        }
        hotel_label   = hotel_labels.get(tier, "Hotel in Aswan")
        hotel_type    = "community_direct" if is_rural else "travelpayouts"

        all_days = [
            {
                "day_number": 1,
                "theme": "Arrival & Corniche Walk",
                "items": [
                    {
                        "type": "flight",
                        "label": "Flight to Aswan (ASW)",
                        "description": "Your gateway to Upper Egypt — book early for best price.",
                        "provider": "Aviasales via Travelpayouts",
                        "cost": flight_cost,
                        "booking_type": "travelpayouts",
                        "real_location": "Aswan International Airport",
                    },
                    {
                        "type": "hotel",
                        "label": f"Check-in: {hotel_label}",
                        "description": "Rest after travel before your first Nile sunset.",
                        "provider": "Hotellook via Travelpayouts" if not is_rural else "Direct — host family",
                        "cost": hotel_ppn,
                        "booking_type": hotel_type,
                        "real_location": city,
                    },
                    {
                        "type": "activity",
                        "label": "Corniche el-Nil evening walk",
                        "description": "Aswan's riverside promenade — best at sunset, completely free.",
                        "provider": "Self-guided",
                        "cost": 0,
                        "booking_type": "free",
                        "real_location": "Corniche el-Nil, Aswan",
                    },
                    {
                        "type": "food",
                        "label": "Dinner at El-Masry Restaurant",
                        "description": "Classic Egyptian koshary and ful — local prices, authentic atmosphere.",
                        "provider": "Local restaurant",
                        "cost": min(daily_food, 10),
                        "booking_type": "local",
                        "real_location": "Sharia el-Souk, Aswan",
                    },
                ],
            },
            {
                "day_number": 2,
                "theme": "Philae Temple & Nile",
                "items": [
                    {
                        "type": "activity",
                        "label": "Philae Temple (Temple of Isis)",
                        "description": "Ancient island temple reached by motorboat — arrive before 9am to beat crowds.",
                        "provider": "Egypt Ministry of Antiquities",
                        "cost": 18,
                        "booking_type": "local",
                        "real_location": "Agilkia Island, south of Aswan",
                    },
                    {
                        "type": "transport",
                        "label": "Motorboat to Philae + back",
                        "description": "Official motorboats run from the dock near the High Dam.",
                        "provider": "Official motorboat service",
                        "cost": 8,
                        "booking_type": "local",
                        "real_location": "Shellal Dock, Aswan",
                    },
                    {
                        "type": "activity",
                        "label": "Felucca ride — Elephantine Island",
                        "description": "Hire a local captain directly on the Nile bank — negotiate $10-15/hour.",
                        "provider": "Local felucca captain (negotiate directly)",
                        "cost": 12,
                        "booking_type": "community_direct",
                        "real_location": "Aswan Nile bank, near EgyptAir office",
                    },
                    {
                        "type": "food",
                        "label": "Nubian lunch at Siou Restaurant",
                        "description": "Home-cooked Nubian food on Elephantine Island — fried fish, molokhia, fresh bread.",
                        "provider": "Siou Restaurant, Elephantine Island",
                        "cost": min(daily_food, 12),
                        "booking_type": "local",
                        "real_location": "Elephantine Island, Aswan",
                    },
                ],
            },
            {
                "day_number": 3,
                "theme": "Nubian Village & Aswan Souk",
                "items": [
                    {
                        "type": "activity",
                        "label": "Nubian Village Gharb Soheil",
                        "description": "Take a boat across the Nile — painted houses, spice stalls, and Nubian families. Walk freely, buy direct from artisans.",
                        "provider": "Local boat captain (5-10 min crossing)",
                        "cost": 15,
                        "booking_type": "community_direct",
                        "real_location": "Gharb Soheil, West Bank, Aswan",
                    },
                    {
                        "type": "activity",
                        "label": "Aswan Souk (Sharia el-Souk)",
                        "description": "Egypt's most authentic spice and craft market. Walk south past the tourist section for real local prices.",
                        "provider": "Self-guided",
                        "cost": 0,
                        "booking_type": "free",
                        "real_location": "Sharia el-Souk, central Aswan",
                    },
                    {
                        "type": "food",
                        "label": "Street breakfast: ta'meya, ful, fresh juice",
                        "description": "Eat where the locals eat — vendors near the souk open from 7am.",
                        "provider": "Street vendors, Sharia el-Souk area",
                        "cost": 4,
                        "booking_type": "local",
                        "real_location": "Sharia el-Souk, Aswan",
                    },
                    {
                        "type": "activity",
                        "label": "Nubian Museum",
                        "description": "5,000 years of Nubian civilization — rescued artifacts, gold jewelry, and the story of the Aswan Dam flooding. Essential context.",
                        "provider": "Egypt Ministry of Antiquities",
                        "cost": 6,
                        "booking_type": "local",
                        "real_location": "Abtal el-Tahrir Street, Aswan",
                    },
                ],
            },
            {
                "day_number": 4,
                "theme": "Tombs of the Nobles & Departure",
                "items": [
                    {
                        "type": "activity",
                        "label": "Tombs of the Nobles (Qubbet el-Hawa)",
                        "description": "Rock-cut cliff tombs with vivid ancient frescoes — visit at dawn before any tour groups arrive.",
                        "provider": "Egypt Ministry of Antiquities",
                        "cost": 10,
                        "booking_type": "local",
                        "real_location": "West Bank cliffs, across from Aswan city",
                    },
                    {
                        "type": "food",
                        "label": "Final Nile-view breakfast",
                        "description": "Rooftop café on the Corniche — coffee, eggs, and fresh bread before your flight.",
                        "provider": "Local café, Corniche el-Nil",
                        "cost": 7,
                        "booking_type": "local",
                        "real_location": "Corniche el-Nil, Aswan",
                    },
                    {
                        "type": "transport",
                        "label": "Taxi to Aswan Airport",
                        "description": "Agree the price the night before — roughly 120-150 EGP (~$4-5). Ask your hotel to arrange.",
                        "provider": "Local taxi (hotel-arranged)",
                        "cost": 5,
                        "booking_type": "local",
                        "real_location": "Aswan city → Aswan International Airport",
                    },
                ],
            },
        ]

        # Add more days if needed using rotation
        if days > 4:
            extras = [
                {
                    "day_number": 5,
                    "theme": "Abu Simbel Day Trip",
                    "items": [
                        {
                            "type": "activity",
                            "label": "Abu Simbel Temples day trip",
                            "description": "Ramesses II's monumental temples 280km south. Join a convoy from Aswan at 4am or fly (25 min). Non-negotiable if you're this far south.",
                            "provider": "Egypt Ministry of Antiquities / local tour operator",
                            "cost": 55,
                            "booking_type": "local",
                            "real_location": "Abu Simbel, Aswan Governorate",
                        },
                        {
                            "type": "transport",
                            "label": "Aswan → Abu Simbel convoy transport",
                            "description": "Tourist convoy departs Aswan at 4am, returns by 2pm. Book through hotel or local agency.",
                            "provider": "Local tour agency",
                            "cost": min(daily_trans + 15, 30),
                            "booking_type": "local",
                            "real_location": "Aswan convoy departure point",
                        },
                    ],
                }
            ]
            all_days += extras

        return all_days[:days]


# ── Singleton + public interface ───────────────────────────────────────────

_builder = TripBuilder()


def build_trip(location: dict, movie_title: str, mbti: str,
               budget: float, days: int, origin: str,
               travel_date: str, groq_api_key: str = "") -> dict:
    """Public function called by main.py — stable interface."""
    return _builder.build(
        location    = location,
        movie_title = movie_title,
        mbti        = mbti,
        budget      = budget,
        days        = days,
        origin      = origin,
        travel_date = travel_date,
    )