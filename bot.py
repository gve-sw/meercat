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
from pprint import pprint

from flask import jsonify
from webexteamssdk import WebexTeamsAPI, Webhook
from webexteamssdk.exceptions import ApiError

import responses
import utils
from conversion import Converter
from editing import Editor


class ChatBot():
    def __init__(self):
        super().__init__()
        self.api = WebexTeamsAPI()
        self.me = self.api.people.me()

        # Create instance of the Converter model
        project_id = str(os.getenv('DIALOGFLOW_PROJECT_ID'))
        self.converter = Converter(project_id, "unique")
        self.editor = Editor()
        # Check if the token represents a bot
        me_resp = self.api.people.me()
        if me_resp.type != 'bot':
            print(
                'WEBEX_TEAMS_ACCESS_TOKEN does not belong to a bot...exiting')
            exit()

    def handle_command(self, person_id, command):
        # Trim the message to get the command type (e.g "/help something" => "help")
        command_type = command.strip().split(" ")[0][1:]
        try:
            parameters = command.strip().split(" ", 1)[1]
        # Will throw an error if no parameters are passed
        except IndexError:
            parameters = ""

        username = utils.person_id_to_username(self.api, person_id)

        # Do some things depending on the command
        if command_type == "help":
            if not self.editor.can_user_edit(username):
                return responses.RESPONSE_HELP_RESTRICTED
            else:
                return responses.RESPONSE_HELP
        elif command_type == "info":
            switch = self.editor.get_switch_by_id(parameters)
            if switch:
                return utils.Responses.generate_model_response(switch)
            else:
                return "Sorry, I couldn't find an equivalent switch for that."
        elif command_type == "list":
            if "switch" in parameters or parameters == "":
                switches = self.editor.list_all_switches(parameters)
                return utils.Responses.generate_switches_response(switches)
            elif "map" in parameters:
                mapping = self.editor.list_all_mapping(parameters)
                return utils.Responses.generate_mapping_response(mapping)
            elif "user" in parameters:
                users = self.editor.get_approved_users()
                return utils.Responses.generate_approved_users_response(
                    self.api, users)
            else:
                return responses.RESPONSE_NOT_IMPLEMENTED
        elif command_type == "edit":
            # Check if the user is allowed to edit
            if not self.editor.can_user_edit(username):
                return responses.RESPONSE_NO_PERMISSION
            switch = self.editor.get_switch_by_id(parameters)
            # Switch didn't exist
            if not switch:
                return f"Cannot find switch with key {parameters}."
            return utils.Responses.generate_edit_response(switch)
        elif command_type == "add-switch":
            # Check if the user is allowed to edit
            if not self.editor.can_user_edit(username):
                return responses.RESPONSE_NO_PERMISSION
            return utils.Responses.generate_add_response()
        elif command_type == "remove-switch":
            # Check if the user is allowed to edit
            if not self.editor.can_user_edit(username):
                return responses.RESPONSE_NO_PERMISSION
            return self.editor.remove_switch_by_id(parameters)
        elif command_type == "add-mapping":
            # Check if the user is allowed to edit
            if not self.editor.can_user_edit(username):
                return responses.RESPONSE_NO_PERMISSION
            return self.editor.add_mapping_by_id(parameters)
        elif command_type == "remove-mapping":
            # Check if the user is allowed to edit
            if not self.editor.can_user_edit(username):
                return responses.RESPONSE_NO_PERMISSION
            return self.editor.remove_mapping_by_id(parameters)
        elif command_type == "allow":
            return self.editor.allow_user_by_id(username, parameters)
        elif command_type == "disallow":
            return self.editor.disallow_user_by_id(username, parameters)
        elif command_type == "request":
            # Send a request message to all admins
            utils.Responses.generate_user_access_request(
                self.api, self.editor, person_id, username, parameters)
        elif command_type == "export":
            return responses.RESPONSE_NOT_IMPLEMENTED
        elif command_type == "import":
            return responses.RESPONSE_NOT_IMPLEMENTED
        else:
            return responses.RESPONSE_COMMAND_NOT_RECOGNISED

    def compare(self, json_data):
        data = json_data

        # We can do some magic on the session id as we stored it as a combo of room and person id
        session_id = data["session"].split('/')[-1].split(".")
        person_id = session_id[0]
        room_id = session_id[1]

        # The text to return and send back to the user
        # This will sometimes be overridden by DialogFlow
        fulfillment_text = ""

        fields = data["queryResult"]["parameters"]
        switch_entity = fields.get("Model", None)

        match_data = self.converter.find_equivalent_switch(fields)
        matched_switches = match_data.get("switches", None)
        switch_entity = match_data.get("matched_model", switch_entity)

        # Check if we found any switch matching the model
        if not matched_switches:
            # Couldn't find any switch matching the model
            if not match_data["matched"]:
                fulfillment_text = "Sorry, I couldn't find any switch matching that model number."
            # Found a switch but couldn't find an equivalent
            else:
                fulfillment_text = f"Sorry, I couldn't find an equivalent switch for that."
        # Multiple fixed chassis matches
        elif len(matched_switches) > 1 and not match_data[
                "modular"] and not match_data["matched"]:
            fulfillment_text = "**I've found multiple matches for that model - please be more specific.**\n\n"
            for switch in matched_switches:
                fulfillment_text += f"- {switch.model}\n"
            fulfillment_text = fulfillment_text[:-1]

        # Modular switch
        elif len(matched_switches) > 1 and match_data["modular"]:
            fulfillment_text = "**This is a modular switch - what is the correct combination?**\n\n"
            for switch in matched_switches:
                fulfillment_text += f"- {switch.model} with a {switch.network_module}\n"
            fulfillment_text = fulfillment_text[:-1]

        elif match_data["matched"]:
            if len(matched_switches) > 1:
                message = f"**There are {len(matched_switches)} equivalent switches for the {switch_entity}**"
                self.api.messages.create(roomId=room_id, markdown=message)

            # If there are lots of equivalent switches, just return the names
            if len(matched_switches) > 3:
                message = f"*To find out more information about any particular switch, type '/info [SWITCH]'*\n\n"
                for switch in matched_switches:
                    message += f"- {switch.id}  \n"
                self.api.messages.create(roomId=room_id, markdown=message)
            else:
                for switch in matched_switches:
                    attachment = utils.Responses.generate_model_response(
                        switch, original_model=switch_entity)
                    self.api.messages.create(roomId=room_id,
                                             text=str(switch),
                                             attachments=[attachment])

        reply = {"fulfillmentText": fulfillment_text}

        return jsonify(reply)

    def execute_action(self, json_data):
        # Create a Webhook object from the JSON data
        webhook_obj = Webhook(json_data)
        # Get the room details
        room = self.api.rooms.get(webhook_obj.data.roomId)
        # Get the message details
        action = self.api.attachment_actions.get(webhook_obj.data.id)
        # Get the sender's details
        person = self.api.people.get(action.personId)

        # This is a VERY IMPORTANT loop prevention control step.
        # If you respond to all messages...  You will respond to the messages
        # that the bot posts and thereby create a loop condition.
        if action.personId == self.me.id:
            print("Sent by me")
            # Message was sent by me (bot); do not respond.
            return "OK"

        # Sanitise the inputs so that it is compatable with the database and to remove
        # security concerns
        if type(action.inputs) == list:
            inputs = self.editor.sanitise_inputs(action.inputs[0])
        else:
            inputs = self.editor.sanitise_inputs(action.inputs)
        # Will return a string if something went wrong, otherwise a dict
        if type(inputs) == str:
            self.api.messages.create(roomId=room.id,
                                     markdown=str(f"**{inputs}**"))
        else:
            edit_result = self.editor.edit_switch_by_id(
                action.inputs["id"], inputs)
            # Same here, if something goes wrong it will be a str
            if type(edit_result) == str:
                self.api.messages.create(roomId=room.id,
                                         markdown=str(f"**{edit_result}**"))
            else:
                # Everything is OK
                self.api.messages.delete(messageId=webhook_obj.data.messageId)
                if edit_result == utils.Results.EDIT:
                    message = f"Successfully updated {action.inputs['id']}"
                else:
                    message = f"Successfully added {action.inputs['id']}"
                self.api.messages.create(roomId=room.id,
                                         markdown=str(f"**{message}!**"))

        return "OK"

    def receive_message(self, json_data):
        # Create a Webhook object from the JSON data
        webhook_obj = Webhook(json_data)
        # Get the room details
        room = self.api.rooms.get(webhook_obj.data.roomId)
        # Get the message details
        message = self.api.messages.get(webhook_obj.data.id)
        # Get the sender's details
        person = self.api.people.get(message.personId)

        # if __debug__:
        #     print(f"\nNEW MESSAGE IN ROOM '{room.title}'")
        #     print(f"FROM '{person.displayName}'")
        #     print(f"MESSAGE '{message.text}'\n")

        # This is a VERY IMPORTANT loop prevention control step.
        # If you respond to all messages...  You will respond to the messages
        # that the bot posts and thereby create a loop condition.
        if message.personId == self.me.id:
            print("Sent by me")
            # Message was sent by me (bot); do not respond.
            return "OK"

        if not message.text or message.text == "":
            print("Empty message.")
            return "OK"

        message_text = message.text

        # Remove the user tag
        if message_text.lower().startswith("meercat"):
            message_text = " ".join([
                part for part in message_text.split(" ")
                if part.lower() != "meercat"
            ])
        # Fix for help command
        if message_text.strip() == "help":
            message_text = "/help"

        # User has entered a command
        if message_text.strip()[0] == "/":
            response_message = self.handle_command(message.personId,
                                                   message_text)
        else:
            # Create a unique session id as a combo of person and room id
            # We will also use this in the future to send content back (probably a little hacky)
            session_id = message.personId + "." + room.id

            # Call DialogFlow API to parse intent of message
            response = self.converter.detect_intent_texts(
                session_id, message_text, 'en')
            response_message = response.fulfillment_text

        if response_message:
            # Allow for a list response
            if type(response_message) is not list:
                response_message = [response_message]
            for response in response_message:
                # Response will be dict if it is an adaptivecard
                if type(response) is dict:
                    self.api.messages.create(
                        roomId=room.id,
                        text=response['content']['fallbackText'],
                        attachments=[response])
                else:
                    try:
                        self.api.messages.create(roomId=room.id,
                                                 markdown=str(response))

                    # Sometimes the message is too long so we will split it in half
                    except ApiError as e:
                        if "length limited" not in e.message.lower():
                            raise ApiError(e.response)
                        parts = str(response).split('\n')
                        part_1 = '\n'.join(parts[0:int(len(parts) / 2)])
                        part_2 = '\n'.join(parts[int(len(parts) / 2):])
                        self.api.messages.create(roomId=room.id,
                                                 markdown=str(part_1))
                        self.api.messages.create(roomId=room.id,
                                                 markdown=str(part_2))

        response_text = {"message": "OK"}
        return jsonify(response_text)
