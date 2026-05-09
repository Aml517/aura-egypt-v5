import requests
import time
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# KEYS
TMDB_KEY = "19835a8eba0867342c3e0014a1d1e310"
PINECONE_KEY = "pcsk_A2Tv5_JXNevtp5qTy5JaHi24ekKgt9FDsuvQz49HTXfnDMom8fx4ZNQuMGfNcEWqHSxD2"

model = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key=PINECONE_KEY)
index = pc.Index("auraegypt-locations")

# THE ASWAN GOLD DATASET
ASWAN_DATA = [
    {"name": "Old Cataract Terrace", "movies": "Death on the Nile, The Crown", "desc": "Victorian colonial elegance, mystery, Agatha Christie vibes."},
    {"name": "Philae Temple at Dusk", "movies": "Harry Potter, Stargate", "desc": "Mystical island temple, sacred geometry, magic shadows."},
    {"name": "Elephantine Island Rocks", "movies": "Dune, Interstellar", "desc": "Alien granite boulders, primeval river, cosmic silence."},
    {"name": "Felucca at Golden Hour", "movies": "The English Patient", "desc": "Romantic orange sky, white sails, vintage peace."},
    {"name": "Nubian House", "movies": "Amélie, Grand Budapest Hotel", "desc": "Colorful whimsical patterns, local soul, vibrant palettes."},
    {"name": "Kitchener's Garden", "movies": "Secret Garden", "desc": "Lush emerald palms, botanical sanctuary, serene river."},
    {"name": "Tombs of the Nobles", "movies": "The Mummy, Indiana Jones", "desc": "Archaeological mystery, hillside rock tombs, grit."},
    {"name": "Aswan High Dam", "movies": "Tenet, Blade Runner", "desc": "Brutalist concrete, industrial power, massive scale."}
]

def harvest():
    print("🧹 Clearing old data...")
    try: index.delete(delete_all=True)
    except: pass
    
    print("🚀 Vectorizing Aswan Gold Sample...")
    vectors = []
    for i, loc in enumerate(ASWAN_DATA):
        text = f"{loc['name']} {loc['desc']} {loc['movies']}"
        v = model.encode(text).tolist()
        vectors.append({
            "id": f"aswan_{i}",
            "values": v,
            "metadata": {"name": loc['name'], "description": loc['desc']}
        })
    index.upsert(vectors=vectors)
    print("SUCCESS: Aswan Knowledge Loaded.")

if __name__ == "__main__":
    harvest()