"""Limiter module"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

IP_LIMITER = Limiter(key_func=get_remote_address)
