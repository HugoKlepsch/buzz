"""API main"""
import argparse
import datetime
from functools import wraps
import logging
import os

from math import sin, cos, sqrt, atan2, radians

from flask import Flask
from flask.logging import create_logger
from flask_apispec import marshal_with
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from webargs.flaskparser import use_args

from api_src.limiter import IP_LIMITER, KEY_LIMITER
from api_src.db import DB
from api_src.garbage_collector import GarbageCollector
from api_src.models import Account, Event, Hype
from api_src.models import AccountSchemaOut
from api_src.models import EventSchemaIn, EventSchemaOut, EventQueryByLocationSchema
from api_src.models import HypeSchemaIn
from api_src.models import Checkin, CheckinSchemaIn
from api_src.models import AuthenticatedMessageSchema
from api_src.schema import JSON_CT, INTERNAL_SERVER_ERROR_JSON_RESPONSE, ok_response, BAD_REQUEST_JSON_RESPONSE
from api_src.schema import JsonApiSchema


def create_app():  # {{{
    """
    Get configuration and create the flask instance.

    :return: The flask app instance.
    :rtype: Flask
    """
    _app = Flask(__name__, template_folder='templates')
    _app.secret_key = 'yeetyeetskeetskeet'
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
    KEY_LIMITER.init_app(_app)

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

        example_account = Account.query.filter_by(device_key='exampleaccount').first()
        if example_account is None:
            _app.logger.info('Creating example account')
            example_account = Account(device_key='exampleaccount')
            DB.session.add(example_account)
            DB.session.commit()

        test_accounts = [Account()] * 5  # five test accounts
        for i, _ in enumerate(test_accounts):
            test_accounts[i] = Account.query.filter_by(device_key='testaccount{i}'.format(i=i)).first()
            if test_accounts[i] is None:
                test_accounts[i] = Account(device_key='testaccount{i}'.format(i=i))
                DB.session.add(test_accounts[i])
                DB.session.commit()

        example_event = Event.query.filter_by(account_id=example_account.id).first()
        if example_event is None:
            _app.logger.info('Creating test event')

            example_event = Event(account_id=example_account.id, latitude=32.079663, longitude=34.775528,
                                  group_size_max=3, group_size_min=1, title="Isreal is real",
                                  category="Social", time=datetime.datetime.utcnow(),
                                  description="Let us come together in peace. 3 hypes")
            DB.session.add(example_event)
            DB.session.commit()
            for i in range(3):
                DB.session.add(Hype(account_id=test_accounts[i].id, event_id=example_event.id))
                DB.session.add(Checkin(account_id=test_accounts[i].id, event_id=example_event.id))

            example_event_two = Event(account_id=example_account.id, latitude=43.545199, longitude=-80.246926,
                                      group_size_max=5, group_size_min=3, title="Trappers halloween costume party",
                                      category="Social drinking", time=datetime.datetime.utcnow(),
                                      description="BYOB costume party. Hawaiian theme. 5 hypes")
            DB.session.add(example_event_two)
            DB.session.commit()
            for i in range(5):
                DB.session.add(Hype(account_id=test_accounts[i].id, event_id=example_event_two.id))
                DB.session.add(Checkin(account_id=test_accounts[i].id, event_id=example_event_two.id))

            example_event_three = Event(account_id=example_account.id, latitude=43.530793, longitude=-80.229077,
                                        group_size_max=1, group_size_min=1, title="LAN party in Reynolds!",
                                        category="Sports", time=datetime.datetime.utcnow(),
                                        description="Bring a laptop and Halo CE for the LAN party. 3 hypes")
            DB.session.add(example_event_three)
            DB.session.commit()
            for i in range(3):
                DB.session.add(Hype(account_id=test_accounts[i].id, event_id=example_event_three.id))
                DB.session.add(Checkin(account_id=test_accounts[i].id, event_id=example_event_three.id))

            example_event_four = Event(account_id=example_account.id, latitude=43.531793, longitude=-80.228077,
                                       group_size_max=1, group_size_min=1, title="Vapers anonymous",
                                       category="Social", time=datetime.datetime.utcnow(),
                                       description="0 hypes")
            DB.session.add(example_event_four)
            DB.session.commit()

        _app.logger.info('Created test account and events')
