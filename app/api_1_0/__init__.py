from flask import Blueprint

api = Blueprint('api', __name__)

from app.api_1_0 import authentication, users, errors, decorators
