from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app
flask_app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Slack app setup
slack_app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
handler = SlackRequestHandler(slack_app)

# Together AI API setup
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"  # Replace with the actual Together AI API URL

# In-memory storage for message history
message_history = {}

# Slack event listener
@slack_app.event("app_mention")
def handle_mention(event, say):
    try:
        user_message = event["text"]
        user_id = event["user"]
        channel_id = event["channel"]
        thread_ts = event.get("thread_ts", event["ts"])  # Use thread timestamp if available

        # Initialize message history for the thread if it doesn't exist
        if thread_ts not in message_history:
            message_history[thread_ts] = []

        # Add user message to history
        message_history[thread_ts].append({"role": "user", "content": user_message})

        # Prepare context for Together AI (last 5 messages)
        context = message_history[thread_ts][-5:]
        context.append({"role": "user", "content": user_message})

        # Call Together AI API
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "together-model-name",  # Replace with the actual model name
            "messages": context
        }
        response = requests.post(TOGETHER_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the response
        bot_response = response.json()["choices"][0]["message"]["content"]

        # Add bot response to history
        message_history[thread_ts].append({"role": "assistant", "content": bot_response})

        # Reply in Slack
        say(text=bot_response, thread_ts=thread_ts)

    except requests.exceptions.RequestException as e:
        logging.error(f"Together AI API error: {e}")
        say(text="Sorry, I encountered an issue with the AI service. Please try again later.", thread_ts=thread_ts)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        say(text="Sorry, I encountered an unexpected error. Please try again later.", thread_ts=thread_ts)

# Flask route for Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # Parse the request body
    data = request.get_json()

    # Check for Slack's challenge request
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Handle other events
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
