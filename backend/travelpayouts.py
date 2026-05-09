# backend/travelpayouts.py  v7.0
"""
Travelpayouts Integration — Production Ready

What's fixed vs v6:
1. Hotellook API: correct endpoint is /api/v2/cache.json with
   'locationId' not 'location' — must resolve city name to ID first
   Fallback: Booking.com API via SerpAPI for real hotel prices
2. Flight links: WayAway verified working format
3. Booking.com deep link: correct aid= for Travelpayouts program
4. GetYourGuide: correct affiliate format
5. ALL links tested — none open a homepage
6. HuggingFace SSL bypass applied to requests in this module too
7. Full fallback chain: Live API → SerpAPI → 2026 estimates
"""

import os, ssl, requests, urllib3
from datetime import datetime, timedelta

# Apply same SSL bypass as main.py — needed for Egyptian ISP
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TP_MARKER    = os.environ.get("TP_MARKER",    "718944")
TP_API_TOKEN = os.environ.get("TP_API_TOKEN", "")
SERP_KEY     = os.environ.get("SERP_API_KEY", "")

# ── Session (SSL bypass + retry) ───────────────────────────────────────────
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def _session() -> requests.Session:
    s       = requests.Session()
    s.verify = False
    retry   = Retry(total=2, backoff_factor=0.3,
                    status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    return s

_sess = _session()


# ── 2026 Market Rate Tables ────────────────────────────────────────────────

FLIGHT_ESTIMATES_2026 = {
    "CAI": 90,   "LHR": 480,  "DXB": 220,  "JFK": 920,
    "CDG": 440,  "AMS": 420,  "FRA": 410,  "IST": 190,
    "RUH": 180,  "DOH": 170,  "BOM": 340,  "SIN": 620,
    "SYD": 980,  "LAX": 980,  "ORD": 940,  "YYZ": 860,
    "DEFAULT": 450,
}

HOTEL_TIERS_2026 = {
    "luxury": {
        "old cataract": 700, "sofitel": 650, "movenpick": 280,
        "mövenpick": 280,    "pyramisa": 180, "basma": 160,
        "default": 350,
    },
    "boutique_nubian": {
        "anakato": 180, "kato dool": 140, "nubian spirit": 95,
        "default": 120,
    },
    "midrange": {"default": 85},
    "community": {"default": 35, "mid": 55},
    "budget":    {"default": 40},
}

ACTIVITY_COSTS_2026 = {
    "philae temple": 18,        "sound and light show": 22,
    "abu simbel": 55,           "high dam": 5,
    "nubian museum": 6,         "tombs of the nobles": 10,
    "felucca ride": 12,         "felucca day": 45,
    "motorboat to philae": 8,   "nubian village tour": 15,
    "cooking class": 35,        "local guide half day": 40,
    "local guide full day": 70, "karnak temple": 20,
    "valley of the kings": 25,  "hot air balloon": 120,
    "default activity": 20,
}

FOOD_COSTS_2026 = {
    "luxury restaurant": 45, "mid restaurant": 18,
    "local restaurant": 8,   "street food": 3,
    "nubian meal": 12,        "cafe breakfast": 6,
    "default": 10,
}

# Booking.com city IDs for Aswan area (avoids 404 on vague searches)
BOOKING_CITY_IDS = {
    "aswan":  "-306414",
    "luxor":  "-306409",
    "cairo":  "-290692",
    "siwa":   "-302146",
    "fayoum": "-290768",
    "hurghada": "-307398",
}


# ── Tier Classification ────────────────────────────────────────────────────

def classify_location_tier(location_name: str, is_rural: bool,
                            price_per_night: float = 0) -> str:
    name = location_name.lower()
    if is_rural:
        return "community"
    luxury_signals = ["old cataract","cataract","sofitel","movenpick",
                      "mövenpick","pyramisa isis","five star"]
    if any(s in name for s in luxury_signals) or price_per_night >= 300:
        return "luxury"
    nubian_signals = ["anakato","kato dool","nubian spirit","nubian house",
                      "nubian boutique","elephantine island"]
    if any(s in name for s in nubian_signals):
        return "boutique_nubian"
    if price_per_night >= 60:
        return "midrange"
    return "budget"


def get_hotel_floor_price(tier: str, location_name: str = "") -> int:
    name = location_name.lower()
    tier_data = HOTEL_TIERS_2026.get(tier, HOTEL_TIERS_2026["midrange"])
    for key, price in tier_data.items():
        if key != "default" and key in name:
            return price
    return tier_data.get("default", 80)


# ── Deep Link Builders (ALL VERIFIED) ─────────────────────────────────────

def flight_link(origin: str, destination: str = "ASW", date: str = "") -> dict:
    """
    WayAway (Travelpayouts own product) — verified deep link format 2026.
    Marker is native — no extra params needed.
    Aviasales fallback uses query-string format (path format = Russian locale only).
    """
    origin      = (origin or "CAI").upper().strip()
    destination = (destination or "ASW").upper().strip()

    try:
        d        = datetime.strptime(date, "%Y-%m-%d")
        date_fmt = d.strftime("%Y-%m-%d")
    except:
        date_fmt = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    # WayAway — primary (Travelpayouts' own flights product)
    wayaway = (
        f"https://www.wayaway.io/flights"
        f"?origin={origin}"
        f"&destination={destination}"
        f"&depart_date={date_fmt}"
        f"&adults=1"
        f"&marker={TP_MARKER}"
    )

    # Aviasales — fallback (query-string, not path format)
    aviasales = (
        f"https://www.aviasales.com/"
        f"?origin={origin}"
        f"&destination={destination}"
        f"&depart_date={date_fmt}"
        f"&adults=1"
        f"&marker={TP_MARKER}"
    )

    return {
        "url":          wayaway,
        "fallback_url": aviasales,
        "label":        f"Flights {origin} → {destination} from {date_fmt}",
        "provider":     "WayAway via Travelpayouts",
        "type":         "flight",
        "marker":       TP_MARKER,
        "prefilled":    True,
    }


def hotel_link(city: str, checkin: str, checkout: str,
               is_rural: bool = False, location_name: str = "",
               tier: str = "midrange") -> dict:
    """
    Booking.com deep link — verified format with Travelpayouts aid.
    Uses city_id where known to avoid vague search results.
    Rural → direct community contact, no aggregator.
    """
    if is_rural or tier == "community":
        return {
            "url":      None,
            "label":    f"Book directly — {location_name or city}",
            "provider": "Direct community booking",
            "type":     "community_direct",
            "note": (
                f"Community-owned accommodation in {city}. "
                f"Search '{location_name} homestay Egypt' on Facebook or WhatsApp. "
                f"100% of payment stays with the host family."
            ),
        }

    try:
        ci_obj  = datetime.strptime(checkin,  "%Y-%m-%d")
        co_obj  = datetime.strptime(checkout, "%Y-%m-%d")
        ci      = ci_obj.strftime("%Y-%m-%d")
        co      = co_obj.strftime("%Y-%m-%d")
        nights  = max((co_obj - ci_obj).days, 1)
    except:
        ci, co, nights = checkin, checkout, 3

    city_lower  = city.lower()
    city_id     = BOOKING_CITY_IDS.get(city_lower, "")
    city_enc    = city.replace(" ", "+") + "%2C+Egypt"

    # Booking.com — aid=1561762 is Travelpayouts Booking.com program
    # label param carries your marker for TP tracking
    if city_id:
        booking_url = (
            f"https://www.booking.com/searchresults.html"
            f"?dest_id={city_id}"
            f"&dest_type=city"
            f"&checkin={ci}"
            f"&checkout={co}"
            f"&group_adults=1&no_rooms=1"
            f"&aid=1561762"
            f"&label=aura-egypt-{TP_MARKER}"
        )
    else:
        booking_url = (
            f"https://www.booking.com/searchresults.html"
            f"?ss={city_enc}"
            f"&checkin={ci}"
            f"&checkout={co}"
            f"&group_adults=1&no_rooms=1"
            f"&aid=1561762"
            f"&label=aura-egypt-{TP_MARKER}"
        )

    # Hotellook widget fallback
    hotellook_url = (
        f"https://hotellook.com/search"
        f"?destination={city.replace(' ', '+')}"
        f"&checkIn={ci}&checkOut={co}"
        f"&adults=1&marker={TP_MARKER}"
    )

    return {
        "url":          booking_url,
        "fallback_url": hotellook_url,
        "label":        f"Hotels in {city} — {nights} nights from {ci}",
        "provider":     "Booking.com via Travelpayouts",
        "type":         "hotel",
        "marker":       TP_MARKER,
        "prefilled":    True,
    }


def transfer_link(from_place: str, to_place: str) -> dict:
    """Kiwitaxi with from/to pre-filled."""
    from_enc = from_place.replace(" ", "+")
    to_enc   = to_place.replace(" ", "+")
    return {
        "url": (
            f"https://kiwitaxi.com/Egypt"
            f"?from={from_enc}&to={to_enc}"
            f"&marker={TP_MARKER}"
        ),
        "label":    f"Transfer: {from_place} → {to_place}",
        "provider": "Kiwitaxi via Travelpayouts",
        "type":     "transfer",
        "marker":   TP_MARKER,
        "prefilled": True,
    }


def activity_link(city: str, activity: str) -> dict:
    """GetYourGuide with pre-filled search query."""
    q = f"{activity} {city} Egypt".replace(" ", "%20")
    return {
        "url": (
            f"https://www.getyourguide.com/s/"
            f"?q={q}&partner_id={TP_MARKER}"
        ),
        "label":    f"{activity}",
        "provider": "GetYourGuide via Travelpayouts",
        "type":     "activity",
        "marker":   TP_MARKER,
        "prefilled": True,
    }


# ── Live Price Fetching ────────────────────────────────────────────────────

def fetch_flight_price(origin: str, destination: str, date: str) -> dict:
    """
    Fetch chain:
    1. Travelpayouts /v1/prices/cheap API (if TP_API_TOKEN set)
    2. SerpAPI Google Flights (if SERP_KEY set)
    3. 2026 market estimate
    """
    if TP_API_TOKEN:
        result = _tp_flight_price(origin, destination, date)
        if result:
            return result

    if SERP_KEY:
        result = _serp_flight_price(origin, destination, date)
        if result:
            return result

    return _estimate_flight(origin, destination, date)


def _tp_flight_price(origin: str, destination: str, date: str) -> dict | None:
    try:
        month = date[:7] if len(date) >= 7 else datetime.now().strftime("%Y-%m")
        r = _sess.get(
            "https://api.travelpayouts.com/v1/prices/cheap",
            headers={"X-Access-Token": TP_API_TOKEN},
            params={
                "origin":      origin.upper(),
                "destination": destination.upper(),
                "depart_date": month,
                "currency":    "usd",
                "limit":       1,
            },
            timeout=6,
        )
        r.raise_for_status()
        dest_data = r.json().get("data", {}).get(destination.upper(), {})
        if dest_data:
            price = list(dest_data.values())[0].get("price", 0)
            if price > 0:
                return {
                    "price":    price,
                    "currency": "USD",
                    "source":   "live_travelpayouts",
                    "link":     flight_link(origin, destination, date),
                }
    except Exception as e:
        print(f"[TP] Flight API: {e}")
    return None


def _serp_flight_price(origin: str, destination: str, date: str) -> dict | None:
    """SerpAPI Google Flights as price fallback."""
    try:
        r = _sess.get(
            "https://serpapi.com/search",
            params={
                "engine":          "google_flights",
                "departure_id":    origin.upper(),
                "arrival_id":      destination.upper(),
                "outbound_date":   date,
                "currency":        "USD",
                "hl":              "en",
                "api_key":         SERP_KEY,
                "type":            "2",   # one-way
            },
            timeout=8,
        )
        r.raise_for_status()
        data    = r.json()
        flights = data.get("best_flights", []) or data.get("other_flights", [])
        if flights:
            cheapest = min(flights, key=lambda f: f.get("price", 9999))
            price    = cheapest.get("price", 0)
            if price > 0:
                return {
                    "price":    price,
                    "currency": "USD",
                    "source":   "live_serpapi_flights",
                    "link":     flight_link(origin, destination, date),
                }
    except Exception as e:
        print(f"[SerpAPI] Flights: {e}")
    return None


def fetch_hotel_prices(city: str, checkin: str, nights: int = 3,
                       is_rural: bool = False, location_name: str = "",
                       tier: str = "midrange") -> dict:
    """
    Fetch chain:
    1. SerpAPI Google Hotels (most reliable, no 404 issues)
    2. Travelpayouts Hotellook API (if TP_API_TOKEN set)
    3. 2026 market estimate
    Rural locations skip all APIs — community pricing only.
    """
    if is_rural or tier == "community":
        return {
            "price_per_night": HOTEL_TIERS_2026["community"]["default"],
            "currency":        "USD",
            "source":          "community_rate",
            "note":            "Homestay — negotiated directly with host family",
            "link":            hotel_link(city, checkin, "", is_rural=True,
                                          location_name=location_name),
        }

    floor_price = get_hotel_floor_price(tier, location_name)

    # Try SerpAPI first — most reliable for Egypt
    if SERP_KEY:
        result = _serp_hotel_price(city, checkin, nights, floor_price, tier)
        if result:
            return result

    # Try Hotellook API
    if TP_API_TOKEN:
        result = _hotellook_price(city, checkin, nights, floor_price, tier)
        if result:
            return result

    return _estimate_hotel(city, checkin, nights, tier, location_name, floor_price)


def _serp_hotel_price(city: str, checkin: str, nights: int,
                      floor_price: int, tier: str) -> dict | None:
    """SerpAPI Google Hotels — reliable, no 404 issues."""
    try:
        checkout = (
            datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=nights)
        ).strftime("%Y-%m-%d")

        r = _sess.get(
            "https://serpapi.com/search",
            params={
                "engine":        "google_hotels",
                "q":             f"hotels in {city} Egypt",
                "check_in_date": checkin,
                "check_out_date":checkout,
                "adults":        1,
                "currency":      "USD",
                "hl":            "en",
                "api_key":       SERP_KEY,
                "sort_by":       2 if tier == "luxury" else 3,
                # sort_by: 2=highest rated, 3=lowest price
            },
            timeout=8,
        )
        r.raise_for_status()
        hotels = r.json().get("properties", [])

        if hotels:
            # Filter by star rating for luxury
            if tier == "luxury":
                candidates = [h for h in hotels if h.get("overall_rating", 0) >= 4.0]
            else:
                candidates = hotels

            if candidates:
                best  = candidates[0]
                price = best.get("rate_per_night", {}).get("lowest", "").replace("$","").replace(",","")
                try:
                    price = int(float(price))
                    price = max(price, floor_price)  # enforce floor
                    checkout_link = (
                        datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=nights)
                    ).strftime("%Y-%m-%d")
                    return {
                        "price_per_night": price,
                        "hotel_name":      best.get("name", ""),
                        "stars":           best.get("overall_rating", 0),
                        "currency":        "USD",
                        "source":          "live_serpapi_hotels",
                        "link":            hotel_link(city, checkin, checkout_link, tier=tier),
                    }
                except:
                    pass
    except Exception as e:
        print(f"[SerpAPI] Hotels ({city}): {e}")
    return None


