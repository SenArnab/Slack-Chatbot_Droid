from dotenv import load_dotenv
import os
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import requests
import logging

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
flask_app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Slack app setup
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
handler = SlackRequestHandler(slack_app)

# DeepSeek API Key
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# In-memory storage for message history (replace with a database in production)
message_history = {}

# Function to call DeepSeek API
def get_deepseek_response(messages):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",  # Or use "deepseek-coder" for coding tasks
        "messages": messages
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logging.error(f"DeepSeek API Error: {e}")
        return "⚠️ Error generating response. Please try again later. ⚠️"

# Slack event listener
@slack_app.event("app_mention")
def handle_mention(event, say):
    try:
        logging.info(f"Received event: {event}")

        user_message = event.get("text", "")
        user_id = event.get("user", "Unknown")
        channel_id = event.get("channel", "Unknown")
        thread_ts = event.get("thread_ts", event["ts"])  # Use thread timestamp if available

        if not user_message:
            logging.error("No message text found in event!")
            say(text="Sorry, I couldn't understand your message.", thread_ts=thread_ts)
            return

        # Initialize message history for the thread if it doesn't exist
        if thread_ts not in message_history:
            message_history[thread_ts] = []

        message_history[thread_ts].append({"role": "user", "content": user_message})

        # Prepare context for DeepSeek API (last 5 messages)
        context = message_history[thread_ts][-5:]

        # Get AI response from DeepSeek
        bot_response = get_deepseek_response(context)

        # Add bot response to history
        message_history[thread_ts].append({"role": "assistant", "content": bot_response})

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
