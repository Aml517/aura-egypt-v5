MBTI_ARCHETYPES = {
    "INTJ": {"style": "Strategic", "pace": "Efficient", "comfort": "Luxury", "activities": ["Private tours", "Historical deep dives"]},
    "ENFP": {"style": "Spontaneous", "pace": "Flexible", "comfort": "Boutique", "activities": ["Hidden gems", "Local experiences"]},
    "ESTP": {"style": "Adventurous", "pace": "Fast", "comfort": "Adventure camps", "activities": ["4x4 safaris", "Hot air balloon"]},
    # All 16...
}

def generate_mbti_itinerary(mbti: str, vibe_location: str, budget: float):
    archetype = MBTI_ARCHETYPES.get(mbti, MBTI_ARCHETYPES["INFP"])
    
    itinerary = {
        "days": 7,
        "style": archetype["style"],
        "hotels": f"{archetype['comfort']} near {vibe_location}",
        "total_price": budget * 0.95,  # 5% AuraEgypt fee
        "activities": [f"{act} in {vibe_location}" for act in archetype["activities"]],
        "flights": "CAI direct, movie-timed",
        "booking_links": {
            "flights": "skyscanner.com/affiliate",
            "hotel": "booking.com/affiliate",
            "tours": "viator.com/affiliate?auraegypt"
        }
    }
    return itinerary