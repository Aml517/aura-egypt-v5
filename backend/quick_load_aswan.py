from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

MY_PINECONE_KEY = "pcsk_A2Tv5_JXNevtp5qTy5JaHi24ekKgt9FDsuvQz49HTXfnDMom8fx4ZNQuMGfNcEWqHSxD2"
pc = Pinecone(api_key=MY_PINECONE_KEY)
index = pc.Index("auraegypt-locations")
model = SentenceTransformer('all-MiniLM-L6-v2')

def load():
    index.delete(delete_all=True)
    data = [
        {"name": "Old Cataract Terrace", "desc": "Victorian luxury, colonial mystery, Agatha Christie vibes"},
        {"name": "Philae Temple at Dusk", "desc": "Mystical island temple, ancient magic, sacred geometry"},
        {"name": "Elephantine Island Rocks", "desc": "Alien granite boulders, brutalist nature, cosmic silence"},
        {"name": "Aswan High Dam", "desc": "Massive concrete brutalism, industrial power, scale"},
        {"name": "Tombs of the Nobles", "desc": "Archaeological grit, hillside mystery, Indiana Jones vibes"}
    ]
    vectors = []
    for i, item in enumerate(data):
        v = model.encode(item["desc"]).tolist()
        vectors.append({"id": f"aswan_{i}", "values": v, "metadata": item})
    index.upsert(vectors=vectors)
    print("SUCCESS: Production knowledge base online.")

if __name__ == "__main__":
    load()