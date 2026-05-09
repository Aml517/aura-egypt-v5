import uuid
import urllib.parse
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# 1. Expanded Affiliate Map
# These are base URLs for your partners. 
# In production, these would be your actual Deep Link generators.
AFFILIATE_LINKS = {
    "White Desert": {
        "tour": "https://www.viator.com/tours/Cairo/White-Desert-and-Bahariya-Oasis",
        "hotel": "https://www.booking.com/searchresults.html?ss=Bahariya+Oasis"
    },
    "Siwa Oasis": {
        "tour": "https://www.viator.com/tours/Cairo/Private-Siwa-Oasis-Adventure",
        "hotel": "https://www.booking.com/searchresults.html?ss=Siwa"
    },
    "Pyramids of Giza": {
        "tour": "https://www.viator.com/tours/Cairo/Giza-Pyramids-and-Sphinx-Tour",
        "hotel": "https://www.booking.com/hotel/eg/marriott-mena-house-cairo"
    },
    "Luxor Temple": {
        "tour": "https://www.viator.com/tours/Luxor/Full-Day-Tour-to-East-and-West-Banks",
        "hotel": "https://www.booking.com/hotel/eg/winter-palace"
    }
}

# 2. Input Validation Model
class BookingLog(BaseModel):
    user_id: str
    itinerary_id: str
    price: float
    source: str # e.g., "Viator" or "Booking.com"
    location: str

# 3. Dynamic URL Generator
def generate_affiliate_url(base_url: str, context: Dict[str, Any]):
    """
    Safely appends UTM parameters and Affiliate IDs to a partner URL.
    Handles existing query parameters in the base_url.
    """
    # Clean up movie title for URL (replace spaces with +)
    movie = urllib.parse.quote_plus(context.get('movie', 'unknown'))
    mbti = context.get('mbti', 'explorer')
    
    params = {
        "aid": "auraegypt_2024",       # Your official Partner ID
        "utm_source": "auraegypt",     # Marketing Source
        "utm_campaign": movie,         # Track which movie drove the sale
        "utm_medium": mbti,            # Track which personality type buys more
        "ref": "cleopatra_ai"          # Character attribution
    }
    
    url_parts = list(urllib.parse.urlparse(base_url))
    query = dict(urllib.parse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urllib.parse.urlencode(query)
    
    return urllib.parse.urlunparse(url_parts)

# 4. Tracking Endpoint
@app.post("/api/track-booking")
async def track_booking(request: BookingLog):
    """
    Triggered when a user clicks 'Book Trip'. 
    Calculates estimated commission and saves to Supabase.
    """
    try:
        # Generate a unique tracking ID for this specific transaction
        tracking_id = f"AE-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate expected commission (average 8%)
        estimated_commission = request.price * 0.08
        
        # Insert into Supabase 'bookings' table
        # This data feeds your Admin Analytics 'MRR' chart
        supabase.table("bookings").insert({
            "tracking_id": tracking_id,
            "user_id": request.user_id,
            "itinerary_id": request.itinerary_id,
            "price": request.price,
            "commission_earned": estimated_commission,
            "affiliate_source": request.source,
            "location_name": request.location,
            "status": "pending" # Changes to 'confirmed' via partner webhook
        }).execute()
        
        return {
            "status": "success",
            "tracking_id": tracking_id,
            "estimated_commission": estimated_commission
        }
    except Exception as e:
        print(f"Tracking Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to log booking")

# 5. Helper to get links for Cleopatra
def get_itinerary_links(location_name: str, movie: str, mbti: str):
    """
    Used by the main itinerary generator to provide clickable links.
    """
    links = AFFILIATE_LINKS.get(location_name, AFFILIATE_LINKS["Pyramids of Giza"])
    context = {"movie": movie, "mbti": mbti}
    
    return {
        "tour_link": generate_affiliate_url(links["tour"], context),
        "hotel_link": generate_affiliate_url(links["hotel"], context)
    }