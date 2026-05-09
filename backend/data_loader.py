import os
import time
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# ===========================================================
# 🔑 EMERGENCY KEY (Hardcoded for immediate data upload)
# ===========================================================
MY_PINECONE_KEY = "pcsk_A2Tv5_JXNevtp5qTy5JaHi24ekKgt9FDsuvQz49HTXfnDMom8fx4ZNQuMGfNcEWqHSxD2"
# ===========================================================

# 1. Initialize the AI Model
print("🔄 Loading AI Model (this may take a moment)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Curated Data for Egypt
EGYPT_LOCATIONS = [
    {"name": "White Desert", "desc": "Cosmic isolation, white chalk monoliths, silent wind, star-filled night sky, otherworldly moonscape."},
    {"name": "Pyramids of Giza", "desc": "Ancient stone giants, golden dawn light, eternal mystery, heavy historical weight, royal grandeur."},
    {"name": "Luxor Karnak Temple", "desc": "Colossal sandstone columns, whispering shadows, divine power, sacred geometry, echoes of pharaohs."},
    {"name": "Siwa Oasis", "desc": "Hidden emerald pools, ancient salt mines, mud-brick fortresses, deep isolation, mystic oracle energy."},
    {"name": "Old Cataract Hotel", "desc": "Agatha Christie mystery, colonial elegance, deep Nile currents, sunset on a felucca, slow luxury."},
    {"name": "Khan el-Khalili", "desc": "Golden chaos, scent of spice and incense, crowded history, glittering brass, narrow medieval alleys."},
    {"name": "Mount Sinai", "desc": "Biblical silence, red granite peaks, spiritual ascension, freezing dawn, ancient monastery bells."},
    {"name": "Marsa Alam", "desc": "Alien turquoise waters, untouched coral reefs, silent dugongs, coastal solitude, vibrant marine life."},
    {"name": "Temple of Philae", "desc": "Island of Isis, water-mirrored stone, romantic mysticism, gentle boat approach, feminine divine energy."}
]

def load_data():
    # Initialize Pinecone
    pc = Pinecone(api_key=MY_PINECONE_KEY)
    index_name = "auraegypt-locations"

    # Create Index if it doesn't exist
    if index_name not in pc.list_indexes().names():
        print(f"🏗️ Creating index: {index_name}...")
        pc.create_index(
            name=index_name, 
            dimension=384, 
            metric='cosine', 
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)

    index = pc.Index(index_name)

    # 3. Vectorize and Upload
    print("🚀 Vectorizing and uploading Egypt locations...")
    vectors = []
    for i, loc in enumerate(EGYPT_LOCATIONS):
        v = model.encode(loc["desc"]).tolist()
        vectors.append({
            "id": f"loc_{i}", 
            "values": v, 
            "metadata": {
                "name": loc["name"], 
                "description": loc["desc"]
            }
        })
    
    index.upsert(vectors=vectors)
    print(f"SUCCESS: Loaded {len(vectors)} locations into Pinecone.")

if __name__ == "__main__":
    load_data()