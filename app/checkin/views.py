from flask import render_template, redirect, url_for, flash
from flask.ext.login import login_required, current_user
from . import checkin
from app import db
from app.model import User, Company, Role
from app.decorators import admin_required, admin_moderator_required
from app.email import send_email
from datetime import datetime, timedelta, date, time as dt_time

@checkin.route('/', methods = ['GET'])
def index():
    return render_template('checkin/checkin_main.html', user = current_user)










