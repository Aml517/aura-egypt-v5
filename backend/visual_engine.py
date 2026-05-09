import torch
import clip
from PIL import Image
import requests
from io import BytesIO

device = "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

class VisualAestheticEngine:
    def __init__(self):
        self.visual_db = {
            "Old Cataract Terrace": "https://images.unsplash.com/photo-1590073242678-70ee3fc28e8e",
            "Philae Temple at Dusk": "https://images.unsplash.com/photo-1572262013778-0062400e936b",
            "Elephantine Island Rocks": "https://images.unsplash.com/photo-1509152730246-6c7d448f3559",
            "Felucca at Golden Hour": "https://images.unsplash.com/photo-1544644181-1484b3fdfc62",
            "Nubian House": "https://images.unsplash.com/photo-1539768942893-daf53e448371",
            "Kitchener's Garden": "https://images.unsplash.com/photo-1568322422394-3cb4978a35e2",
            "Tombs of the Nobles": "https://images.unsplash.com/photo-1544971587-b842c27f8e14",
            "Aswan High Dam": "https://images.unsplash.com/photo-1518391846015-55a9cb0bb4ad"
        }

    def get_visual_score(self, movie_title, location_name):
        try:
            img_url = self.visual_db.get(location_name)
            if not img_url: return 55.0
            res = requests.get(img_url)
            img = preprocess(Image.open(BytesIO(res.content))).unsqueeze(0).to(device)
            txt = clip.tokenize([f"Cinematic style of {movie_title}"]).to(device)
            with torch.no_grad():
                sim = torch.cosine_similarity(model.encode_image(img), model.encode_text(txt))
                return float(sim.item() * 100)
        except: return 60.0

visual_engine = VisualAestheticEngine()