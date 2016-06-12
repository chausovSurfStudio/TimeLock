from flask import Blueprint

nfc = Blueprint('nfc', __name__)

from . import views
from app.model import Permission

@nfc.app_context_processor
def inject_permissions():
    return dict(Permission = Permission)