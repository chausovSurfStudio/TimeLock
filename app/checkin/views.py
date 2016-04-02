from flask import render_template, redirect, url_for, flash, request
from flask.ext.login import login_required, current_user
from . import checkin
from app import db
from app.model import User, Company, Role, Checkin
from app.decorators import admin_required, admin_moderator_required
from app.email import send_email
from app.checkin.forms import CheckinWithCurrentTimeForm, CheckinCustomTimeForm
from datetime import datetime, timedelta, date, time as dt_time


@checkin.route('/', methods = ['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type = int)
    graphs = Checkin.get_checkins_page(page)
    keys = graphs.keys()
    keys.sort()
    default_date_strings = create_default_strings(keys)

    needed_monday = keys[0]
    needed_sunday = needed_monday + timedelta(days = 6)
    prev_monday = needed_monday - timedelta(days = 7)
    prev_sunday = needed_sunday - timedelta(days = 7)
    next_monday = needed_monday + timedelta(days = 7)
    next_sunday = needed_sunday + timedelta(days = 7)

    need_week_title = needed_monday.strftime('%d.%m') + " - " + needed_sunday.strftime('%d.%m')
    prev_week_title = prev_monday.strftime('%d.%m') + " - " + prev_sunday.strftime('%d.%m')
    next_week_title = next_monday.strftime('%d.%m') + " - " + next_sunday.strftime('%d.%m')

    return render_template('checkin/checkin_main.html', user = current_user, graphs = graphs, keys = keys, page = page, 
    	need_title = need_week_title, prev_title = prev_week_title, next_title = next_week_title, default_date_strings = default_date_strings)

def create_default_strings(dates):
    dict = {}
    for date in dates:
        dict.update({date: date.strftime("%d %m %Y %H:%M")})
    return dict

def get_checkins_for_date(date):
    checkins = Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(date, date + timedelta(days = 1))).order_by(Checkin.time)
    checkins_dict = {}
    for checkin in checkins:
        checkins_dict.update({checkin.time.strftime("%A, %d %B %H:%M"): checkin.time.strftime("%d %m %Y %H:%M")})
    return checkins_dict

@checkin.route('/current_time', methods = ['GET', 'POST'])
@login_required
def checkin_with_current_time():
    now = datetime.now()
    now = now.replace(second = 0, microsecond = 0)
    print(now)
    checkin = Checkin(time = now, user_id = current_user.id, trustLevel = True)
    db.session.add(checkin)
    flash('Checkin has been created')
    return redirect(url_for('checkin.index'))

@checkin.route('/custom_time/<default_date_string>', methods = ['GET', 'POST'])
@login_required
def checkin_with_custom_time(default_date_string):
    form  = CheckinCustomTimeForm()
    if form.validate_on_submit():
        time_string = "{} {} {} {} {}".format(form.day.data, form.month.data, form.year.data, form.hours.data, form.minutes.data)
        custom_date = datetime.strptime(time_string, "%d %m %Y %H %M")
        checkin = Checkin(time = custom_date, user_id = current_user.id, trustLevel = False)
        db.session.add(checkin)
        return redirect(url_for('checkin.index'))
    default_date = datetime.strptime(default_date_string, "%d %m %Y %H:%M")
    form.minutes.data = default_date.minute
    form.hours.data = default_date.hour
    form.day.data = default_date.day
    form.year.data = default_date.year
    form.month.data = default_date.month
    return render_template('checkin/custom_time.html', form = form)

@checkin.route('/checkins_create', methods = ['GET','POST'])
@login_required
def checkins_create():
    default_date_string = datetime.now().strftime("%d %m %Y %H:%M")
    return render_template('checkin/checkins_create.html', default_date_string = default_date_string)

@checkin.route('/edit/<date_string>', methods = ['GET', 'POST'])
@login_required
def edit(date_string):
    date = datetime.strptime(date_string, "%d %m %Y %H:%M")
    checkins_dict = get_checkins_for_date(date)
    keys = checkins_dict.keys()
    keys.sort()
    dict_is_empty = True
    if any(checkins_dict):
        dict_is_empty = False
    return render_template('checkin/edit.html', checkins = checkins_dict, keys = keys, dict_is_empty = dict_is_empty)

@checkin.route('/edit/checkin/<date_string>', methods = ['GET', 'POST'])
@login_required
def edit_checkin(date_string):
    form  = CheckinCustomTimeForm()
    selected_date = datetime.strptime(date_string, "%d %m %Y %H:%M")
    selected_checkin = Checkin.get_checkin_with_time(selected_date, current_user.id)
    if not selected_checkin:
        flash("Not found checkins with selected time")
        return redirect(url_for('checkin.index'))
    if form.validate_on_submit():
        time_string = "{} {} {} {} {}".format(form.day.data, form.month.data, form.year.data, form.hours.data, form.minutes.data)
        custom_date = datetime.strptime(time_string, "%d %m %Y %H %M")
        selected_checkin.time = custom_date
        selected_checkin.trustLevel = False
        db.session.add(selected_checkin)
        flash("Checkin has been updated")
        return redirect(url_for('checkin.index'))
    form.minutes.data = selected_date.minute
    form.hours.data = selected_date.hour
    form.day.data = selected_date.day
    form.year.data = selected_date.year
    form.month.data = selected_date.month
    selected_date = selected_date.strftime("%A, %d %B %H:%M")
    return render_template('checkin/edit_checkin.html', form = form, selected_date = selected_date)