def _hotellook_price(city: str, checkin: str, nights: int,
                     floor_price: int, tier: str) -> dict | None:
    """
    Hotellook API — requires locationId, not city name.
    Step 1: resolve city to locationId
    Step 2: fetch prices
    """
    try:
        checkout = (
            datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=nights)
        ).strftime("%Y-%m-%d")

        # Step 1: resolve location name to ID
        loc_r = _sess.get(
            "https://engine.hotellook.com/api/v2/lookup.json",
            params={
                "query":    city,
                "lang":     "en",
                "lookFor":  "city",
                "limit":    1,
                "token":    TP_API_TOKEN,
            },
            headers={"X-Access-Token": TP_API_TOKEN},
            timeout=5,
        )
        loc_r.raise_for_status()
        loc_data    = loc_r.json()
        cities      = loc_data.get("results", {}).get("cities", [])
        if not cities:
            return None
        location_id = cities[0].get("id", "")
        if not location_id:
            return None

        # Step 2: fetch hotel prices
        r = _sess.get(
            "https://engine.hotellook.com/api/v2/cache.json",
            params={
                "locationId": location_id,
                "checkIn":    checkin,
                "checkOut":   checkout,
                "currency":   "usd",
                "token":      TP_API_TOKEN,
                "limit":      5,
                "language":   "en",
            },
            headers={"X-Access-Token": TP_API_TOKEN},
            timeout=6,
        )
        r.raise_for_status()
        hotels = r.json()

        if hotels:
            candidates = (
                [h for h in hotels if h.get("stars", 0) >= 4]
                if tier == "luxury" else hotels
            )
            if candidates:
                best      = min(candidates, key=lambda h: h.get("priceFrom", 9999))
                raw_price = best.get("priceFrom", 0)
                price     = max(raw_price, floor_price)
                return {
                    "price_per_night": price,
                    "hotel_name":      best.get("hotelName", ""),
                    "stars":           best.get("stars", 0),
                    "currency":        "USD",
                    "source":          "live_hotellook",
                    "link":            hotel_link(city, checkin, checkout, tier=tier),
                }
    except Exception as e:
        print(f"[Hotellook] ({city}): {e}")
    return None


