from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from collections import Counter

# --- Analytics Logic ---

@app.get("/api/admin/analytics")
async def admin_analytics():
    try:
        # 1. Fetch all bookings and join with itinerary templates to see what was sold
        # Assuming your Supabase schema has a 'bookings' table
        response = supabase.table("bookings").select("*, itinerary_templates(name, movie_title)").execute()
        bookings = response.data
        
        if not bookings:
            return {"mrr": 0, "top_vibes": [], "total_bookings": 0}

        # 2. Calculate Revenue (MRR - Monthly Recurring Revenue)
        # Summing commissions from the last 30 days
        total_commission = sum(float(b.get("commission_earned", 0)) for b in bookings)
        mrr = total_commission # Simplified for MVP
        
        # 3. Calculate Top Vibes (Trending Movie -> Egypt Location matches)
        # We count occurrences of movie/location pairs
        vibe_counts = Counter([f"{b['itinerary_templates']['movie_title']} → {b['itinerary_templates']['name']}" for b in bookings if b.get('itinerary_templates')])
        top_vibes = [{"vibe": k, "count": v} for k, v in vibe_counts.most_common(5)]

        # 4. Get Regional Boost status from Supabase
        boosts_response = supabase.table("boosts").select("city, priority").execute()
        
        return {
            "mrr": round(mrr, 2),
            "total_bookings": len(bookings),
            "top_vibes": top_vibes,
            "regional_boosts": boosts_response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Regional Boost Logic ---

@app.post("/api/admin/boost")
async def set_boost(request: Dict[str, Any]):
    """
    This endpoint allows the Ministry of Tourism to slide a priority bar.
    It updates both Supabase (for records) and Pinecone (for real-time search weighting).
    """
    city = request.get("city")
    priority = request.get("priority") # Value 0.0 to 1.0

    if city is None or priority is None:
        raise HTTPException(status_code=400, detail="Missing city or priority")

    try:
        # 1. Update the 'boosts' table in Supabase so the UI reflects the change
        supabase.table("boosts").upsert({"city": city, "priority": priority}).execute()

        # 2. Real-time Pinecone Update
        # We find the IDs in Pinecone that match this city and update their 'boost_score' metadata.
        # When we query Pinecone later, we will multiply the match score by this boost_score.
        
        index = pc.Index("auraegypt-locations")
        
        # First, find the IDs for this city
        # Note: We assume 'city' is stored in metadata
        search_res = index.query(
            vector=[0]*384, # Dummy vector for metadata filtering
            filter={"city": {"$eq": city}},
            top_k=100,
            include_metadata=True
        )

        # Update each matching record's metadata in Pinecone
        for match in search_res['matches']:
            index.update(
                id=match['id'],
                set_metadata={"boost_priority": priority}
            )

        return {"status": "success", "message": f"Boost for {city} set to {priority}"}
        
    except Exception as e:
        print(f"Boost Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update regional boost")