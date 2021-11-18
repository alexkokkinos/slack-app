import requests
import os

weather = os.environ.get("WEATHERAPI_KEY")
weatherurl = "https://api.weatherapi.com/v1/forecast.json"

def get_weather(zipcode):
  response = requests.get(
    url=weatherurl,
    params={'q': zipcode}
  )
  if response:
    print(response.json())

get_weather('60657')

# 629410947305-3ebltr175e1hh3gcariimffs9s2dl0k2.apps.googleusercontent.com