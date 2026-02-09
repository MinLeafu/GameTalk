# User Bio

import requests

def get_location_by_ip():
    try:
    # Send a request to an IP geolocation API
        response = requests.get("https://ipinfo.io/json")
        data = response.json()

        if 'loc' in data:
            # Extract latitude and longitude
            lat, lon = map(float, data['loc'].split(','))
            city = data.get('city', 'Unknown')
            country = data.get('country', 'Unknown')
            print(f"Approximate Location: {city}, {country}")
            print(f"Coordinates: Latitude: {lat}, Longitude: {lon}")
            return lat, lon, city, country
        else:
            print("Location data not available from the API.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the API: {e}")
        return None

def user_bio():
    user_name = input ("What is your name?")
    user_age = input ("Age?")
    user_games = input ("What games do you play?")
    user_location = get_location_by_ip()
