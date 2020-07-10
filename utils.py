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

from pyadaptivecards.actions import Submit
from pyadaptivecards.card import AdaptiveCard
from pyadaptivecards.components import (Column, Fact, Image, ImageSize,
                                        TextBlock)
from pyadaptivecards.container import Container, FactSet
from pyadaptivecards.inputs import Choices, Number, Text, Toggle

import models


def person_id_to_username(api, person_id):
    persons = api.people.list(id=person_id)
    for person in persons:
        if person.id == person_id:
            for email in person.emails:
                # We only want cisco people
                if "@cisco.com" in email:
                    return email.split("@")[0]
    return None


class DictWrapper:
    def __init__(self, d):
        self.__d = d

    def to_dict(self):
        return self.__d

    def to_json(self):
        import json
        return json.dumps(self.to_dict())


class Results:
    NEW = 1
    EDIT = 2


class Responses:
    @staticmethod
    def generate_model_response(switch_data, original_model=None):
        items = []
        if original_model:
            items.append(
                TextBlock(text=f"The {original_model} is equivalent to the",
                          size="Small",
                          weight="Lighter"))
        items.append(
            TextBlock(text=f"{switch_data.model}",
                      size="ExtraLarge",
                      color="Accent",
                      spacing=None))
        title = Container(items=items)

        facts = []
        for attr, description in models.Switch._name_mapping.items():
            value = vars(switch_data).get(attr, None)
            if value:
                facts.append(Fact(description, value))

        factset = FactSet(facts)

        card = AdaptiveCard(body=[title, factset],
                            fallbackText=str(switch_data))

        attachment = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card.to_dict(),
        }

        return attachment

    @staticmethod
    def generate_switches_response(switches):
        response = f"**The following {len(switches)} switches are in the database:**\n\n"

        for switch in switches:
            response += f"- {switch.id}  \n"

        return response.strip()

    @staticmethod
    def generate_mapping_response(mappings):
        response = f"**The following {len(mappings)} mappings are in the database:**\n\n"

        for mapping in mappings:
            response += f"- {mapping.catalyst} <=> {mapping.meraki}  \n"

        return response.strip()

    @staticmethod
    def generate_edit_response(switch):
        title = Container(items=[
            TextBlock(text=f"Currently editing switch",
                      size="Small",
                      weight="Lighter"),
            TextBlock(text=f"{switch.model}",
                      size="ExtraLarge",
                      color="Accent",
                      spacing=None)
        ])

        items = []
        vars(models.Switch).keys()
        for attr, description in models.Switch._name_mapping.items():
            try:
                value = vars(switch).get(attr, None)
                # Don't append null values or internal attributes
                if attr[0] != '_':
                    if type(value) == bool:
                        items.append(Toggle(description, attr, value=value))
                    else:
                        items.append(TextBlock(text=f"{description}"))
                        items.append(
                            Text(attr, placeholder=f"{description}", value=value))

            except AttributeError:
                continue

        submit = Submit(title="Update")

        body = Container(items=items)

        card = AdaptiveCard(
            body=[title, body],
            actions=[submit],
            fallbackText=str(
                "Adaptive cards need to be enabled to use this feature."))

        attachment = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card.to_dict(),
        }

        return attachment

    @staticmethod
    def generate_add_response():
        title = Container(items=[
            TextBlock(text=f"Currently adding a new switch",
                      size="Small",
                      weight="Lighter"),
        ])

        items = []
        for attr in vars(models.Switch).keys():
            # Don't append null values or internal attributes
            if attr[0] != '_':
                # This is so stupid, probably not the best way to do it
                target_type = str(
                    getattr(models.Switch, attr).property.columns[0].type)
                if target_type == "BOOLEAN":
                    items.append(Toggle(attr, attr))
                else:
                    items.append(TextBlock(text=f"{attr}"))
                    items.append(Text(attr, placeholder=f"{attr}"))

        submit = Submit(title="Add")

        body = Container(items=items)

        card = AdaptiveCard(
            body=[title, body],
            actions=[submit],
            fallbackText=str(
                "Adaptive cards need to be enabled to use this feature."))

        attachment = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card.to_dict(),
        }

        return attachment

    @staticmethod
    def generate_user_access_request(api, editor, person_id, username,
                                     parameters):
        admins = editor.get_admin_users()
        person = api.people.get(person_id)
        if not person or not admins:
            pass

        # Display none if nothing is supplied
        if parameters == "":
            parameters = "None"

        message = f"{person.displayName} is requesting access for reason: {parameters}\n\nGrant access with command '/allow {username}'"

        for admin in admins:
            api.messages.create(toPersonEmail=admin.id + "@cisco.com",
                                markdown=message)

    @staticmethod
    def generate_approved_users_response(api, users):
        message = "**Users with editing permissions:**\n\n"
        for user in users:
            persons = api.people.list(email=f"{user.id}@cisco.com")
            for person in persons:
                message += f"{person.displayName} => {user.id}  \n"
        return message
