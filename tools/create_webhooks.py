#!/usr/bin/env python3
#  -*- coding: utf-8 -*-
"""Sample script to read local ngrok info and create a corresponding webhook.

Sample script that reads ngrok info from the local ngrok client api and creates
a Webex Teams Webhook pointint to the ngrok tunnel's public HTTP URL.

Typically ngrok is called run with the following syntax to redirect an
Internet accesible ngrok url to localhost port 8080:

    $ ngrok http 8080

To use script simply launch ngrok, and then launch this script.  After ngrok is
killed, run this script a second time to remove webhook from Webex Teams.

Copyright (c) 2016-2019 Cisco and/or its affiliates.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Use future for Python v2 and v3 compatibility
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
from builtins import *
# Find and import urljoin
from urllib.parse import urljoin

import click
import requests
from webexteamssdk import WebexTeamsAPI

__author__ = "Brad Bester"
__author_email__ = "brbester@cisco.com"
__contributors__ = ["Chris Lunsford <chrlunsf@cisco.com>"]
__copyright__ = "Copyright (c) 2016-2019 Cisco and/or its affiliates."
__license__ = "MIT"




# Constants
NGROK_CLIENT_API_BASE_URL = "http://localhost:4040/api"
WEBHOOK_NAME = ["message_webhook", "attachment_action_webhook"]
WEBHOOK_URL_SUFFIX = ["/events", "/actions"]
WEBHOOK_RESOURCE = ["messages", "attachmentActions"]
WEBHOOK_EVENT = ["created", "created"]


def get_ngrok_public_url():
    """Get the ngrok public HTTP URL from the local client API."""
    try:
        response = requests.get(url=NGROK_CLIENT_API_BASE_URL + "/tunnels",
                                headers={'content-type': 'application/json'})
        response.raise_for_status()

    except requests.exceptions.RequestException:
        print("Could not connect to the ngrok client API; "
              "assuming not running.")
        return None

    else:
        for tunnel in response.json()["tunnels"]:
            if tunnel.get("public_url", "").startswith("http://"):
                print("Found ngrok public HTTP URL:", tunnel["public_url"])
                return tunnel["public_url"]


def delete_webhooks_with_name(api, name):
    """Find a webhook by name."""
    for webhook in api.webhooks.list():
        if webhook.name == name:
            print("Deleting Webhook:", webhook.name, webhook.targetUrl)
            api.webhooks.delete(webhook.id)


def create_ngrok_webhook(api, ngrok_public_url):
    """Create a Webex Teams webhook pointing to the public ngrok URL."""
    for x in range(len(WEBHOOK_NAME)):
        print(f"Creating Webhook '{WEBHOOK_NAME[x]}'...")
        webhook = api.webhooks.create(
            name=WEBHOOK_NAME[x],
            targetUrl=urljoin(ngrok_public_url, WEBHOOK_URL_SUFFIX[x]),
            resource=WEBHOOK_RESOURCE[x],
            event=WEBHOOK_EVENT[x],
        )

        print(webhook)
        print("Webhook successfully created.")


@click.command
@click.option('--url', prompt="Webhook base URL",
              help="The base URL of your bot to receive webhooks from Webex Teams. " + \
                    "If omitted, attempts to find local ngrok tunnel.")
def main(url):
    """Delete previous webhooks. If local ngrok tunnel, create a webhook."""
    api = WebexTeamsAPI()
    for name in WEBHOOK_NAME:
        delete_webhooks_with_name(api, name=name)
    if not url:
        public_url = get_ngrok_public_url()
    else:
        public_url = url
    if public_url is not None:
        create_ngrok_webhook(api, public_url)


if __name__ == '__main__':
    main()
