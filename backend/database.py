# backend/database.py
# SINGLE SOURCE OF TRUTH for all location data.
# KEY STANDARD: description, price_per_night, persona_weights, mbti_alignment, genre_boost

ASWAN_LOCATIONS = [
    {
        "name": "Elephantine Island Rocks",
        "description": "Primeval black granite boulders, alien cosmic landscape, absolute silence, rugged untouched wilderness, otherworldly geology.",
        "tags": ["rugged", "cosmic", "otherworldly", "solitude"],
        "price_per_night": 65,
        "persona_weights": {"Solo": 1.0, "Couple": 0.6, "Family": 0.4, "Group": 0.3},
        "mbti_alignment": ["INFP", "INTJ", "INTP", "ISTP"],
        "genre_boost": {
            "Science Fiction": 0.18, "Adventure": 0.12, "Documentary": 0.10,
            "Action": 0.08, "Romance": -0.15, "Comedy": -0.18, "Animation": -0.20
        },
        "social_impact": "Revenue funds Nubian archaeological preservation on the island.",
        "image_url": "https://images.unsplash.com/photo-1509152730246-6c7d448f3559?w=800",
        "activities": [
            {"name": "Sunrise granite boulder hike", "type": "activity", "cost_range": [15, 25]},
            {"name": "Pharaonic rock inscriptions tour", "type": "activity", "cost_range": [10, 20]},
            {"name": "Nile swimming at dawn", "type": "activity", "cost_range": [0, 5]},
        ]
    },
    {
        "name": "Philae Temple at Dusk",
        "description": "Mystical island sanctuary, sacred geometry, magic shadows, ancient goddess worship, divine water reflections at golden hour.",
        "tags": ["spiritual", "ancient", "ethereal", "sacred"],
        "price_per_night": 150,
        "persona_weights": {"Solo": 0.9, "Couple": 1.0, "Family": 0.7, "Group": 0.5},
        "mbti_alignment": ["INFJ", "INFP", "ENFP", "ISFJ"],
        "genre_boost": {
            "Fantasy": 0.18, "Mystery": 0.12, "Adventure": 0.10, "History": 0.12,
            "Horror": -0.05, "Comedy": -0.15, "Action": -0.08
        },
        "social_impact": "Ticket revenue supports UNESCO site maintenance, employing local guides.",
        "image_url": "https://images.unsplash.com/photo-1572262013778-0062400e936b?w=800",
        "activities": [
            {"name": "Philae sound & light show", "type": "activity", "cost_range": [20, 35]},
            {"name": "Guided hieroglyph reading tour", "type": "activity", "cost_range": [15, 25]},
            {"name": "Felucca crossing at sunset", "type": "transport", "cost_range": [5, 10]},
        ]
    },
    {
        "name": "Nubian Village Gharb Soheil",
        "description": "Vibrant kaleidoscopic colors, mud-brick domed houses, soulful community spirit, bustling spice markets, authentic living culture.",
        "tags": ["colorful", "authentic", "community", "family_friendly"],
        "price_per_night": 45,
        "persona_weights": {"Solo": 0.7, "Couple": 0.8, "Family": 1.0, "Group": 0.9},
        "mbti_alignment": ["ENFP", "ESFP", "ENFJ", "ESFJ"],
        "genre_boost": {
            "Animation": 0.18, "Musical": 0.18, "Comedy": 0.12, "Family": 0.15,
            "Horror": -0.30, "Thriller": -0.20, "Science Fiction": -0.10
        },
        "social_impact": "100% of bookings go directly to Nubian family-run homestays.",
        "image_url": "https://images.unsplash.com/photo-1539768942893-daf53e448371?w=800",
        "activities": [
            {"name": "Nubian cooking class with local family", "type": "food", "cost_range": [20, 35]},
            {"name": "Indigo textile & craft workshop", "type": "activity", "cost_range": [10, 20]},
            {"name": "Village boat tour with children's school visit", "type": "activity", "cost_range": [8, 15]},
        ]
    },
    {
        "name": "Old Cataract Terrace",
        "description": "Victorian colonial grandeur, high tea at sunset, Agatha Christie murder mystery atmosphere, refined Nile elegance.",
        "tags": ["luxury", "noir", "historical", "colonial"],
        "price_per_night": 450,
        "persona_weights": {"Solo": 0.8, "Couple": 1.0, "Family": 0.5, "Group": 0.4},
        "mbti_alignment": ["INTJ", "INFJ", "ISTJ", "ENTJ"],
        "genre_boost": {
            "Mystery": 0.15, "Drama": 0.10, "History": 0.15, "Thriller": 0.12,
            "Comedy": -0.20, "Animation": -0.18
        },
        "social_impact": "Employs 40+ Aswan residents in hospitality and heritage restoration.",
        "image_url": "https://images.unsplash.com/photo-1590073242678-70ee3fc28e8e?w=800",
        "activities": [
            {"name": "High tea on the Nile terrace", "type": "food", "cost_range": [30, 50]},
            {"name": "Agatha Christie suite private tour", "type": "activity", "cost_range": [20, 40]},
            {"name": "Private felucca at dusk", "type": "transport", "cost_range": [40, 70]},
        ]
    },
    {
        "name": "Felucca Golden Hour Cruise",
        "description": "Drifting on the Nile at sunset, golden light on ancient sails, timeless romance, peaceful river life, cinematic horizon.",
        "tags": ["romantic", "serene", "cinematic", "golden"],
        "price_per_night": 90,
        "persona_weights": {"Solo": 0.6, "Couple": 1.0, "Family": 0.7, "Group": 0.6},
        "mbti_alignment": ["INFP", "ENFP", "ISFP", "INFJ"],
        "genre_boost": {
            "Romance": 0.20, "Drama": 0.12, "Musical": 0.10, "Adventure": 0.08,
            "Horror": -0.25, "Action": -0.12
        },
        "social_impact": "Sustains 12 traditional felucca captain families.",
        "image_url": "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?w=800",
        "activities": [
            {"name": "Overnight Nile felucca voyage", "type": "activity", "cost_range": [40, 80]},
            {"name": "Nile fishing at dawn", "type": "activity", "cost_range": [10, 20]},
            {"name": "Stars & Nile night photography", "type": "activity", "cost_range": [5, 15]},
        ]
    },
    {
        "name": "Tombs of the Nobles",
        "description": "Rock-cut cliff tombs, faded frescoes of ancient daily life, scholarly solitude, forgotten histories carved in stone.",
        "tags": ["archaeological", "scholarly", "hidden", "contemplative"],
        "price_per_night": 50,
        "persona_weights": {"Solo": 1.0, "Couple": 0.7, "Family": 0.6, "Group": 0.5},
        "mbti_alignment": ["INTJ", "ISTJ", "INTP", "INFJ"],
        "genre_boost": {
            "History": 0.20, "Documentary": 0.18, "Mystery": 0.12, "Drama": 0.10,
            "Comedy": -0.20, "Animation": -0.18
        },
        "social_impact": "Guides trained from Aswan youth unemployment programs.",
        "image_url": "https://images.unsplash.com/photo-1544971587-b842c27f8e14?w=800",
        "activities": [
            {"name": "Expert Egyptologist private tour", "type": "activity", "cost_range": [25, 45]},
            {"name": "Sunrise cliff photography walk", "type": "activity", "cost_range": [5, 10]},
            {"name": "Ancient pigment fresco study workshop", "type": "activity", "cost_range": [15, 25]},
        ]
    },
    {
        "name": "Kitchener Island Garden",
        "description": "Lush tropical oasis on the Nile, rare African palms, exotic birdsong, serene colonial garden paths, hidden green escape.",
        "tags": ["lush", "serene", "botanical", "hidden"],
        "price_per_night": 40,
        "persona_weights": {"Solo": 0.9, "Couple": 0.9, "Family": 0.8, "Group": 0.6},
        "mbti_alignment": ["ISFP", "INFP", "ISFJ", "ENFP"],
        "genre_boost": {
            "Drama": 0.12, "Romance": 0.15, "Documentary": 0.10, "Animation": 0.08,
            "Action": -0.15, "Thriller": -0.12
        },
        "social_impact": "Botanical research station employs 8 local horticultural graduates.",
        "image_url": "https://images.unsplash.com/photo-1568322422394-3cb4978a35e2?w=800",
        "activities": [
            {"name": "Rare species botanical guided walk", "type": "activity", "cost_range": [10, 20]},
            {"name": "Watercolor painting in the garden", "type": "activity", "cost_range": [15, 25]},
            {"name": "Bird-watching at dawn", "type": "activity", "cost_range": [5, 10]},
        ]
    },
    {
        "name": "Aswan High Dam Overlook",
        "description": "Soviet brutalist mega-engineering, raw industrial power, vast Lake Nasser horizon, humanity conquering nature at epic scale.",
        "tags": ["brutalist", "monumental", "industrial", "vast"],
        "price_per_night": 35,
        "persona_weights": {"Solo": 0.8, "Couple": 0.5, "Family": 0.7, "Group": 0.8},
        "mbti_alignment": ["INTJ", "INTP", "ENTJ", "ESTJ"],
        "genre_boost": {
            "Documentary": 0.20, "Science Fiction": 0.12, "Action": 0.10, "History": 0.15,
            "Romance": -0.20, "Musical": -0.18
        },
        "social_impact": "Tourism fees fund local engineering scholarship programs.",
        "image_url": "https://images.unsplash.com/photo-1518391846015-55a9cb0bb4ad?w=800",
        "activities": [
            {"name": "Dam engineering documentary screening", "type": "activity", "cost_range": [5, 10]},
            {"name": "Lake Nasser boat tour", "type": "activity", "cost_range": [20, 40]},
            {"name": "Panoramic sunset walk", "type": "activity", "cost_range": [0, 5]},
        ]
    },
]

# Travelpayouts marker — replace with your own if needed
TP_MARKER = "718944"

# Travelpayouts affiliate link builder
def tp_link(service: str, origin: str = "CAI", destination: str = "ASW", date: str = "") -> str:
    base = f"?marker={TP_MARKER}"
    links = {
        "flight": f"https://www.aviasales.com/{base}&origin={origin}&destination={destination}&depart_date={date}&adults=1",
        "hotel":  f"https://www.hotellook.com/{base}&destination=Aswan&checkIn={date}&adults=1",
        "transfer": f"https://www.kiwitaxi.com/{base}",
        "activity": f"https://travelpayouts.com/activities/{base}",
    }
    return links.get(service, f"https://www.travelpayouts.com/{base}")