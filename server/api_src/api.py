"""API main"""
import argparse
import datetime
from functools import wraps
import logging
import os
import random
import string

from flask import Flask, render_template, send_from_directory
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
    _app = Flask(__name__, template_folder='../templates')
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


def gen_game_ext_id():
    """
    Generate a new game_ext_id. 8 character string all caps.
    :return: The new game_ext_id
    :rtype: str
    """
    return ''.join(random.choices(string.ascii_uppercase, k=8))


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
        player_list = []
        buzz_index = 0
        for player in players:
            if player.buzz_time:
                player_buzz_index = buzz_index
                buzz_index += 1
            else:
                player_buzz_index = -1

            player_list.append({
                'username': player.username,
                'buzz_order': player_buzz_index
            })

        return {
            'q_num': game.q_num,
            'player_list': player_list
        }, 200, JSON_CT

    return "Invalid game ID, go back and try again", 404


@APP.route('/api/<string:game_ext_id>/clearbuzz', methods=['POST'])
@use_args(SessionAuthenticatedMessageSchema())
@IP_LIMITER.limit('1 per 1 seconds')
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
@IP_LIMITER.limit('1 per 1 seconds')
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


@APP.route('/api/<string:game_ext_id>/buzz', methods=['POST'])
@use_args(SessionAuthenticatedMessageSchema())
@IP_LIMITER.limit('5 per 1 seconds')
@authenticated()
def game_buzz(payload, game_ext_id):
    """
    Buzzes in the current game state as the player authenticated with the session_key

    :param dict payload: POST payload
    :param str game_ext_id: 8 character game_id, Game.game_ext_id in model
    :return: Game update status
    :rtype: dict
    """
    game_ext_id = game_ext_id.upper()

    if not is_authenticated(payload=payload, for_game_ext_id=game_ext_id):
        return {'msg': 'Not authenticated'}, 401, JSON_CT

    player = PlayerSession.query.filter_by(session_key=payload['session_key']).first()
    if player:
        if not player.buzz_time:
            player.buzz_time = datetime.datetime.utcnow()
            DB.session.commit()
        return {
            'msg': 'Buzzed',
            'buzz_time': str(player.buzz_time)
        }, 200, JSON_CT

    return {'msg': 'Invalid session_key'}, 400, JSON_CT


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


@APP.route('/api/create', methods=['POST'])
@use_args(PlayerJoinSchemaIn())
@IP_LIMITER.limit('1 per 10 seconds')
def game_create(payload):
    """
    Create a game session

    :param dict payload: POST payload, must contain 'username'
    :return: Game session_key and game_ext_id.
    :rtype: dict
    """
    game = Game(game_ext_id=gen_game_ext_id())
    DB.session.add(game)
    DB.session.commit()

    username = payload['username']

    player = PlayerSession(username=username,
                           session_key=gen_session_key(),
                           game_id=game.id)
    DB.session.add(player)
    DB.session.commit()
    return {
        'session_key': player.session_key,
        'game_ext_id': game.game_ext_id
    }, 200, JSON_CT


@APP.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return 'You know, for buzz'


@APP.route('/static/js/<path:file_path>', methods=['GET'])
def static_file_router(file_path):
    """Static file router"""
    return send_from_directory('../static', file_path)


@APP.route('/', methods=['GET'])
def landing_page():
    """Landing page"""
    return render_template('landing_page.html')


def main():
    """Main"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=80)
    arguments = parser.parse_args()

    APP.run(debug=True, host='0.0.0.0', port=arguments.port, use_reloader=False)


if __name__ == '__main__':
    main()
