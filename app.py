import os
from posix import environ
from slack_bolt import App, Respond
import weather
import logging
from pgdatabase import PGDatabase

app = App(
  token=os.environ.get("SLACK_BOT_TOKEN"),
  signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Log level should not be hardcoded
logging.basicConfig(level=logging.ERROR)

def get_user_prefs(user_and_team_id):
  """
  Retrieves the user preferences from the database, formatted as a dictionary

  Arguments:
    user_and_team_id -- The Slack user ID and team ID separated by an underscore
  """

  db = PGDatabase()
  db.query("SELECT location, ideal_temp, units from userprefs.userprefs where user_and_team_id = %s;", (user_and_team_id,))
  result = db.cursor.fetchone()
  db.close()
  if result is not None:
    logging.debug(result)
    return {
      "location": result[0],
      "ideal_temp": result[1],
      "units": result[2]
    }
  else:
    return {
      "location": '',
      "ideal_temp": int(),
      "units": ''
    }

def home_tab_content(user_prefs, update_status):
  """
  Returns the home tab view content based on user preferences and whether the last action was successful

  Arguments:
    user_prefs -- user preferences (dictionary)
    update_status -- update status used to relay success/failure
  """

  view = {
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
              "initial_value": user_prefs["location"] or '',
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
            "block_id": "location_block"
          },
          {
            "type": "input",
            "element": {
              "type": "plain_text_input",
              "action_id": "ideal_temperature_submit",
              "initial_value": str(user_prefs["ideal_temp"]) if user_prefs["ideal_temp"] else '',
              "placeholder": {
                "type": "plain_text",
                "text": "00"
              }
            },
            "label": {
              "type": "plain_text",
              "text": "Your ideal walking temperature",
              "emoji": False
            },
            "block_id": "ideal_temp_block"
          },
          {
            "type": "input",
            "element": {
              "type": "static_select",
              "placeholder": {
                "type": "plain_text",
                "text": "Temperature Units",
                "emoji": True
              },
              "options": [
                {
                  "text": {
                    "type": "plain_text",
                    "text": "Fahrenheit (°F)",
                    "emoji": True
                  },
                  "value": "f"
                },
                {
                  "text": {
                    "type": "plain_text",
                    "text": "Celsius (°C)",
                    "emoji": True
                  },
                  "value": "c"
                }
              ],
              "action_id": "units_submit",
              "initial_option": {
                "value": user_prefs["units"] if user_prefs["units"] else "f",
                "text": {
                  "type": "plain_text",
                  "text": "Celsius (°C)" if user_prefs["units"] == "c" else "Fahrenheit (°F)",
                  "emoji": True
                }
              }
            },
            "label": {
              "type": "plain_text",
              "text": "Temperature Units",
              "emoji": True
            },
            "block_id": "units_block"
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Save Preferences",
                  "emoji": True
              },
              "value": "save_preferences",
              "action_id": "save_preferences",
              "style": "primary"
            }
          ],
            "block_id": "save_preferences"
        }
      ]
    }

  if update_status == "successful_update":
    view["blocks"].append({
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": ":white_check_mark: Preferences updated successfully!",
				"emoji": True
		}
	})
  if update_status == "error_update":
    view["blocks"].append({
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": ":exclamation: Error updating preferences! Reload the Home tab and try again.",
				"emoji": True
		}
  })
  if update_status == "error_update_ideal_temp":
    view["blocks"].append({
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": ":exclamation: Error updating preferences! Ideal Temperature must be an integer (e.g., 72, NOT 72.5 or 72F)",
				"emoji": True
		}
	})

  return view

@app.event("app_home_opened")
def render_home_tab(client, event, logger):
  """
  Event handling for when the user opens the home tab. This function retrieves user preferences and attempts to publish the home tab

  Arguments:
    client -- Slack Bolt client
    event -- Slack Bolt event
    logger -- Slack Bolt logger
  """

  user_and_team_id = f"{event['user']}_{event['view']['team_id']}"
  user_prefs = get_user_prefs(user_and_team_id)
  logger.debug(user_prefs)
  try:
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=event["user"],
      # the view object that appears in the app home
      view=home_tab_content(user_prefs=user_prefs, update_status=None)
    )
  
  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

