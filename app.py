import os
from slack_bolt import App, Respond
import requests
import weather
import sqlite3
import logging

app = App(
  token=os.environ.get("SLACK_BOT_TOKEN"),
  signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

logging.basicConfig(level=logging.DEBUG)

def get_user_prefs(user_and_team_id):
  con = sqlite3.connect('db.db')
  cursor = con.execute("SELECT location, ideal_temp, units from userprefs where user_and_team_id = :user_and_team_id", {"user_and_team_id": user_and_team_id})
  results_list = cursor.fetchall()
  if len(results_list) == 1:
    return {
      "location": results_list[0][0],
      "ideal_temp": results_list[0][1],
      "units": results_list[0][2]
    }
  else:
    return {
      "location": '',
      "ideal_temp": '',
      "units": 'F'
    }

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  user_and_team_id = f"{event['user']}_{event['view']['team_id']}"
  user_prefs = get_user_prefs(user_and_team_id)
  logger.info(user_prefs)
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
              "text": "Enter your location to set your default weather location!"
            }
          },
          {
            "type": "input",
            "element": {
              "type": "plain_text_input",
              "action_id": "location_submit",
              "initial_value": user_prefs["location"],
              "placeholder": {
                "type": "plain_text",
                "text": "examples: 90210 | Beverly Hills, CA | 34.0736,118.4004"
              }
            },
            "label": {
              "type": "plain_text",
              "text": "Location",
              "emoji": False
            },
            "dispatch_action": True,
            "block_id": "location_block"
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

def update_user_info(user_and_team_id, user_id, team_id, location):
  conn = sqlite3.connect('db.db')
  conn.execute("""INSERT INTO userprefs (user_and_team_id, user_id, team_id, location)
                          VALUES (:user_and_team_id, :user_id, :team_id, :location)
                          ON CONFLICT(user_and_team_id) DO UPDATE SET location=:location
               """,
              {
                "user_and_team_id": user_and_team_id,
                "user_id": user_id,
                "team_id": team_id,
                "location": location
              })
  conn.commit()

@app.action("location_submit")
def handle_actions(ack, body, logger):
    logger.debug(body)
    ack()
    user_and_team_id = f"{body['user']['id']}_{body['user']['team_id']}"
    user_id = body["user"]["id"]
    team_id = body["user"]["team_id"]
    location = get_desired_action(action_id="location_submit", actions=body["actions"])["value"]

    update_user_info(
      user_and_team_id = user_and_team_id,
      user_id = user_id,
      team_id = team_id,
      location = location
    )

@app.command("/walktime")
def handle_walktime(ack, body, logger, respond: Respond):
  ack()
  logger.info(body)
  user_and_team_id = f"{body['user_id']}_{body['team_id']}"

  try:
    user_prefs = get_user_prefs(user_and_team_id)
  except Exception as e:
    logger.error(f"Error retrieving user preferences: {e}")
  
  try:
    best_walk = weather.get_best_walk(user_prefs)
  except ValueError as e:
    respond(
      """
We were unable to find the best walk for today. 
This problem might occur if there are no more hours left in the day for the location specified.
Support for walking information beyond today's date may be added in the future!
      """)
    logger.error(e)

  # Shorthand for later disgusting ternary operator usage
  c = user_prefs['units'] == "c" 

  response_intro_markdown = f"""
  The best time to walk in *{best_walk['location']['name']}* is *<!date^{best_walk['best_walk_hour']['time_epoch']}^{{time}}|{best_walk['best_walk_hour']['time']} (local time)>*:
  \n\n
  """

  response_weather_markdown = f"""
*{best_walk['best_walk_hour']['condition']['text']}*
*{best_walk['best_walk_hour']['temp_c'] if c else best_walk['best_walk_hour']['temp_f']}{'°C' if c else '°F'}*
Feels like {best_walk['best_walk_hour']['feelslike_c'] if c else best_walk['best_walk_hour']['feelslike_f']}{'°C' if c else '°F'}, 
Chance of Rain: {best_walk['best_walk_hour']['chance_of_rain']}%
  """

  response_footnotes = f"""
Note: Walking time is shown in your current Slack timezone. This time will be offset by a time zone difference if your configured location is in a different time zone.
\n\n
Set your location and other preferences in the <slack://app?team={body['team_id']}&id={body['api_app_id']}&tab=home|Home tab of this App>.
  """

  try:
    respond(blocks=[
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": response_intro_markdown
			}
		},
    {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": response_weather_markdown
			},
			"accessory": {
				"type": "image",
				"image_url": f"https:{best_walk['best_walk_hour']['condition']['icon']}",
				"alt_text": "Current condition icon"
			}
		},
    {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": response_footnotes
			}
		}
	])
  except Exception as e:
    logger.error(f"Error responding to slash command: {e}")

if __name__ == "__main__":
  app.start(port=int(os.environ.get("PORT", 3000)))