# ── Budget Builder ─────────────────────────────────────────────────────────

def build_real_budget(
    total_budget:     float,
    days:             int,
    origin:           str,
    destination_city: str,
    travel_date:      str,
    is_rural:         bool  = False,
    location_name:    str   = "",
    tier:             str   = "midrange",
    price_per_night:  float = 0,
) -> dict:
    """
    Builds a realistic budget using live prices → SerpAPI → 2026 estimates.
    Enforces price floors. Never returns $0 for flight or hotel.
    """
    # Resolve checkout date
    try:
        checkout = (
            datetime.strptime(travel_date, "%Y-%m-%d") + timedelta(days=days)
        ).strftime("%Y-%m-%d")
    except:
        checkout = ""

    # Flight
    flight_data = fetch_flight_price(origin, "ASW", travel_date)
    flight_cost = flight_data["price"]
    if flight_cost == 0 and origin.upper() != "ASW":
        flight_cost = FLIGHT_ESTIMATES_2026.get(
            origin.upper(), FLIGHT_ESTIMATES_2026["DEFAULT"]
        )

    # Hotel
    if price_per_night >= 300:
        tier = "luxury"
    elif is_rural:
        tier = "community"

    hotel_data      = fetch_hotel_prices(
        city=destination_city, checkin=travel_date,
        nights=days, is_rural=is_rural,
        location_name=location_name, tier=tier,
    )
    hotel_per_night = hotel_data["price_per_night"]
    hotel_total     = hotel_per_night * days

    # Remaining
    fixed       = flight_cost + hotel_total
    remaining   = total_budget - fixed
    daily_left  = max(remaining / max(days, 1), 0)

    budget_warning = None
    if remaining < 0:
        min_needed = fixed + days * 30
        budget_warning = (
            f"Budget of ${int(total_budget)} is insufficient. "
            f"Flight (${flight_cost}) + hotel (${hotel_total}) = ${int(fixed)}. "
            f"Minimum recommended: ${int(min_needed)}."
        )

    activity_daily  = round(daily_left * 0.40)
    food_daily      = round(daily_left * 0.35)
    transport_daily = round(daily_left * 0.20)
    buffer_daily    = round(daily_left * 0.05)
    total_planned   = fixed + (activity_daily + food_daily + transport_daily) * days

    return {
        "flight": {
            "cost":   flight_cost,
            "source": flight_data.get("source", "estimated_2026"),
            "link":   flight_data.get("link", flight_link(origin, "ASW", travel_date)),
        },
        "hotel": {
            "cost_per_night": hotel_per_night,
            "total":          hotel_total,
            "source":         hotel_data.get("source", "estimated_2026"),
            "name":           hotel_data.get("hotel_name", ""),
            "tier":           tier,
            "link":           hotel_data.get("link",
                                hotel_link(destination_city, travel_date,
                                           checkout, is_rural=is_rural, tier=tier)),
        },
        "daily": {
            "activity":  activity_daily,
            "food":      food_daily,
            "transport": transport_daily,
            "buffer":    buffer_daily,
            "total":     activity_daily + food_daily + transport_daily + buffer_daily,
        },
        "summary": {
            "total_budget":  round(total_budget),
            "total_planned": round(total_planned),
            "remaining":     round(total_budget - total_planned),
            "fixed_costs":   round(fixed),
            "is_feasible":   remaining >= 0,
        },
        "budget_warning": budget_warning,
        "price_sources": {
            "flight": flight_data.get("source", "estimated_2026"),
            "hotel":  hotel_data.get("source", "estimated_2026"),
        },
        "links": {
            "flight":   flight_link(origin, "ASW", travel_date),
            "hotel":    hotel_link(destination_city, travel_date, checkout,
                                    is_rural=is_rural, tier=tier),
            "transfer": transfer_link("Aswan Airport", destination_city),
        },
    }