# }}}


APP = create_app()
setup_database(APP)


def is_authenticated(payload, as_device=None):
    """
    Check if the requester is authenticated

    :param dict payload: Payload loaded from request. Key 'device_key' should exist
    :param str as_device: Optional device_key the requester should be authenticated as
    :return: Is the requester authenticated
    :rtype: bool
    """
    if 'device_key' in payload:
        device_key = payload['device_key']
        return (Account.query.filter_by(device_key=device_key).first() is not None) and \
               (as_device is None or device_key == as_device)
    return False


def authenticated(as_device=None):
    """
    Decorator to ensure a user is authenticated before calling decorated function.

    :param str as_device: Optional device_key the requester should be authenticated as
    :return: The decorated function
    :rtype: funct
    """
    def _authenticated(function):
        @wraps(function)
        def __authenticated(payload, *args, **kwargs):
            # just do here everything what you need

            if not is_authenticated(payload=payload, as_device=as_device):
                # TODO add the token auth
                if 'device_key' in payload:
                    account = Account(device_key=payload['device_key'])
                    DB.session.add(account)
                    DB.session.commit()
                else:
                    return {'msg': 'Not authenticated'}, 401, JSON_CT

            result = function(payload, *args, **kwargs)

            return result
        return __authenticated
    return _authenticated


def calculate_event_hotness(event):
    """
    Calculate the hotness of an event, and add it as the `hotness` field on the event.

    :param Union[Event,Iterable(Event)] event: the event to calculate hotness for
    :return: The given event, with new `hotness` field containing the hotness
    :rtype: Event
    """

    # we need the "HYPE" for each event before we can calculate hotness.
    calculate_event_hype(event)
    calculate_event_checkins(event)

    def _calculate_event_hotness(_event):
        return (_event.hype ** 0.9) + (_event.checkins ** 0.9)

    if isinstance(event, list):
        for element in event:
            element.hotness = _calculate_event_hotness(element)
    else:
        event.hotness = _calculate_event_hotness(event)
    return event


def calculate_event_checkins(event):
    """
    Retrieve the number of checkins for a particular event, and enter it as a `checkins` key
    in the event dictionary.
    """

    def _calculate_event_checkins(_event):
        event_id = _event.id
        try:
            return Checkin.query.filter_by(event_id=event_id).count()
        except SQLAlchemyError as exception:
            APP.logger.exception("Failed to calculate the checkins for this event: %s", exception)
            return None

    if isinstance(event, list):
        for element in event:
            element.checkins = _calculate_event_checkins(element)
    else:
        event.checkins = _calculate_event_checkins(event)
    return event


def set_was_checkedin_by_user(event, device_key):# {{{
    """
        Given an event, check to see if it was been checked into for a user.
    """

    def _set_was_checkedin_by_user(_event, _device_key):
        event_id = _event.id
        try:
            account_id = Account.query.filter_by(device_key=_device_key).first().id

            was_checkedin = Checkin.query.filter_by(account_id=account_id, event_id=event_id).count() > 0
            return was_checkedin

        except SQLAlchemyError as exception:
            APP.logger.exception("Failed to check into this event: %s", exception)
            return None

    if isinstance(event, list):
        for element in event:
            element.was_checkedin = _set_was_checkedin_by_user(element, device_key)

    else:
        event.was_checkedin = _set_was_checkedin_by_user(event, device_key)

    return event


def set_was_hyped_by_user(event, device_key):
    """
    Check the database to see if the event in question was hyped by this device key
    before.  If so, set event->was_hyped to true; otherwise false.
    """

    def _set_was_hyped_by_user(_event, _device_key):
        event_id = _event.id
        try:
            account_id = Account.query.filter_by(device_key=_device_key).first().id

            # check if there exists a record of this account hyping this event.
            was_hyped = Hype.query.filter_by(account_id=account_id, event_id=event_id).count() > 0
            return was_hyped

        except SQLAlchemyError as exception:
            APP.logger.exception("Failed to retrieve hype record: %s", exception)
            return None


    if isinstance(event, list):
        for element in event:
            element.was_hyped = _set_was_hyped_by_user(element, device_key)
    else:
        event.was_hyped = _set_was_hyped_by_user(event, device_key)
    return event


