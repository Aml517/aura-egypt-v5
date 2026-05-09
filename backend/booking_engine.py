import urllib.parse

class BookingEngine:
    def __init__(self):
        self.marker = "718944" 

    def generate_link(self, location_name):
        query = urllib.parse.quote(f"{location_name} Aswan Egypt")
        # Direct trackable search on Trip.com
        return f"https://www.trip.com/search/all?keyword={query}&marker={self.marker}"

booking_engine = BookingEngine()