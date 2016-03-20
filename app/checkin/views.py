from flask import render_template, redirect, url_for, flash, request
from flask.ext.login import login_required, current_user
from . import checkin
from app import db
from app.model import User, Company, Role, Checkin
from app.decorators import admin_required, admin_moderator_required
from app.email import send_email
from app.checkin.forms import CheckinWithCurrentTimeForm
from datetime import datetime, timedelta, date, time as dt_time


@checkin.route('/', methods = ['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type = int)
    checkins = Checkin.get_checkins_page(page)
    keys = checkins.keys()
    keys.sort()
    print('keys',keys)
    return render_template('checkin/checkin_main.html', user = current_user, checkins = checkins, keys = keys)


@checkin.route('/current_time', methods = ['GET', 'POST'])
@login_required
def checkin_with_current_time():
	form = CheckinWithCurrentTimeForm()
	if form.validate_on_submit():
		checkin = Checkin(time = datetime.utcnow(), user_id = current_user.id)
		db.session.add(checkin)
		return redirect(url_for('checkin.index'))
	return render_template('checkin/current_time.html', form = form, current_time = datetime.utcnow())









