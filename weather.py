import requests
import os
import logging
# import time

logging.basicConfig(level=logging.DEBUG)

weather_api_key = os.environ.get("WEATHERAPI_KEY")
weatherurl = "https://api.weatherapi.com/v1/forecast.json"
default_userprefs = {
    "ideal_temp": 72,
    "units": "f",
    "location": "90210"
  }

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
    if hour["time_epoch"] >= weather_info["location"]["localtime_epoch"]:
      remaining_hours.append(hour)
  logging.info(f"Total forecast hours: %i", (len(hours)))
  logging.info(f"Remaining hours: %i", (len(remaining_hours)))
  return {
    "hour": remaining_hours,
    "location": weather_info["location"],
    "current": weather_info["current"]
  }


def get_weather_score(hour, userprefs=default_userprefs):
  score = 0

  ## Rain Adjustments
  score -= hour["chance_of_rain"]
  score -= hour["chance_of_snow"]
  
  ### Temperature Adjustments

  ## I use multipliers for more extreme temperatures.
  ## I will guess that, for most people, warmer temperature extremes are less bearable than colder ones
  ## because cold is more easily rectified by adding clothing
  # Fahrenheit
  if userprefs["units"] == "f":
    multiplier = 1
    # Temperature is colder than ideal - 20 degrees
    if hour["feelslike_f"] < userprefs["ideal_temp"] - 20:
      multiplier = 2
    # Temperature is warmer than ideal + 10 degrees
    if hour["feelslike_f"] > userprefs["ideal_temp"] + 10:
      multiplier = 2
    score -= abs(multiplier * (userprefs["ideal_temp"] - hour["feelslike_f"]))
  # Celsius
  else:
    multiplier = 1.8 # Adjust multiplier for Celsius to keep it consistent with Fahrenheit results
    # Temperature is colder than ideal - 7 degrees
    if hour["feelslike_c"] < userprefs["ideal_temp"] - 11.11:
      multiplier = 3.6
    # Temperature is over 27 degrees
    if hour["feelslike_c"] > userprefs["ideal_temp"] + 5.55:
      multiplier = 3.6
    score -= abs(multiplier * (userprefs["ideal_temp"] - hour["feelslike_c"]))

  ### End Temperature Adjustments

  ### Wind Speed Adjustments
  # This wind speed scale is crudely based on the Beaufort wind force scale
  # 30MPH is more than twice as "bad" as 15MPH, so we have scaling multipliers
  # https://mountain-hiking.com/hike-safe-wind/
  multiplier=0.25
  if hour["wind_mph"] > 10:
    multiplier=0.5
  if hour["wind_mph"] > 20:
    multiplier=1
  if hour["wind_mph"] > 25:
    multiplier=2
  if hour["wind_mph"] > 30:
    multiplier=5
  if hour["wind_mph"] > 33:
    multiplier=10
  score -= multiplier * hour["wind_mph"]

  ### End Wind Speed Adjustments

  return score

def get_best_walk(user_prefs=default_userprefs):
  conditions = get_hourly_conditions(user_prefs["location"])
  for hour in conditions["hour"]:
    hour["weather_score"] = get_weather_score(hour, user_prefs)
    logging.debug(f"{hour['time']} – {hour['feelslike_f']}°F – Wind: {hour['wind_mph']} MPH – Rain: {hour['will_it_rain']} - Chance of Rain: {hour['chance_of_rain']} - Score: {hour['weather_score']}")
  best_walk = max(conditions["hour"], key=lambda x:x["weather_score"])
  best_walk_info = {
    "best_walk_hour": best_walk,
    "location": conditions["location"],
    "current": conditions["current"]
  }
  return best_walk_info

# results = get_best_walk()
# logging.debug(results)
