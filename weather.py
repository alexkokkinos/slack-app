import requests
import os
import logging
import time

logging.basicConfig(level=logging.DEBUG)

weather_api_key = os.environ.get("WEATHERAPI_KEY")
weatherurl = "https://api.weatherapi.com/v1/forecast.json"

def get_weather(location):
  response = requests.get(
    url=weatherurl,
    params={
      'key': weather_api_key,
      'q': location,
      'alerts': "no"
    }
  )
  if response.status_code == 200:
    return response.json()
  else:
    raise Exception("Undesired response code: %i \n %s" % (response.status_code, response.text))

def get_hourly_conditions(location):
  weather_info = get_weather(location)
  hours = weather_info["forecast"]["forecastday"][0]["hour"]
  remaining_hours = []
  for hour in hours:
    if hour["time_epoch"] >= time.time():
      remaining_hours.append(hour)
  logging.info(f"Total forecast hours: %i", (len(hours)))
  logging.info(f"Remaining hours: %i", (len(remaining_hours)))
  return remaining_hours

def get_weather_score(hour):
  # placeholder, move to parameters
  userprefs = {
    "ideal_temp": 72,
    "units": "f"
  }
  score = 0
  if hour["will_it_rain"] or hour["will_it_snow"] == 1:
    score-=100
  
  ### Temperature Adjustments
  temp_adjustment = userprefs["ideal_temp"] - hour["feelslike_" + userprefs["units"]]
  
  # Fahrenheit
  if userprefs["units"] == "f":
    multiplier = 1
    # Temperature is under 50 degrees
    if hour["feelslike_f"] < 50:
      multiplier = 2
    # Temperature is over 80 degrees
    if hour["feelslike_f"] > 80:
      multiplier = 2
    score -= abs(multiplier * (userprefs["ideal_temp"] - hour["feelslike_f"]))
  # Celsius
  else:
    multiplier = 1
    # Temperature is under 10 degrees
    if hour["feelslike_c"] < 10:
      multiplier = 2
    # Temperature is over 27 degrees
    if hour["feelslike_c"] > 27:
      multiplier = 2
    score -= abs(multiplier(userprefs["ideal_temp"] - hour["feelslike_c"]))

  ### End Temperature Adjustments

  # This wind speed scale is crudely based on the Beaufort wind force scale
  # It seems to be, essentially, logarithmic – 30MPH is more than twice as "bad" as 15MPH
  # https://mountain-hiking.com/hike-safe-wind/
  if hour["wind_mph"] > 20:
    score-=10
  if hour["wind_mph"] > 25:
    score-=50
  if hour["wind_mph"] > 30:
    score-=50
  if hour["wind_mph"] > 33:
    score-=100

  return score

hours = get_hourly_conditions("Barcelona, Aruba")
for hour in hours:
  print(hour["time"] + " – " + str(hour["feelslike_f"]) + "°F – Wind: " + str(hour["wind_mph"]) + "MPH – " + "Rain: " + str(hour["will_it_rain"]) + " - Score: " + str(get_weather_score(hour)))
