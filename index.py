from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
from flask import Flask, render_template, request
import json
from textblob import TextBlob
import time
import threading

# Monkey patch for compatibility
if not hasattr(time, 'clock'):
    time.clock = time.time

app = Flask(__name__)

# Initialize the ChatBot with SQL storage
bot = ChatBot("chatbot", 
              storage_adapter='chatterbot.storage.SQLStorageAdapter',
              database_uri='sqlite:///database.db',
              read_only=False,
              logic_adapters=[
                  {
                      "import_path": "chatterbot.logic.BestMatch",
                      "default_response": "I'm not sure about that, but I'm here for you! Want to talk about something else?",
                      "maximum_similarity_threshold": 0.75
                  },
                  {
                      "import_path": "chatterbot.logic.MathematicalEvaluation"
                  }
              ])

# Load training data from an external file
def load_training_data():
    try:
        with open("training_data.json", "r") as file:
            return json.load(file)
    except:
        return []

# Additional friendly training data based on social media conversations
friendly_chat = [
    "hello", "Hey there! How's your day going? 😊",
    "how are you", "I'm just a bot, but I'm feeling great! How about you?",
    "what's up", "Not much, just chilling in cyberspace! What about you?",
    "tell me a joke", "Sure! Why don't skeletons fight each other? Because they don't have the guts! 😂",
    "who's your favorite person", "I like everyone equally! But you seem pretty cool! 😎",
    "bye", "Goodbye! Hope to chat again soon! Take care!"
]

# Train chatbot with external dataset
training_data = load_training_data() + friendly_chat
if training_data:
    list_trainer = ListTrainer(bot)
    list_trainer.train(training_data)

# Function to analyze emotion from user input
def analyze_emotion(text):
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment > 0.5:
        return "You seem happy! That's awesome! 😊"
    elif sentiment < -0.5:
        return "I'm here for you. Want to talk about it? 💙"
    return None

# Thread lock for thread safety
chatbot_lock = threading.Lock()

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/get")
def get_chatbot_response():
    userText = request.args.get('userMessage')
    if userText:
        with chatbot_lock:
            emotion_response = analyze_emotion(userText)
            if emotion_response:
                return emotion_response
            response = bot.get_response(userText)
            if response.confidence < 0.5:
                return "Hmm, I might not know that yet, but I'm eager to learn! Tell me more!"
            return str(response)
    return "Oops! I didn't quite get that. Could you say it differently?"

if __name__ == "__main__":
    app.run(debug=True)