def calculate_event_hype(event):
    """
    Retrieve the hype entries for a particular event, and enter it as a `hype` key
    in the event dictionary.
    """

    def _calculate_event_hype(_event):
        event_id = _event.id
        try:
            return Hype.query.filter_by(event_id=event_id).count()
        except SQLAlchemyError as exception:
            APP.logger.exception("Failed to get hype for event: %s", exception)
            return None

    if isinstance(event, list):
        for element in event:
            element.hype = _calculate_event_hype(element)
    else:
        event.hype = _calculate_event_hype(event)
    return event


def haversine_distance(lat_a, lng_a, lat_b, lng_b):
    """
    Returns the Haversine distance between two points (see Haversine's algorithm)
    """
    earth_radius = 6373.0

    rad_lat_a = radians(lat_a)
    rad_lng_a = radians(lng_a)

    rad_lat_b = radians(lat_b)
    rad_lng_b = radians(lng_b)

    dlat = rad_lat_b - rad_lat_a
    dlng = rad_lng_b - rad_lng_a

    const_a = sin(dlat / 2)**2 + cos(rad_lat_a) * cos(rad_lat_b) * sin(dlng / 2)**2
    const_c = 2 * atan2(sqrt(const_a), sqrt(1 - const_a))

    distance = earth_radius * const_c

    return distance * 1000



@APP.route('/api/all_accounts', methods=['POST'])
@use_args(AuthenticatedMessageSchema())
@authenticated(as_device='testaccount')  # TODO create admin account
@marshal_with(AccountSchemaOut(many=True))
def all_accounts(_payload):
    """
    Get all accounts. Must be authenticated as 'testaccount'.

    :return: All accounts
    :rtype: list[Account]
    """
    return Account.query.all()


@APP.route('/api/events/by_location', methods=['POST'])
@use_args(EventQueryByLocationSchema())
@IP_LIMITER.limit('5 per 1 seconds')
@KEY_LIMITER.limit('5 per 1 seconds')
@authenticated()
@marshal_with(EventSchemaOut(many=True))
def events_for_area(payload):
    """
    Get all events in an area.

    :return: All events in the given area
    :rtype: list[EventSchemaOut]
    """
    try:
        latitude_ne = float(payload['latitude_northeast'])
        longitude_ne = float(payload['longitude_northeast'])
        latitude_sw = float(payload['latitude_southwest'])
        longitude_sw = float(payload['longitude_southwest'])
    except (KeyError, ValueError):
        return [{'msg': 'Bad request'}], 400, JSON_CT

    events = Event.query.filter(
        and_(
            and_(
                Event.latitude >= latitude_sw,
                Event.latitude < latitude_ne
            ),
            and_(
                Event.longitude >= longitude_sw,
                Event.longitude < longitude_ne
            )
        )
    ).all() or []

    calculate_event_hotness(events)
    calculate_event_checkins(events)
    set_was_hyped_by_user(events, payload['device_key'])
    set_was_checkedin_by_user(events, payload['device_key'])

    return events


@APP.route('/api/events/by_device_key', methods=['POST'])
@use_args(AuthenticatedMessageSchema())
@IP_LIMITER.limit('5 per 1 second')
@KEY_LIMITER.limit('5 per 1 second')
@authenticated()
@marshal_with(EventSchemaOut(many=True))
def events_for_account_id(payload):
    """
    Get all events for the authenticated user.

    :return: All events for the logged in user.
    :rtype: list[EventSchemaOut]
    """
    device_key = payload['device_key'] or ''
    account = Account.query.filter_by(device_key=device_key).first()
    if account:
        events = Event.query.filter_by(account_id=account.id).all() or []
        calculate_event_hotness(events)
        calculate_event_checkins(events)
        set_was_hyped_by_user(events, payload['device_key'])
        set_was_checkedin_by_user(events, payload['device_key'])
        return events
    return []


