"""API main"""
import argparse
import datetime
from functools import wraps
import logging
import os
import random
import string

from flask import Flask
from flask.logging import create_logger
from webargs.flaskparser import use_args

from api_src.limiter import IP_LIMITER
from api_src.db import DB
from api_src.models import Game, PlayerSession
from api_src.models import SessionAuthenticatedMessageSchema
from api_src.models import PlayerJoinSchemaIn, SetQNumSchemaIn
from api_src.schema import JSON_CT


def create_app():  # {{{
    """
    Get configuration and create the flask instance.

    :return: The flask app instance.
    :rtype: Flask
    """
    _app = Flask(__name__)
    _app.secret_key = 'yeetyeetskeetskeet' # This seems like a TODO, but I don't know what to do about it
    _app.logger = create_logger(_app)
    _app.logger.setLevel(logging.DEBUG)

    db_host = os.environ.get('DBHOST', '127.0.0.1')
    db_port = int(os.environ.get('DBPORT', 5432))
    db_password = os.environ.get('DBPASS', 'notwaterloo')
    db_database = 'buzzdb'
    db_string = 'postgresql://root:{password}@{host}:{port}/{database}'.format(
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_database
    )
    _app.config['SQLALCHEMY_DATABASE_URI'] = db_string
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    DB.init_app(_app)
    IP_LIMITER.init_app(_app)

    return _app
# }}}

def setup_database(_app):  # {{{
    """Add some sample data to database"""
    with _app.app_context():
        _app.logger.info('Creating databases')
        DB.drop_all()  # TODO do not drop all data on restart
        DB.create_all()
        DB.session.commit()
        _app.logger.info('Created databases')

        example_game = Game.query.filter_by(game_ext_id='BASEMENT').first()
        if example_game is None:
            _app.logger.info('Creating example game')
            example_game = Game(game_ext_id='BASEMENT')
            DB.session.add(example_game)
            DB.session.commit()

        for i in range(5):
            test_playersession = PlayerSession(username='Player{num}'.format(num=i),
                                               session_key=gen_session_key(),
                                               game_id=example_game.id)
            DB.session.add(test_playersession)
            DB.session.commit()

        _app.logger.info('Created test game and playersessions')
# }}}


def is_authenticated(payload, for_game_ext_id=None):
    """
    Check if the requester is authenticated

    :param dict payload: Payload loaded from request. Key 'session_key' should exist
    :param str for_game_ext_id: game_ext_id the session key must match
    :return: Is the requester authenticated
    :rtype: bool
    """
    if 'session_key' in payload:
        session_key = payload['session_key']
        player = PlayerSession.query.filter_by(session_key=session_key).first()
        if for_game_ext_id:
            game = Game.query.filter_by(id=player.game_id).first()
            if game:
                return game.game_ext_id == for_game_ext_id
        else:
            return player is not None
    return False


def authenticated(for_game_ext_id=None):
    """
    Decorator to ensure a user is authenticated before calling decorated function.

    :param str for_game_ext_id: game_ext_id the session key must match
    :return: The decorated function
    :rtype: funct
    """
    def _authenticated(function):
        @wraps(function)
        def __authenticated(payload, *args, **kwargs):
            # just do here everything what you need

            if not is_authenticated(payload=payload, for_game_ext_id=for_game_ext_id):
                return {'msg': 'Not authenticated'}, 401, JSON_CT

            result = function(payload, *args, **kwargs)

            return result
        return __authenticated
    return _authenticated