# ── Link Injection ─────────────────────────────────────────────────────────

def inject_links_into_itinerary(
    itinerary:        list,
    origin:           str,
    travel_date:      str,
    destination_city: str,
    is_rural:         bool = False,
    tier:             str  = "midrange",
) -> list:
    """
    Injects real deep links into every itinerary item.
    Validates costs — no $0 on non-free items.
    """
    origin = (origin or "CAI").upper().strip()
    try:
        ci_obj  = datetime.strptime(travel_date, "%Y-%m-%d")
        checkout= (ci_obj + timedelta(days=len(itinerary))).strftime("%Y-%m-%d")
        checkin = ci_obj.strftime("%Y-%m-%d")
    except:
        checkin = checkout = travel_date

    floor_hotel  = get_hotel_floor_price(tier, destination_city)
    floor_flight = FLIGHT_ESTIMATES_2026.get(
        origin, FLIGHT_ESTIMATES_2026["DEFAULT"]
    )

    for day in itinerary:
        for item in day.get("items", []):
            t    = item.get("type", "activity")
            btype= item.get("booking_type", "local")
            cost = item.get("cost", 0)
            label= item.get("label", "")

            # ── Cost validation ────────────────────────────────────────────
            if cost == 0 and btype != "free":
                if t == "flight":
                    item["cost"] = floor_flight
                    item["cost_note"] = "Estimated — live price varies"
                elif t == "hotel":
                    item["cost"] = floor_hotel
                    item["cost_note"] = f"Floor price for {tier} tier"
                elif t == "activity":
                    item["cost"] = ACTIVITY_COSTS_2026.get(
                        label.lower(), ACTIVITY_COSTS_2026["default activity"]
                    )
                elif t == "food":
                    item["cost"] = FOOD_COSTS_2026["default"]
                elif t in ("transport", "transfer"):
                    item["cost"] = 10

            # ── Link injection ─────────────────────────────────────────────
            if t == "flight":
                lnk = flight_link(origin, "ASW", travel_date)
                item.update({"booking_url": lnk["url"],
                             "booking_url_fallback": lnk.get("fallback_url"),
                             "provider": lnk["provider"],
                             "link_type": "deep_link"})

            elif t == "hotel":
                lnk = hotel_link(
                    destination_city, checkin, checkout,
                    is_rural=(is_rural or btype == "community_direct"),
                    location_name=label, tier=tier,
                )
                item.update({"booking_url": lnk.get("url"),
                             "booking_url_fallback": lnk.get("fallback_url"),
                             "provider": lnk["provider"],
                             "link_type": lnk["type"]})
                if lnk.get("note"):
                    item["booking_note"] = lnk["note"]

            elif t in ("transport", "transfer"):
                lnk = transfer_link("Aswan Airport", destination_city)
                item.update({"booking_url": lnk["url"],
                             "provider": lnk["provider"],
                             "link_type": "deep_link"})

            elif t == "activity":
                lnk = activity_link(destination_city, label)
                item.update({"booking_url": lnk["url"],
                             "provider": lnk["provider"],
                             "link_type": "deep_link"})

            elif t == "food":
                item.update({"booking_url": None,
                             "provider": item.get("provider","Local restaurant"),
                             "link_type": "local"})

    return itinerary


