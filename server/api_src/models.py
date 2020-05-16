"""
Module for declaring database models, and their marshmallow schemas
"""
from marshmallow import fields

from api_src.db import DB
from api_src.schema import DictSchema, SessionAuthenticatedMessageSchema


#############
# DB models #
#############


class Game(DB.Model):
    """Game database model"""
    __tablename__ = 'game'
    id = DB.Column(DB.Integer, nullable=False, autoincrement=True, primary_key=True)
    game_ext_id = DB.Column(DB.String(8), nullable=False)
    q_num = DB.Column(DB.Integer, nullable=False, default=0)


class PlayerSession(DB.Model):
    """Player->Game session database model"""
    __tablename__ = 'playersession'
    id = DB.Column(DB.Integer, nullable=False, autoincrement=True, primary_key=True)
    username = DB.Column(DB.String(64), nullable=False)
    session_key = DB.Column(DB.String(8), nullable=False)
    buzz_time = DB.Column(DB.DateTime, nullable=True)
    game_id = DB.Column(DB.Integer, DB.ForeignKey(Game.__tablename__ + '.id', ondelete='CASCADE'), nullable=False)


###################
# Message Schemas #
###################


class PlayerJoinSchemaIn(DictSchema):
    """Schema for payload for /api/<game_ext_id>/join"""
    username = fields.String(required=True)

class SetQNumSchemaIn(SessionAuthenticatedMessageSchema):
    """Schema for payload for /api/<game_ext_id>/set_q_num"""
    q_num = fields.Integer(required=True)
