import requests

def geocode_location(location_name: str) -> tuple[float, float] | None:
    """
    Geocodes a location name using the Nominatim API.
    Returns a tuple of (latitude, longitude) or None if not found.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location_name,
        "format": "json",
        "limit": 1,
        "countrycodes": "de"  # Limit search to Germany
    }
    headers = {
        "User-Agent": "German Bau Scraper (https://github.com/a-j-s/german-bau-scraper)"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except requests.exceptions.RequestException as e:
        print(f"Geocoding request failed: {e}")
    except (KeyError, IndexError, ValueError) as e:
        print(f"Failed to parse geocoding response: {e}")

    return None
