import requests

def get_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        location = data.get('loc', 'Unknown location')
        city = data.get('city', 'Unknown city')
        region = data.get('region', 'Unknown region')
        country = data.get('country', 'Unknown country')
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={location}"

        locatoin_str = f"Google Maps URL: {google_maps_url}"
        return locatoin_str
    except Exception as e:
        return f"Error retrieving location: {e}"