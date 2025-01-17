from flask import Flask, render_template, request
from geopy.geocoders import Nominatim
from functools import partial
app = Flask(__name__)
geolocator = Nominatim(user_agent="Pancha-Thon")



import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 28.6273928,
	"longitude": 77.1716954,
	"current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation", "rain", "showers", "snowfall", "weather_code", "cloud_cover", "pressure_msl", "surface_pressure", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
	"hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "weather_code", "wind_speed_10m", "soil_temperature_6cm"]
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Current values. The order of variables needs to be the same as requested.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_relative_humidity_2m = current.Variables(1).Value()
current_apparent_temperature = current.Variables(2).Value()
current_is_day = current.Variables(3).Value()
current_precipitation = current.Variables(4).Value()
current_rain = current.Variables(5).Value()
current_showers = current.Variables(6).Value()
current_snowfall = current.Variables(7).Value()
current_weather_code = current.Variables(8).Value()
current_cloud_cover = current.Variables(9).Value()
current_pressure_msl = current.Variables(10).Value()
current_surface_pressure = current.Variables(11).Value()
current_wind_speed_10m = current.Variables(12).Value()
current_wind_direction_10m = current.Variables(13).Value()
current_wind_gusts_10m = current.Variables(14).Value()
l=[]
l.append(f"Current time {current.Time()}")
l.append(f"Current temperature_2m {current_temperature_2m}")
l.append(f"Current relative_humidity_2m {current_relative_humidity_2m}")
l.append(f"Current apparent_temperature {current_apparent_temperature}")
l.append(f"Current is_day {current_is_day}")
l.append(f"Current precipitation {current_precipitation}")
l.append(f"Current rain {current_rain}")
l.append(f"Current showers {current_showers}")
l.append(f"Current snowfall {current_snowfall}")
l.append(f"Current weather_code {current_weather_code}")
l.append(f"Current cloud_cover {current_cloud_cover}")
l.append(f"Current pressure_msl {current_pressure_msl}")
l.append(f"Current surface_pressure {current_surface_pressure}")
l.append(f"Current wind_speed_10m {current_wind_speed_10m}")
l.append(f"Current wind_direction_10m {current_wind_direction_10m}")
# l.append(f"Current wind_gusts_10m {current_wind_gusts_}")
print(l)



# # Process hourly data. The order of variables needs to be the same as requested.
# hourly = response.Hourly()
# hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
# hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
# hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
# hourly_rain = hourly.Variables(3).ValuesAsNumpy()
# hourly_weather_code = hourly.Variables(4).ValuesAsNumpy()
# hourly_wind_speed_10m = hourly.Variables(5).ValuesAsNumpy()
# hourly_soil_temperature_6cm = hourly.Variables(6).ValuesAsNumpy()

# hourly_data = {"date": pd.date_range(
# 	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
# 	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
# 	freq = pd.Timedelta(seconds = hourly.Interval()),
# 	inclusive = "left"
# )}
# hourly_data["temperature_2m"] = hourly_temperature_2m
# hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
# hourly_data["precipitation"] = hourly_precipitation
# hourly_data["rain"] = hourly_rain
# hourly_data["weather_code"] = hourly_weather_code
# hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
# hourly_data["soil_temperature_6cm"] = hourly_soil_temperature_6cm

# hourly_dataframe = pd.DataFrame(data = hourly_data)
# print(hourly_dataframe)


@app.route('/')
def index():
    return render_template('index.html', a = l)






# @app.route("/search?term", methods = "GET")
@app.route('/search/<search_term>')
def search(search_term):
  # Get the search term from the query parameter
  search_term = request.args.get("term")
  location = geolocator.geocode(search_term)
  return_val = (location.longitude, location.latitude)

  # You can return data in various formats (JSON, GeoJSON, etc.) based on your needs
  return return_val

if __name__ == '__main__':
    app.run(debug=False)