def get_desired_action(actions, action_id):
  for action in actions:
    if action["action_id"] == action_id:
      return action

def update_user_info(user_and_team_id, user_id, team_id, location, units, ideal_temp):
  db = PGDatabase()
  db.query("""INSERT INTO userprefs.userprefs (user_and_team_id, user_id, team_id, location, ideal_temp, units)
                          VALUES (%s, %s, %s, %s, %s, %s)
                          ON CONFLICT (user_and_team_id) DO UPDATE SET location = %s, ideal_temp = %s, units = %s
               """,
              (
                # VALUES
                user_and_team_id,
                user_id,
                team_id,
                location,
                ideal_temp,
                units,
                # DO UPDATE SET
                location,
                ideal_temp,
                units
              ),)
  db.close()

@app.action("save_preferences")
def handle_actions(ack, body, client, logger):
    """
    Handles the updates that need to occur when the user presses "Save Preferences" in the Home tab

    Arguments:
      ack -- Slack Bolt acknowledgement function
      body -- Slack Bolt body
      client -- Slack Bolt client
      logger -- Slack Bolt logger
    """
    ack()
    logger.debug(body)
    user_and_team_id = f"{body['user']['id']}_{body['user']['team_id']}"
    user_id = body["user"]["id"]
    team_id = body["user"]["team_id"]

    # Information that the user put into the Home tab. We read the view state.
    location = body["view"]["state"]["values"]["location_block"]["location_submit"]["value"]
    # Check if the user selected anything
    if body["view"]["state"]["values"]["units_block"]["units_submit"]["selected_option"]:
      units = body["view"]["state"]["values"]["units_block"]["units_submit"]["selected_option"]["value"]
    else:
      units = None
    ideal_temp = body["view"]["state"]["values"]["ideal_temp_block"]["ideal_temperature_submit"]["value"]
    update_status = "successful_update"

    # If the ideal temperature isn't an integer, we throw it out and let the user know
    # TODO: Accept floating point numbers 
    if not ideal_temp.isdigit():
      ideal_temp = None
      update_status = "error_update_ideal_temp"

    # Try to update the user preferences in the database
    try:
      update_user_info(
        user_and_team_id = user_and_team_id,
        user_id = user_id,
        team_id = team_id,
        location = location,
        ideal_temp = ideal_temp,
        units = units
      )
    
      # The no-error view
      client.views_publish(
        user_id=user_id,
        view=home_tab_content(
          user_prefs={
            "ideal_temp": ideal_temp,
            "units": units,
            "location": location
          }, 
        update_status=update_status))
    except Exception as e:
      # We would publish this alternative view with an error message if there's some kind of error.
      update_status = "error_update"
      client.views_publish(
      user_id=user_id,
      view=home_tab_content(
        user_prefs={
          "ideal_temp": ideal_temp,
          "units": units,
          "location": location
        }, 
        update_status=update_status))

@app.command("/walktime")
def handle_walktime(ack, body, logger, respond: Respond):
  """
  Handles the /walktime slash command

  Arguments:
    ack: Slack Bolt acknowledge function
    body: Slack Bolt body
    logger: Slack Bolt logger
    respond: Slack Bolt response
  """
  ack()
  logger.debug(body)
  user_and_team_id = f"{body['user_id']}_{body['team_id']}"

  # Try to retrieve the user preferences from the database
  try:
    user_prefs = get_user_prefs(user_and_team_id)
    logger.debug(user_prefs)
  except Exception as e:
    logger.error(f"Error retrieving user preferences: {e}")
  
  # Try to retrieve the best walk base on user preferences
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

  # Shorthand for disgusting ternary operator usage that we'll use later
  c = user_prefs['units'] == "c" 

  response_intro_markdown = f"""
  The best time to walk in *{best_walk['location']['name']}* is *<!date^{best_walk['best_walk_hour']['time_epoch']}^{{time}}|{best_walk['best_walk_hour']['time']} (local time)>*:
  \n\n
  """

  # The output below changes based on whether the user's units are set to C or F. /walktime arbitrarily defaults to Fahrenheit
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

# Development server
if __name__ == "__main__":
  app.start(port=int(os.environ.get("PORT", 3000)))

# Production Heroku Deployment
from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)
