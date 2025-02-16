from dotenv import load_dotenv
import os
from flask import Flask, request, redirect, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import requests
import logging

load_dotenv()

flask_app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.environ.get("SLACK_REDIRECT_URI")

slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
handler = SlackRequestHandler(slack_app)

HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

message_history = {}

# Function to call Hugging Face API
def get_huggingface_response(messages):
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    user_message = messages[-1]["content"]

    payload = {"inputs": user_message}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise HTTP errors if any
        return response.json()[0]["generated_text"]  # Extract response text
    except requests.exceptions.HTTPError as e:
        logging.error(f"Hugging Face API Error: {e.response.status_code} - {e.response.text}")
        return f"⚠️ API Error: {e.response.status_code} - {e.response.text} ⚠️"
    except requests.exceptions.RequestException as e:
        logging.error(f"Hugging Face API Error: {e}")
        return "⚠️ Error generating response. Please try again later. ⚠️"

# Slack event listener
@slack_app.event("app_mention")
def handle_mention(event, say):
    try:
        logging.info(f"Received event: {event}")

        user_message = event.get("text", "")
        thread_ts = event.get("thread_ts", event["ts"])  # Use thread timestamp if available

        if not user_message:
            logging.error("No message text found in event!")
            say(text="Sorry, I couldn't understand your message.", thread_ts=thread_ts)
            return

        # Initialize message history for the thread if it doesn't exist
        if thread_ts not in message_history:
            message_history[thread_ts] = []

        message_history[thread_ts].append({"role": "user", "content": user_message})

        # Prepare context for Hugging Face API (last 5 messages)
        context = message_history[thread_ts][-5:]

        # Get AI response from Hugging Face
        bot_response = get_huggingface_response(context)

        # Add bot response to history
        message_history[thread_ts].append({"role": "assistant", "content": bot_response})

        # Reply in Slack
        say(text=bot_response, thread_ts=thread_ts)

    except Exception as e:
        logging.error(f"Error in handle_mention: {e}", exc_info=True)
        say(text="Sorry, I encountered an error. Please try again later.", thread_ts=thread_ts)

# OAuth Route: Handles the Slack installation process
@flask_app.route("/slack/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Error: Missing 'code' parameter", 400

    # Exchange code for access token
    response = requests.post("https://slack.com/api/oauth.v2.access", data={
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri": SLACK_REDIRECT_URI
    })

    data = response.json()
    if not data.get("ok"):
        return f"Error: {data.get('error')}", 400

    return "✅ Bot installed successfully! You can now mention @YourBotName in Slack.", 200

# Flask route for Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
