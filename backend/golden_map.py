# backend/golden_map.py

MOVIE_TO_EXPERIENCE = {
    "dune": {
        "places": ["Elephantine Island Rocks", "Aswan High Dam"], 
        "vibe": "epic desert engineering and ancient spice routes",
        "score": 92.5,
        "location": "Elephantine Island Rocks"
    },
    "death on the nile": {
        "places": ["Old Cataract Terrace", "Nile Felucca"], 
        "vibe": "Victorian luxury mystery",
        "score": 98.2,
        "location": "Old Cataract Terrace"
    },
    "harry potter": {
        "places": ["Philae Temple at Dusk", "Old Cataract Terrace"], 
        "vibe": "mystical island magic",
        "score": 94.1,
        "location": "Philae Temple at Dusk"
    },
    "indiana jones": {
        "places": ["Tombs of the Nobles", "Philae Temple"], 
        "vibe": "archaeological adventure and hidden traps",
        "score": 89.7,
        "location": "Tombs of the Nobles"
    },
    "inception": {
        "places": ["Elephantine Island Rocks", "Aswan High Dam"], 
        "vibe": "brutalist rock formations and layered realities",
        "score": 87.3,
        "location": "Elephantine Island Rocks"
    },
    "interstellar": {
        "places": ["Elephantine Island Rocks", "High Dam"],
        "vibe": "cosmic isolation and monolithic structures",
        "score": 91.0,
        "location": "Elephantine Island Rocks"
    }
}

def smart_match(movie_title: str):
    movie = movie_title.lower().strip()
    return MOVIE_TO_EXPERIENCE.get(movie, None)