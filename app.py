"""
Copyright (c) 2020 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import json
import logging
import os

import requests
from flask import Flask, jsonify, render_template, request

from bot import ChatBot
from conversion import Converter

# Create flask instance
app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

# Create an instance of the chat bot
bot = ChatBot()


@app.route('/')
def index():
    gif = "https://66.media.tumblr.com/0a14eda38c31356d1e164009ef1edf2f/tumblr_mjpnd23P7x1qhbw13o1_400.gifv"
    return render_template('index.html', gif_url=gif)


@app.route('/compare', methods=["POST"])
def compare():
    return bot.compare(request.json)


@app.route('/events', methods=['POST'])
def message_received():
    # Get the POST data sent from Webex Teams
    return bot.receive_message(request.json)


@app.route('/actions', methods=['POST'])
def attachment_action_received():
    return bot.execute_action(request.json)


# run Flask app
if __name__ == "__main__":
    # Check for correct environment variables
    if (os.environ.get("WEBEX_TEAMS_ACCESS_TOKEN") == ''):
        print("WEBEX_TEAMS_ACCESS_TOKEN not found in environment variables")
        exit()
    elif (os.getenv('DIALOGFLOW_PROJECT_ID') == ''):
        print("DIALOGFLOW_PROJECT_ID not found in environment variables")
        exit()

    app.run("0.0.0.0", port=port)