def gen_session_key():
    """
    Generate a new session key. 64 character alpha-numeric string.
    :return: The new session key
    :rtype: str
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=64))


APP = create_app()
setup_database(APP)


@APP.route('/api/<string:game_ext_id>', methods=['POST'])
@use_args(SessionAuthenticatedMessageSchema())
@IP_LIMITER.limit('5 per 1 seconds')
@authenticated()
def game_status_simple(payload, game_ext_id):
    """
    Get status of game session denoted by game_id.

    :param dict payload: POST payload
    :param str game_ext_id: 8 character game_id, Game.game_ext_id in model
    :return: Game status
    :rtype: dict
    """
    game_ext_id = game_ext_id.upper()

    if not is_authenticated(payload=payload, for_game_ext_id=game_ext_id):
        return {'msg': 'Not authenticated'}, 401, JSON_CT

    game = Game.query.filter_by(game_ext_id=game_ext_id).first()
    if game:
        players = PlayerSession.query.filter_by(game_id=game.id).all()
        players.sort(key=lambda player: (player.buzz_time if player.buzz_time
                                         else datetime.datetime(year=1980, month=1, day=1)))
        return {
            'q_num': game.q_num,
            'player_list': [
                {
                    'username': player.username,
                    'buzz_order': i if player.buzz_time else -1
                }
                for i, player in enumerate(players)
            ]
        }, 200, JSON_CT

    return "Invalid game ID, go back and try again", 404


@APP.route('/api/<string:game_ext_id>/clearbuzz', methods=['POST'])
@use_args(SessionAuthenticatedMessageSchema())
@IP_LIMITER.limit('5 per 1 seconds')
@authenticated()
def game_clear_buzz(payload, game_ext_id):
    """
    Clear buzzes in the current game state

    :param dict payload: POST payload
    :param str game_ext_id: 8 character game_id, Game.game_ext_id in model
    :return: Game update status
    :rtype: dict
    """
    game_ext_id = game_ext_id.upper()

    if not is_authenticated(payload=payload, for_game_ext_id=game_ext_id):
        return {'msg': 'Not authenticated'}, 401, JSON_CT

    game = Game.query.filter_by(game_ext_id=game_ext_id).first()
    if game:
        players = PlayerSession.query.filter_by(game_id=game.id).all()
        for player in players:
            player.buzz_time = None
        DB.session.commit()
        return {'msg': 'Buzzes cleared'}, 200, JSON_CT

    return "Invalid game ID, go back and try again", 404


@APP.route('/api/<string:game_ext_id>/set_q_num', methods=['POST'])
@use_args(SetQNumSchemaIn())
@IP_LIMITER.limit('5 per 1 seconds')
@authenticated()
def game_set_q_num(payload, game_ext_id):
    """
    Set the question number in the current game state

    :param dict payload: POST payload, must have q_num
    :param str game_ext_id: 8 character game_id, Game.game_ext_id in model
    :return: Game update status
    :rtype: dict
    """
    game_ext_id = game_ext_id.upper()

    if not is_authenticated(payload=payload, for_game_ext_id=game_ext_id):
        return {'msg': 'Not authenticated'}, 401, JSON_CT

    game = Game.query.filter_by(game_ext_id=game_ext_id).first()
    if game:
        try:
            new_q_num = int(payload['q_num'])
            game.q_num = new_q_num
            DB.session.commit()
            return {'msg': 'Question number set to {q_num}'.format(q_num=new_q_num)}, 200, JSON_CT
        except (KeyError, ValueError):
            return {'msg': 'Invalid question number'}, 400, JSON_CT

    return "Invalid game ID, go back and try again", 404


@APP.route('/api/<string:game_ext_id>/join', methods=['POST'])
@use_args(PlayerJoinSchemaIn())
@IP_LIMITER.limit('1 per 1 seconds')
def game_join(payload, game_ext_id):
    """
    Join a game session denoted by game_id.

    :param dict payload: POST payload, must contain 'username'
    :param str game_ext_id: 8 character game_id, Game.game_ext_id in model
    :return: Game session_key. PlayerSession.session_key in model
    :rtype: dict
    """
    game_ext_id = game_ext_id.upper()

    game = Game.query.filter_by(game_ext_id=game_ext_id).first()
    if game:
        username = payload['username']

        player = PlayerSession.query.filter_by(game_id=game.id, username=username).first()
        if not player:
            player = PlayerSession(username=username,
                                   session_key=gen_session_key(),
                                   game_id=game.id)
            DB.session.add(player)
            DB.session.commit()
        return {'session_key': player.session_key}, 200, JSON_CT

    return "Invalid game ID, go back and try again", 404


@APP.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return 'You know, for buzz'


def main():
    """Main"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=80)
    arguments = parser.parse_args()

    APP.run(debug=True, host='0.0.0.0', port=arguments.port, use_reloader=False)


if __name__ == '__main__':
    main()
