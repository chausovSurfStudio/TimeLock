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

    needed_monday = keys[0]
    needed_sunday = needed_monday + timedelta(days = 6)
    prev_monday = needed_monday - timedelta(days = 7)
    prev_sunday = needed_sunday - timedelta(days = 7)
    next_monday = needed_monday + timedelta(days = 7)
    next_sunday = needed_sunday + timedelta(days = 7)

    need_week_title = needed_monday.strftime('%d.%m') + " - " + needed_sunday.strftime('%d.%m')
    prev_week_title = prev_monday.strftime('%d.%m') + " - " + prev_sunday.strftime('%d.%m')
    next_week_title = next_monday.strftime('%d.%m') + " - " + next_sunday.strftime('%d.%m')

    return render_template('checkin/checkin_main.html', user = current_user, checkins = checkins, keys = keys, page = page, 
    	need_title = need_week_title, prev_title = prev_week_title, next_title = next_week_title)


@checkin.route('/current_time', methods = ['GET', 'POST'])
@login_required
def checkin_with_current_time():
	form = CheckinWithCurrentTimeForm()
	if form.validate_on_submit():
		checkin = Checkin(time = datetime.utcnow(), user_id = current_user.id)
		db.session.add(checkin)
		return redirect(url_for('checkin.index'))
	return render_template('checkin/current_time.html', form = form, current_time = datetime.utcnow())









