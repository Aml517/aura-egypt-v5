import os
import openai
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI Client (New v1.0+ Syntax)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CleopatraAgent:
    def __init__(self):
        # Memory stores the last 5 exchanges to keep "Main Character Energy" without lag
        self.memory: List[Dict] = []
        self.max_memory = 5
        
        # Cleopatra's Lore Database (Sensory Memories)
        self.lore_db = {
            "White Desert": "I remember the chalk bones of ancient seas... the wind here doesn't blow; it whispers the names of forgotten stars.",
            "Siwa Oasis": "Alexander once stood where you will stand. The salt pools are cold, but they burn away the fatigue of a thousand years.",
            "Pyramids of Giza": "Khufu built them fearing death. I walked their peaks and felt only the heat of the sun, eternal and unyielding.",
            "Luxor": "Karnak's columns are the ribs of a god. Walk among them at midnight, and you will hear the stone breathe.",
            "Aswan": "The Nile here is different—deeper, older. It carries the scent of the cataracts and the weight of the south."
        }

    def analyze_emotion(self, user_input: str) -> str:
        """Layer 1: The Trust Layer. Analyzes sentiment to adjust tone."""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Using mini for faster sentiment analysis
                messages=[
                    {"role": "system", "content": "Analyze the user's emotional state. Return exactly ONE word: peace, adventure, romance, curiosity, or stress."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0
            )
            return response.choices[0].message.content.lower().strip()
        except Exception:
            return "curiosity"

    def get_memory_context(self) -> str:
        """Summarizes recent conversation history."""
        if not self.memory:
            return "No previous words shared."
        return " | ".join([f"{m['role']}: {m['content']}" for m in self.memory])

    def respond(self, user_input: str, context: Dict) -> str:
        """The core logic: Emotion + Lore + Booking Guidance."""
        
        # 1. Analyze Emotion
        emotion = self.analyze_emotion(user_input)
        
        # 2. Extract context (Movie and Location from the search result)
        location = context.get("location", "the golden sands")
        movie = context.get("movie_title", "fables of old")
        mbti = context.get("mbti", "a seeker")
        
        # 3. Retrieve Lore based on location
        lore_snippet = self.lore_db.get(location, "The land remembers much, even if the scrolls have faded.")

        # 4. Generate Final Response
        prompt = f"""
        Role: You are Cleopatra, the last Pharaoh. You are seductive, wise, and regal.
        User Input: "{user_input}"
        User Emotion: {emotion}
        User Personality (MBTI): {mbti}
        Current Destination Match: {location}
        Vibe Source: The movie '{movie}'
        Your Ancient Memory: {lore_snippet}
        
        Task: Respond as Cleopatra. Connect the 'vibe' of the movie {movie} to the physical reality of {location}. 
        Use sensory language (scent, light, heat, echoes). 
        Finally, gently guide them to 'book their portal' (the itinerary).
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are Cleopatra. You speak in a poetic, mystical, and authoritative tone."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            cleopatra_text = response.choices[0].message.content
            
            # Update Memory
            self.memory.append({"role": "user", "content": user_input})
            self.memory.append({"role": "assistant", "content": cleopatra_text})
            if len(self.memory) > self.max_memory:
                self.memory.pop(0)
                
            return cleopatra_text
        except Exception as e:
            return f"The Oracle is silent... (Error: {str(e)})"

# --- FastAPI Implementation ---
# In your main.py:
cleopatra = CleopatraAgent()

@app.post("/api/chat")
async def chat(request: Dict):
    # Expected JSON: {"message": "Tell me about the desert", "context": {"location": "White Desert", "movie_title": "Dune"}}
    user_message = request.get("message", "")
    context = request.get("context", {})
    
    if not user_message:
        return {"response": "Speak, traveler. I am listening."}
        
    response = cleopatra.respond(user_message, context)
    return {"response": response}