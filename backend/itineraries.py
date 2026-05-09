# backend/itineraries.py

ASWAN_ITINERARIES = {
    "Aswan High Dam": {
        "title": "The Industrial Giant Journey",
        "daily_plan": [
            "Dawn private tour of the High Dam (Brutalist focus)",
            "Boat ride to Kalabsha Temple",
            "Sunset at the Lotus Tower",
            "Dinner overlooking Lake Nasser",
            "Desert trekking to the Soviet-Egyptian Friendship Monument",
            "Stargazing in the dark-sky desert zone",
            "Morning flight back across the desert"
        ],
        "total_cost": 450,
        "booking_url": "https://viator.com/aswan-dam?aid=auraegypt"
    },
    "Old Cataract Terrace": {
        "title": "The Agatha Christie Mystery",
        "daily_plan": [
            "Check-in at the Palace Wing (Old Cataract)",
            "High Tea on the terrace where Christie wrote her masterpiece",
            "Private Felucca sail around Lord Kitchener's island",
            "Gourmet dinner at 1902 Restaurant",
            "Walking tour of the Aswan Spice Market",
            "Midnight spa treatment with Nile views",
            "Breakfast on the historic veranda"
        ],
        "total_cost": 1200,
        "booking_url": "https://booking.com/cataract?aid=auraegypt"
    },
    "Philae Temple at Dusk": {
        "title": "The Pearl of Egypt Mysticism",
        "daily_plan": [
            "Taxi boat to Philae Island at sunrise",
            "Meditation session in the Temple of Isis",
            "Visit to the Kiosk of Trajan",
            "Sound and Light show after dark",
            "Nubian dinner in Gharb Soheil",
            "Photography workshop for ancient shadows",
            "Departure via traditional rowing boat"
        ],
        "total_cost": 350,
        "booking_url": "https://viator.com/philae?aid=auraegypt"
    }
}

def get_itinerary(place: str):
    # Fallback to High Dam if the exact key isn't found
    return ASWAN_ITINERARIES.get(place, ASWAN_ITINERARIES["Philae Temple at Dusk"])