"""
Module for declaring database models, and their marshmallow schemas
"""
from datetime import datetime

from marshmallow import fields

from api_src.db import DB
from api_src.schema import JsonApiSchema, AuthenticatedMessageSchema


# TODO
# This file is retained as an example how to use the database and schema module.
# Only the schema code is used for now.

class Account(DB.Model):
    """Account database model"""
    __tablename__ = 'accounts'
    id = DB.Column(DB.Integer, nullable=False, autoincrement=True, primary_key=True)
    device_key = DB.Column(DB.String(350), nullable=False)
    create_date = DB.Column(DB.DateTime, nullable=False, default=datetime.utcnow)


class Event(DB.Model):
    """Event database model"""
    __tablename__ = 'events'
    id = DB.Column(DB.Integer, nullable=False, autoincrement=True, primary_key=True)
    latitude = DB.Column(DB.Float(precision=32, asdecimal=True), nullable=False)
    longitude = DB.Column(DB.Float(precision=32, asdecimal=True), nullable=False)
    account_id = DB.Column(DB.Integer, DB.ForeignKey(Account.__tablename__ + '.id', ondelete='CASCADE'), nullable=False)
    time = DB.Column(DB.DateTime, nullable=False)
    group_size_max = DB.Column(DB.Integer, nullable=False)
    group_size_min = DB.Column(DB.Integer, nullable=False)
    title = DB.Column(DB.String(50), nullable=False)
    category = DB.Column(DB.String(50), nullable=False)
    description = DB.Column(DB.String(140), nullable=False)
    create_date = DB.Column(DB.DateTime, nullable=False, default=datetime.utcnow)


class Hype(DB.Model):
    """Hype database model"""
    __tablename__ = 'hypes'
    id = DB.Column(DB.Integer, nullable=False, autoincrement=True, primary_key=True)
    event_id = DB.Column(DB.Integer, DB.ForeignKey(Event.__tablename__ + '.id', ondelete='CASCADE'), nullable=False)
    account_id = DB.Column(DB.Integer, DB.ForeignKey(Account.__tablename__ + '.id', ondelete='CASCADE'), nullable=False)
    create_date = DB.Column(DB.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (DB.UniqueConstraint('event_id', 'account_id', name='_hype_event_account_unique_constraint'),)


class HypeSchemaIn(AuthenticatedMessageSchema):
    """The input marshmallow schema for hype requests"""
    event_id = fields.Integer()


class HypeSchemaOut(JsonApiSchema):
    """The output schema for get Hype requests"""
    count = fields.Integer()


class Checkin(DB.Model):
    """Checkin database model"""
    __tablename__ = 'checkins'
    id = DB.Column(DB.Integer, nullable=False, autoincrement=True, primary_key=True)
    event_id = DB.Column(DB.Integer, DB.ForeignKey(Event.__tablename__ + '.id', ondelete='CASCADE'), nullable=False)
    account_id = DB.Column(DB.Integer, DB.ForeignKey(Account.__tablename__ + '.id', ondelete='CASCADE'), nullable=False)
    create_date = DB.Column(DB.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (DB.UniqueConstraint('event_id', 'account_id', name='_checkin_event_account_unique_constraint'),)


class CheckinSchemaIn(AuthenticatedMessageSchema):
    """Checking Input schema"""
    event_id = fields.Integer()
    user_latitude = fields.Float()
    user_longitude = fields.Float()


class CheckinSchemaOut(JsonApiSchema):
    """Checkin Output Schema"""
    count = fields.Integer()


class EventSchemaIn(AuthenticatedMessageSchema):
    """Event marshmallow schema"""
    latitude = fields.Float()
    longitude = fields.Float()
    time = fields.DateTime()
    group_size_max = fields.Integer()
    group_size_min = fields.Integer()
    title = fields.String()
    category = fields.String()
    description = fields.String()


# TODO I don't like putting these schemas here, but I don't have a better place for them yet.
class EventQueryByLocationSchema(AuthenticatedMessageSchema):
    """Event marshmallow schema"""
    latitude_northeast = fields.Float()
    longitude_northeast = fields.Float()
    latitude_southwest = fields.Float()
    longitude_southwest = fields.Float()


class EventSchemaOut(JsonApiSchema):
    """Event marshmallow schema"""
    id = fields.Integer()
    latitude = fields.Float()
    longitude = fields.Float()
    account_id = fields.Integer()
    time = fields.DateTime()
    hotness = fields.Float()
    group_size_max = fields.Integer()
    group_size_min = fields.Integer()
    title = fields.String()
    category = fields.String()
    description = fields.String()
    hype = fields.Integer()
    checkins = fields.Integer()
    was_checkedin = fields.Boolean()
    was_hyped = fields.Boolean()


class AccountSchemaOut(JsonApiSchema):
    """Account marshmallow schema"""
    id = fields.Integer()
    device_key = fields.String()
