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

import os

import sqlalchemy as db
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

database_url = os.getenv('DATABASE_URL')
db_engine = db.create_engine(database_url)
Session = sessionmaker(bind=db_engine)
Base = declarative_base(name='Model')


class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    privilege = Column(String)

    def is_admin(self):
        return self.privilege.lower() == "admin"

    def can_edit(self):
        return self.privilege.lower() == "editor" or self.is_admin()


class Mapping(Base):
    __tablename__ = 'mapping'

    id = Column(Integer, primary_key=True)
    catalyst = Column(String, ForeignKey('switch.id'))
    meraki = Column(String, ForeignKey('switch.id'))


class Switch(Base):
    __tablename__ = 'switch'

    id = Column(String, primary_key=True)
    platform = Column(String)
    model = Column(String)
    modular = Column(Boolean)

    stackable = Column(Boolean)
    network_module = Column(String)
    tier = Column(String)

    dl_ge = Column(Integer)
    dl_ge_poe = Column(Integer)
    dl_ge_poep = Column(Integer)
    dl_ge_upoep = Column(Integer)
    dl_ge_sfp = Column(Integer)
    dl_2ge_upoe = Column(Integer)
    dl_mgig_poep = Column(Integer)
    dl_mgig_upoe = Column(Integer)
    dl_10ge = Column(Integer)
    dl_10ge_sfpp = Column(Integer)
    dl_25ge_sfp28 = Column(Integer)
    dl_40ge_qsfpp = Column(Integer)
    dl_100ge_qsfp28 = Column(Integer)
    ul_ge_sfp = Column(Integer)
    ul_mgig = Column(Integer)
    ul_10ge_sfpp = Column(Integer)
    ul_25ge_sfp28 = Column(Integer)
    ul_40ge_qsfpp = Column(Integer)
    ul_100ge_qsfp28 = Column(Integer)

    poe_power = Column(Integer)
    switching_capacity = Column(Integer)
    mac_entry = Column(Integer)
    vlan = Column(Integer)
    note = Column(String)

    # Map some pretty names
    _name_mapping = {
        "id": "ID",
        "platform": "Platform",
        "model": "Model",
        "modular": "Modular?",
        "stackable": "Stackable?",
        "network_module": "Network Module",
        "tier": "Tier",
        "dl_ge": "1GE DL",
        "dl_ge_poe": "1GE-PoE DL",
        "dl_ge_poep": "1GE-PoE+ DL",
        "dl_ge_upoep": "1GE-UPoE+ DL",
        "dl_ge_sfp": "1G-SFP DL",
        "dl_2ge_upoe": "2.5GE-UPoE DL",
        "dl_mgig_poep": "mGig-PoE+ DL",
        "dl_mgig_upoe": "mGig-UPoE DL",
        "dl_10ge": "10GE DL",
        "dl_10ge_sfpp": "10G-SFP+ DL",
        "dl_25ge_sfp28": "25G-SFP28 DL",
        "dl_40ge_qsfpp": "40G-QSFP+ DL",
        "dl_100ge_qsfp28": "100G-QSFP28 DL",
        "ul_ge_sfp": "1G-SFP UL",
        "ul_mgig": "mGig UL",
        "ul_10ge_sfpp": "10G-SFP UL",
        "ul_25ge_sfp28": "25G-SFP28 UL",
        "ul_40ge_qsfpp": "40G-QSFP+ UL",
        "ul_100ge_qsfp28": "100G-QSFP28 UL",
        "poe_power": "PoE Power",
        "switching_capacity": "Switching Capacity",
        "mac_entry": "Mac Table Size",
        "vlan": "VLAN",
        "note": "Notes"
    }

    def __repr__(self):
        text = "Here are the details of the equivalent switch:\n\n"
        for attr, value in vars(self).items():
            # Don't append null values or internal attributes
            if value and value != 'null' and attr[0] != '_':
                text += f"{attr}: {value}\n"

        return text