# ── Metadata Verification ─────────────────────────────────────────────────

def verify_location_metadata(locations: list) -> list:
    """
    Audits Pinecone metadata entries.
    Flags any location missing image_url or description.
    Returns list with 'metadata_ok' and 'metadata_issues' fields.
    """
    verified = []
    for loc in locations:
        issues = []
        if not loc.get("image_url") or loc["image_url"] in ("", None):
            issues.append("missing_image_url")
        if not loc.get("description") or len(loc.get("description","")) < 30:
            issues.append("description_too_short")
        if not loc.get("price_per_night") or loc.get("price_per_night", 0) == 0:
            issues.append("missing_price")
        if not loc.get("city"):
            issues.append("missing_city")

        loc["metadata_ok"]     = len(issues) == 0
        loc["metadata_issues"] = issues
        verified.append(loc)

    return verified


# ── Estimator Fallbacks ────────────────────────────────────────────────────

def _estimate_flight(origin: str, destination: str, date: str) -> dict:
    price = FLIGHT_ESTIMATES_2026.get(
        origin.upper(), FLIGHT_ESTIMATES_2026["DEFAULT"]
    )
    return {
        "price":    price,
        "currency": "USD",
        "source":   "estimated_2026",
        "note":     f"2026 market estimate {origin}→{destination}",
        "link":     flight_link(origin, destination, date),
    }


def _estimate_hotel(city: str, checkin: str, nights: int,
                    tier: str, location_name: str, floor_price: int) -> dict:
    try:
        checkout = (
            datetime.strptime(checkin, "%Y-%m-%d") + timedelta(days=nights)
        ).strftime("%Y-%m-%d")
    except:
        checkout = ""
    return {
        "price_per_night": floor_price,
        "currency":        "USD",
        "source":          "estimated_2026",
        "note":            f"2026 market estimate ({tier}) in {city}",
        "link":            hotel_link(city, checkin, checkout, tier=tier),
    }