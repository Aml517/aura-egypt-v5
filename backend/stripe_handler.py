import os
import stripe
from fastapi import Request, HTTPException, APIRouter
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Stripe and Supabase
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET") # Get this from Stripe CLI or Dashboard
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

router = APIRouter()

@router.post("/api/create-checkout")
async def create_checkout(request: Request):
    try:
        data = await request.json()
        
        # We include metadata so the Webhook knows which user and trip to fulfill later
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Cinematic {data.get("movie", "Egypt")} Trip',
                        'description': f'Destination: {data.get("location", "Ancient Egypt")}',
                    },
                    'unit_amount': int(data["total_price"] * 100), # Stripe expects cents
                },
                'quantity': 1,
            }],
            mode='payment',
            metadata={
                "user_id": data.get("user_id"),
                "itinerary_id": data.get("itinerary_id"),
                "location": data.get("location")
            },
            success_url='http://localhost:3000/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:3000/',
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    This is the most important part. Stripe calls this when the payment is SUCCESSFUL.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None

    # 1. Verify the event came from Stripe (Security)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Handle the successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Extract the metadata we sent in 'create_checkout'
        user_id = session['metadata'].get('user_id')
        itinerary_id = session['metadata'].get('itinerary_id')
        
        # 3. FULFILLMENT: Update Supabase
        # Mark the booking as 'paid' so the user can see their full itinerary
        try:
            supabase.table("bookings").update({
                "status": "confirmed",
                "stripe_session_id": session['id'],
                "amount_paid": session['amount_total'] / 100
            }).eq("user_id", user_id).eq("itinerary_id", itinerary_id).execute()
            
            print(f"✅ Trip fulfilled for User: {user_id}")
        except Exception as e:
            print(f"❌ Database update failed: {e}")

    return {"status": "success"}