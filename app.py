import os
from slack_bolt import App
import requests
# import weather
import sqlite3

app = App(
  token=os.environ.get("SLACK_BOT_TOKEN"),
  signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

import logging

logging.basicConfig(level=logging.DEBUG)

weather = os.environ.get("WEATHERAPI_KEY")
weatherurl = "https://api.weatherapi.com/v1/forecast.json"

def get_weather(zipcode):
  response = requests.get(
    url=weatherurl,
    params={'q': zipcode}
  )
  if response:
    print(response.json())

# get_weather('60657')

# 629410947305-3ebltr175e1hh3gcariimffs9s2dl0k2.apps.googleusercontent.com

def get_user_prefs(user_id, team_id):
  user_and_team_id = user_id + team_id
  con = sqlite3.connect('db.db')
  cursor = con.execute("SELECT user_and_team_id, postalcode from userprefs where user_and_team_id = :user_and_team_id", {"user_and_team_id": user_and_team_id})
  results_list = cursor.fetchall()
  if len(results_list == 0):
    cursor = con.execute("INSERT INTO userprefs (user_and_team_id, user_id, team_id) VALUES (:user_and_team_id, :user_id, :team_id)", 
      {
        "user_and_team_id": user_and_team_id,
        "user_id": user_id,
        "team_id": team_id
      })
    return '0'
  else:
    if len(results_list[0][1]):
      return results_list[0][1]
  return 0

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=event["user"],
      # the view object that appears in the app home
      view={
        "type": "home",
        "callback_id": "home_view",

        # body of the view
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Weather App Settings*"
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "Enter your ZIP code to set your default weather location!"
            }
          },
          {
            "type": "input",
            "element": {
              "type": "plain_text_input",
              "action_id": "zip_code_submit"
            },
            "label": {
              "type": "plain_text",
              "text": "Zip Code",
              "emoji": False
            },
            "dispatch_action": True,
            "block_id": "zip_code_block"
          }
        ]
      }
    )
  
  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

def get_desired_action(actions, action_id):
  for action in actions:
    if action["action_id"] == action_id:
      return action

def update_user_info(user_and_team_id, user_id, team_id, postalcode):
  conn = sqlite3.connect('db.db')
  conn.execute("""INSERT INTO userprefs (user_and_team_id, user_id, team_id, postalcode)
                          VALUES (:user_and_team_id, :user_id, :team_id, :postalcode)
                          ON CONFLICT(user_and_team_id) DO UPDATE SET postalcode=:postalcode
               """,
              {
                "user_and_team_id": user_and_team_id,
                "user_id": user_id,
                "team_id": team_id,
                "postalcode": postalcode
              })
  conn.commit()
  

@app.action("zip_code_submit")
def handle_actions(ack, body, logger):
    ack()
    
    user_and_team_id = body["user"]["id"] + "_" + body["user"]["team_id"]
    user_id = body["user"]["id"]
    team_id = body["user"]["team_id"]
    postalcode = get_desired_action(action_id="zip_code_submit", actions=body["actions"])["value"]

    update_user_info(
      user_and_team_id = user_and_team_id,
      user_id = user_id,
      team_id = team_id,
      postalcode = postalcode
    )

if __name__ == "__main__":
  app.start(port=int(os.environ.get("PORT", 3000)))