@APP.route('/api/event', methods=['POST'])
@use_args(EventSchemaIn())
@IP_LIMITER.limit('1 per 10 seconds')
@KEY_LIMITER.limit('1 per 10 seconds')
@authenticated()
@marshal_with(JsonApiSchema())
def create_event(event_data):
    """
    Create an event.

    :param dict event_data: Dict with a subset of the Event fields.
    :return: Status of the request. 200 if valid, 400 or 500 if not.
    :rtype: tuple[dict, int, dict]
    """
    device_key = event_data.get('device_key', None)
    latitude = event_data.get('latitude', None)
    longitude = event_data.get('longitude', None)
    time = event_data.get('time', None)
    description = event_data.get('description', None)
    category = event_data.get('category', None)

    group_size_min = event_data.get('group_size_min', None)
    group_size_max = event_data.get('group_size_max', None)
    title = event_data.get('title', None)

    APP.logger.info('Creating event at (%f,%f)', latitude, longitude)
    try:
        account = Account.query.filter_by(device_key=device_key).first()
        event = Event(account_id=account.id,
                      latitude=latitude,
                      longitude=longitude,
                      time=time,
                      group_size_max=group_size_max,
                      group_size_min=group_size_min,
                      title=title,
                      description=description,
                      category=category)

        DB.session.add(event)
        DB.session.commit()
        return ok_response('Added event at (%f,%f)' % (latitude, longitude))
    except SQLAlchemyError as exception:
        APP.logger.exception('Failed to create event: %s', exception)
        return INTERNAL_SERVER_ERROR_JSON_RESPONSE


@APP.route('/api/checkin/by_id', methods=['POST'])
@use_args(CheckinSchemaIn())
@IP_LIMITER.limit('1 per 5 seconds')
@KEY_LIMITER.limit('1 per 5 seconds')
@authenticated()
@marshal_with(JsonApiSchema())
def checkin_event(checkin_data):
    """Endpoint for Checking into an event; creates a new Checkin entry"""
    device_key = checkin_data.get('device_key', None)
    event_id = checkin_data.get('event_id', None)
    user_latitude = checkin_data.get('user_latitude', None)
    user_longitude = checkin_data.get('user_longitude', None)

    try:
        account = Account.query.filter_by(device_key=device_key).first()

        if Checkin.query.filter_by(account_id=account.id, event_id=event_id).count() > 0:
            return {'msg': 'Cannot checkin to this event again.'}, 409, JSON_CT

        event = Event.query.filter_by(id=event_id).first()
        if event:

            if haversine_distance(event.latitude, event.longitude, user_latitude, user_longitude) <= 100:
                checkin = Checkin(account_id=account.id, event_id=event_id)
                DB.session.add(checkin)
                DB.session.commit()
                return ok_response('Successfully checked in to this event %d' % (event_id))

            return BAD_REQUEST_JSON_RESPONSE

        return BAD_REQUEST_JSON_RESPONSE

    except SQLAlchemyError as exception:
        APP.logger.exception("Failed to checkin to this event: %s", exception)
        return INTERNAL_SERVER_ERROR_JSON_RESPONSE


@APP.route('/api/hype/by_id', methods=['POST'])
@use_args(HypeSchemaIn())
@IP_LIMITER.limit('1 per 2 seconds')
@KEY_LIMITER.limit('1 per 2 seconds')
@authenticated()
@marshal_with(JsonApiSchema())
def hype_event(hype_data):
    """Endpoint for hyping an event; creates a new Hype entry"""
    device_key = hype_data.get('device_key', None)
    event_id = hype_data.get('event_id', None)

    try:
        account = Account.query.filter_by(device_key=device_key).first()

        if Hype.query.filter_by(account_id=account.id, event_id=event_id).count() > 0:
            return {'msg': 'Cannot hype an event again.'}, 409, JSON_CT

        hype = Hype(account_id=account.id, event_id=event_id)
        DB.session.add(hype)
        DB.session.commit()
        return ok_response('Successfully hyped event %d' % (event_id))

    except SQLAlchemyError as exception:
        APP.logger.exception("Failed to hype event: %s", exception)
        return INTERNAL_SERVER_ERROR_JSON_RESPONSE



@APP.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return 'You know, for buzz'


def main():
    """Main"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=80)
    arguments = parser.parse_args()

    collector = GarbageCollector(DB, APP, datetime.timedelta(hours=1), retention_period=datetime.timedelta(hours=24))
    collector.start()

    APP.run(debug=True, host='0.0.0.0', port=arguments.port, use_reloader=False)


if __name__ == '__main__':
    main()
