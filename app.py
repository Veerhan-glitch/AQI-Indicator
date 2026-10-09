import os
from functools import lru_cache

from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter
import openmeteo_requests
import requests_cache
from retry_requests import retry
import os
import requests
from dotenv import load_dotenv

# Load .env values
load_dotenv()

app = Flask(__name__)
env_geolocator = Nominatim(user_agent="pancha-thon")


def _nominatim_lookup(operation, query, timeout):
    if operation == "reverse":
        return env_geolocator.reverse(query, timeout=timeout)
    return env_geolocator.geocode(query, timeout=timeout)


nominatim_lookup = RateLimiter(
    _nominatim_lookup,
    min_delay_seconds=1,
    max_retries=0,
    swallow_exceptions=False
)


@lru_cache(maxsize=512)
def cached_reverse_lookup(lat, lon):
    return nominatim_lookup("reverse", (lat, lon), timeout=5)

# Weather from Open-Meteo
def get_weather(lat, lon):
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "precipitation", "cloud_cover", "pressure_msl",
            "wind_speed_10m", "wind_direction_10m"
        ]
    }
    try:
        responses = openmeteo.weather_api(url, params=params)
        current = responses[0].Current()
        return {
            "temperature_2m": current.Variables(0).Value(),
            "humidity": current.Variables(1).Value(),
            "apparent_temperature": current.Variables(2).Value(),
            "precipitation": current.Variables(3).Value(),
            "cloud_cover": current.Variables(4).Value(),
            "pressure_msl": current.Variables(5).Value(),
            "wind_speed_10m": current.Variables(6).Value(),
            "wind_direction_10m": current.Variables(7).Value()
        }
    except Exception as e:
        print("Weather fetch error:", e)
        return {"error": "Weather data unavailable"}

# AQI from OpenWeatherMap
def get_aqi(lat, lon):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        r = requests.get(url, timeout=5)
        r_json = r.json()
        print("AQI API response:", r_json)

        if "list" not in r_json or not r_json["list"]:
            return {"aqi_index": -1, "message": r_json.get("message", "AQI unavailable")}

        data = r_json["list"][0]
        return {
            "aqi_index": data["main"]["aqi"],
            "pm2_5": data["components"]["pm2_5"],
            "pm10": data["components"]["pm10"],
            "no2": data["components"]["no2"],
            "o3": data["components"]["o3"]
        }
    except Exception as e:
        print("AQI fetch error:", e)
        return {"aqi_index": -1, "message": "Error fetching AQI"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    term = request.args.get("term")
    if not term:
        return jsonify({"error": "No search term provided"}), 400
    try:
        location = nominatim_lookup("geocode", term, timeout=5)
    except (GeocoderUnavailable, GeocoderTimedOut):
        return jsonify({"error": "Geocoding service unavailable or timed out."}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    if not location:
        return jsonify({"error": "Location not found"}), 404

    weather = get_weather(location.latitude, location.longitude)
    aqi = get_aqi(location.latitude, location.longitude)

    return jsonify({
        "latitude": location.latitude,
        "longitude": location.longitude,
        "location": location.address,
        "weather": weather,
        "aqi": aqi
    })

@app.route('/reverse')
def reverse_lookup():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "Latitude and longitude required"}), 400
    try:
        location = cached_reverse_lookup(round(lat, 3), round(lon, 3))
    except Exception as e:
        print("Reverse geocoding unavailable:", e)
        location = None

    weather = get_weather(lat, lon)
    aqi = get_aqi(lat, lon)

    return jsonify({
        "latitude": lat,
        "longitude": lon,
        "location": location.address if location else f"{lat:.4f}, {lon:.4f}",
        "weather": weather,
        "aqi": aqi
    })


if __name__ == '__main__':
    if os.environ.get("FLASK_ENV") != "production":
        app.run(debug=True)
