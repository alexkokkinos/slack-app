import requests
import os
import logging

logging.basicConfig(level=logging.DEBUG)

weather_api_key = os.environ.get("WEATHERAPI_KEY")
weatherurl = "https://api.weatherapi.com/v1/forecast.json"
default_userprefs = {
    "ideal_temp": 72,
    "units": "f",
    "location": "90210"
  }

def get_weather(location):
  """
  Retrieves hourly weather conditions from WeatherAPI.com

  Arguments:
    location -- A string representing your location. Weather API can handle a lot of things like city name, postal code, or coordinates
  """
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
  """
  Uses the get_weather function to retrieve the weather conditions but parse out the hourly forecast and only return the relevant data for the rest of the day

  Arguments:
    location -- A string representing your location. Weather API can handle a lot of things like city name, postal code, or coordinates
  """
  weather_info = get_weather(location)
  hours = weather_info["forecast"]["forecastday"][0]["hour"]
  remaining_hours = []
  for hour in hours:
    if hour["time_epoch"] >= weather_info["location"]["localtime_epoch"]:
      remaining_hours.append(hour)
  logging.debug(f"Total forecast hours: %i", (len(hours)))
  logging.debug(f"Remaining hours: %i", (len(remaining_hours)))
  return {
    "hour": remaining_hours,
    "location": weather_info["location"],
    "current": weather_info["current"]
  }


def get_weather_score(hour, userprefs=default_userprefs):
  """
  Inspects an hour's data and returns a score based on its weather conditions.
  The score starts from a baseline of 0 and decreases from there (yes, all scores are negative)
  Points are deducted for wind, rain, and temperature difference from the ideal
  """
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

def check_key_value(dict, key):
  """
  Utility function that ensures that the desired key is present

  Arguments:
    dict -- input dictionary
    key -- desired key
  """
  if key in dict.keys():
    return bool(dict[key])
  return False

def safe_user_prefs_defaults(user_prefs):
  """
  Utility function that ensures that the provided user preferences are safe, falls back to sensible defaults

  Arguments:
    user_prefs -- User preferences as a dictionary
  """
  return {
    "location": '90210' if not check_key_value(user_prefs, 'location') else user_prefs['location'],
    "units": 'f' if not check_key_value(user_prefs, 'units') else user_prefs['units'],
    "ideal_temp": 72 if not check_key_value(user_prefs, 'ideal_temp') else user_prefs['ideal_temp']
  }

def get_best_walk(prefs):
  """
  Wrapper function that retrieves the best walk based on user preferences

  Arguments:
    prefs -- User preferences as a dictionary
  """
  user_prefs = safe_user_prefs_defaults(prefs)
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
