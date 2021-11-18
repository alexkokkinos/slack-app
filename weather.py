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
    if hour["time_epoch"] <= time.time():
      remaining_hours.append(hour)
  logging.info(f"Total forecast hours: %i", (len(hours)))
  logging.info(f"Remaining hours: %i", (len(remaining_hours)))
  return remaining_hours


get_hourly_conditions("60657")