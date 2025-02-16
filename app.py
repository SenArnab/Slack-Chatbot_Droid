from dotenv import load_dotenv
import os
from flask import Flask, request, redirect, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
import requests
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
flask_app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Slack OAuth credentials
SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_REDIRECT_URI = os.environ.get("SLACK_REDIRECT_URI")

# Hugging Face API Key
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

# Dictionary to store installed workspace tokens (Replace with a database in production)
installed_bots = {}

# OAuth Settings
oauth_settings = OAuthSettings(
    client_id=SLACK_CLIENT_ID,
    client_secret=SLACK_CLIENT_SECRET,
    scopes=["app_mentions:read", "chat:write", "channels:history"],
    redirect_uri=SLACK_REDIRECT_URI,
)

# Initialize Slack App with OAuth
slack_app = App(
    signing_secret=SLACK_SIGNING_SECRET,
    oauth_settings=oauth_settings
)

# Flask Slack handler
handler = SlackRequestHandler(slack_app)

# Store installed bot tokens
@slack_app.event("tokens_revoked")
def handle_token_revocation(event):
    team_id = event["team_id"]
    if team_id in installed_bots:
        del installed_bots[team_id]

@slack_app.event("app_home_opened")
def handle_app_home_opened(event, client):
    team_id = event["team_id"]
    if team_id not in installed_bots:
        client.chat_postMessage(channel=event["user"], text="Please install the app first.")

# OAuth Callback Route
@flask_app.route("/slack/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Error: Missing 'code' parameter", 400

    # Exchange code for token
    response = requests.post("https://slack.com/api/oauth.v2.access", data={
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri": SLACK_REDIRECT_URI
    })

    data = response.json()
    if not data.get("ok"):
        return f"Error: {data.get('error')}", 400

    # Store bot token for the workspace
    installed_bots[data["team"]["id"]] = data["access_token"]

    return "✅ Bot installed successfully! You can now mention @YourBotName in Slack.", 200

# Function to call Hugging Face API
def get_huggingface_response(user_message):
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": user_message}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()[0]["generated_text"]
    except requests.exceptions.HTTPError as e:
        logging.error(f"Hugging Face API Error: {e.response.status_code} - {e.response.text}")
        return f"⚠️ API Error: {e.response.status_code} - {e.response.text} ⚠️"
    except requests.exceptions.RequestException as e:
        logging.error(f"Hugging Face API Error: {e}")
        return "⚠️ Error generating response. Please try again later. ⚠️"

# Slack event listener for @mentions
@slack_app.event("app_mention")
def handle_mention(event, say):
    try:
        logging.info(f"Received event: {event}")

        user_message = event.get("text", "").replace(f"<@{event['user']}>", "").strip()
        thread_ts = event.get("thread_ts", event["ts"])  # Use thread timestamp if available

        if not user_message:
            logging.error("No message text found in event!")
            say(text="Sorry, I couldn't understand your message.", thread_ts=thread_ts)
            return

        # Get AI response from Hugging Face
        bot_response = get_huggingface_response(user_message)

        # Reply in Slack
        say(text=bot_response, thread_ts=thread_ts)

    except Exception as e:
        logging.error(f"Error in handle_mention: {e}", exc_info=True)
        say(text="Sorry, I encountered an error. Please try again later.", thread_ts=thread_ts)

# Flask route for Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
