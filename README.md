# Walk Time Slack App

This Slack application suggests the best time to go outside and take a walk!
With many of us working from home, we're often sitting inside on Zoom calls.
This Slack application hopes to get people moving and enjoying the outdoors while respecting their busy schedule!

The walk score is based on user preferences set in the Home tab of the app.

Once set, you can run `/walktime` to get your personalized walk time suggestion!

The walkability score is based on the "feels-like" temperature, wind, and rain conditions.
Only the remainder of the current day's hourly forecast is considered in generating this walk time suggestion.

In the next development phase, this application will interface with a calendar API such as Google Calendar to fit your walk in to your schedule.
It would automatically notify you of your day's walking time(s).

# Local Development

Local development consists of a PostgreSQL database, the Bolt development server, and ngrok.

## Database setup

You'll need a PostgreSQL database with the following setup (note that these create queries were gathered from pgadmin):

```sql
CREATE ROLE walk WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  CREATEDB
  NOCREATEROLE
  NOREPLICATION
  PASSWORD '<password>';
```

```sql
CREATE SCHEMA IF NOT EXISTS userprefs
    AUTHORIZATION walk;
```

```sql
CREATE TABLE IF NOT EXISTS userprefs.userprefs
(
    user_and_team_id text COLLATE pg_catalog."default" NOT NULL,
    user_id text COLLATE pg_catalog."default",
    team_id text COLLATE pg_catalog."default",
    location text COLLATE pg_catalog."default",
    units text COLLATE pg_catalog."default",
    ideal_temp integer,
    CONSTRAINT userprefs_pkey PRIMARY KEY (user_and_team_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS userprefs.userprefs
    OWNER to walk;
```

## Environment Variables

I created a `.gitignore`d shell script in this repository to set my local environment variables.

Since I use the Fish shell, I used these `set -x VAR VALUE` commands (instead of `export VAR=value`):

```shell
set -x WEATHERAPI_KEY <key>
set -x SLACK_SIGNING_SECRET <secret>
set -x SLACK_BOT_TOKEN <token>

# Postgres Setup
set -x DBNAME walk
set -x DBUSER walk
set -x DBHOST localhost
set -x DBPORT 5432
set -x DBPASSWORD <password>
```

Run the resulting script before you attempt local development.

## Starting the app

```shell
brew install ngrok
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python app.py
# In a separate terminal...
ngrok http 3000
```
## Setting up api.slack.com

The following app settings in api.slack.com need have endpoints pointed to the temporary ngrok address

* Interactivity and Shortcuts
* Slash Commands
* Event Subscriptions

e.g. `https://<temporary-ngrok-address>.ngrok.io/slack/events`
