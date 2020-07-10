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

import sqlalchemy as db
from sqlalchemy import or_
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import sessionmaker

import models
from utils import Results


class Editor():
    def __init__(self):
        pass

    def get_approved_users(self, db_session=None):
        # Reuse an existing session if it is passed
        if db_session:
            users = db_session.query(models.User).all()

            return users

        # Create a new db session
        else:
            try:
                db_session = models.Session()

                users = db_session.query(models.User).all()

                return users

            except InvalidRequestError:
                # An SQL error will occur if the database is being spammed
                db_session.rollback()
                return False

            finally:
                db_session.close()

    def get_admin_users(self, db_session=None):
        # Reuse an existing session if it is passed
        if db_session:
            users = db_session.query(models.User).filter(
                models.User.privilege.like("admin")).all()

            return users

        # Create a new db session
        else:
            try:
                db_session = models.Session()

                users = db_session.query(models.User).filter(
                    models.User.privilege.like("admin")).all()

                return users

            except InvalidRequestError:
                # An SQL error will occur if the database is being spammed
                db_session.rollback()
                return False

            finally:
                db_session.close()

    def can_user_edit(self, username, db_session=None):
        # Reuse an existing session if it is passed
        if db_session:
            user = db_session.query(
                models.User).filter(models.User.id == username).all()

            if len(user) == 1:
                return user[0].can_edit()
            return False

        elif not username:
            return False

        # Create a new db session
        else:
            try:
                db_session = models.Session()

                user = db_session.query(
                    models.User).filter(models.User.id == username).all()

                if len(user) == 1:
                    return user[0].can_edit()
                return False

            except InvalidRequestError:
                # An SQL error will occur if the database is being spammed
                db_session.rollback()
                return False

            finally:
                db_session.close()

    def allow_user_by_id(self, me, username):
        try:
            db_session = models.Session()

            if not self.can_user_edit(me, db_session=db_session):
                return f"You do not have permissions to edit allowed users."

            user = db_session.query(
                models.User).filter(models.User.id == username).all()

            if len(user) == 1:
                db_session.delete(user[0])

            new_user = models.User(id=username, privilege="editor")
            db_session.add(new_user)

            db_session.commit()

            return f"Successfully added {username} to the allowed editors list."

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def disallow_user_by_id(self, me, person_id):
        try:
            db_session = models.Session()

            if not self.can_user_edit(me, db_session=db_session):
                return f"You do not have permissions to edit allowed users."

            user = db_session.query(
                models.User).filter(models.User.id == person_id).all()

            if len(user) == 1:
                if not user[0].can_edit():
                    return f"User {person_id} is not on the editors list."
                if user[0].is_admin():
                    return f"User {person_id} is an admin and cannot be removed."
                db_session.delete(user[0])
                db_session.commit()
                return f"Successfully removed {person_id} from the allowed editors list."

            return f"User {person_id} is not on the editors list."

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def list_all_switches(self, parameters):
        # See if there is a filter
        parameters = [p.strip() for p in parameters.split(" ")]
        if len(parameters) > 1:
            do_filter = True
        else:
            do_filter = False
        try:
            db_session = models.Session()

            switches = db_session.query(models.Switch)

            if do_filter:
                switches = switches.filter(
                    models.Switch.id.like(f"%{parameters[1]}%"))

            switches = switches.all()

            return switches

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def list_all_mapping(self, parameters):
        parameters = [p.strip() for p in parameters.split(" ")]
        if len(parameters) > 1:
            do_filter = True
        else:
            do_filter = False

        try:
            db_session = models.Session()

            mapping = db_session.query(models.Mapping)

            if do_filter:
                mapping = mapping.filter(
                    or_(models.Mapping.meraki.like(f"%{parameters[1]}%"),
                        models.Mapping.catalyst.like(f"%{parameters[1]}%")))

            mapping = mapping.all()

            return mapping

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def get_switch_by_id(self, id):
        try:
            db_session = models.Session()

            switch = db_session.query(models.Switch) \
                        .filter(models.Switch.id.like(f"{id}")) \
                        .all()

            if len(switch) == 1:
                return switch[0]

            return None

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def sanitise_inputs(self, values):
        for k, v in values.items():
            try:
                # Convert to bool
                if v == "false":
                    values[k] = False
                elif v == "true":
                    values[k] = True

                # Cast types to target type
                target_type = str(getattr(models.Switch, k).type)
                if target_type == "VARCHAR":
                    values[k] = str(v)
                elif target_type == "INTEGER":
                    if v == None or v == "":
                        v = 0
                    values[k] = int(v)

            except AttributeError:
                return f"Attribute {k} does not exist in models.Switch!"
            except ValueError:
                return f"'{v}' is not valid for attribute {k}. Needs to be of type {target_type}"
        return values

    def edit_switch_by_id(self, id, values):
        try:
            db_session = models.Session()

            switch = db_session.query(models.Switch) \
                        .filter(models.Switch.id.like(f"{id}")) \
                        .all()

            # Edit existing entry
            if len(switch) == 1:
                for k, v, in values.items():
                    # need to type check the inputs here

                    if k in vars(models.Switch).keys():
                        switch[0].__setattr__(k, v)
                db_session.commit()
                return Results.EDIT

            # Create new entry
            elif len(switch) == 0:
                new_switch = models.Switch()
                for k, v, in values.items():
                    # need to type check the inputs here
                    if k in vars(models.Switch).keys():
                        new_switch.__setattr__(k, v)

                db_session.add(new_switch)
                db_session.commit()
                return Results.NEW

            # Didn't match, probably more than one match
            return f"Encountered an error please try again later."
        except AttributeError:
            db_session.rollback()
            return f"Encountered an error please try again later."

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def remove_switch_by_id(self, id):
        try:
            db_session = models.Session()

            switch = db_session.query(models.Switch) \
                        .filter(models.Switch.id.like(f"{id}")) \
                        .all()

            if len(switch) == 1:
                db_session.delete(switch[0])
                db_session.commit()
                return f"Successfully removed **{id}** from the database."

            return f"Could not find **{id}** in the database."

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def remove_mapping_by_id(self, parameters):
        parameters = parameters.split(" ")
        if len(parameters) != 2:
            return "Please only supply 2 keys in the format */remove-mapping PK PK*"
        try:
            db_session = models.Session()

            mapping = db_session.query(models.Mapping) \
                        .filter(or_(
                            models.Mapping.meraki.like(f"{parameters[0]}"),
                            models.Mapping.catalyst.like(f"{parameters[0]}")
                        )) \
                        .filter(or_(
                            models.Mapping.meraki.like(f"{parameters[1]}"),
                            models.Mapping.catalyst.like(f"{parameters[1]}")
                        )) \
                        .all()

            if len(mapping) == 1:
                db_session.delete(mapping[0])
                db_session.commit()
                return f"Successfully removed mapping **{parameters[0]}<=>{parameters[1]}** from the database."

            return f"Could not find **{parameters[0]}<=>{parameters[1]}** in the database."

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()

    def add_mapping_by_id(self, parameters):
        parameters = [p.strip() for p in parameters.split(" ")]
        if len(parameters) != 2:
            return "Please only supply 2 keys in the format */add-mapping PK PK*"
        try:
            db_session = models.Session()

            mapping = db_session.query(models.Mapping) \
                        .filter(or_(
                            models.Mapping.meraki.like(f"{parameters[0]}"),
                            models.Mapping.catalyst.like(f"{parameters[0]}")
                        )) \
                        .filter(or_(
                            models.Mapping.meraki.like(f"{parameters[1]}"),
                            models.Mapping.catalyst.like(f"{parameters[1]}")
                        )) \
                        .all()

            if len(mapping) > 0:
                return f"Mapping **{parameters[0]}<=>{parameters[1]}** already exists in the database."
            else:
                # Determine meraki vs catalyst
                if parameters[0][0].lower() == 'm':
                    meraki = parameters[0]
                    catalyst = parameters[1]
                else:
                    meraki = parameters[1]
                    catalyst = parameters[0]

                mapping = models.Mapping(meraki=meraki, catalyst=catalyst)
                db_session.add(mapping)
                db_session.commit()
                return f"Successfully added mapping **{parameters[0]}<=>{parameters[1]}** to the database."

            return f"Could not find **{parameters[0]}<=>{parameters[1]}** in the database."

        except InvalidRequestError:
            # An SQL error will occur if the database is being spammed
            db_session.rollback()
            return f"Encountered an error please try again later."

        finally:
            db_session.close()
