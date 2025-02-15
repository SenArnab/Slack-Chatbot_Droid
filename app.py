from dotenv import load_dotenv
import os
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import openai
from datetime import datetime
import logging

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
flask_app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Slack app setup
slack_app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
handler = SlackRequestHandler(slack_app)

# OpenAI setup
openai.api_key = os.environ.get("OPENAI_API_KEY")

# In-memory storage for message history (replace with a database in production)
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

        # Prepare context for OpenAI (last 5 messages)
        context = message_history[thread_ts][-5:]
        context.append({"role": "user", "content": user_message})

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=context
        )

        bot_response = response["choices"][0]["message"]["content"]

        # Add bot response to history
        message_history[thread_ts].append({"role": "assistant", "content": bot_response})

        # Reply in Slack
        say(text=bot_response, thread_ts=thread_ts)

    except Exception as e:
        logging.error(f"Error handling mention: {e}")
        say(text="Sorry, I encountered an error. Please try again later.", thread_ts=thread_ts)

# Flask route for Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)