from flask import Blueprint

checkin = Blueprint('checkin', __name__)

from . import views
from app.model import Permission

@checkin.app_context_processor
def inject_permissions():
    return dict(Permission = Permission)