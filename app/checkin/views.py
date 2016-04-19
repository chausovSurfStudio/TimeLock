from flask import redirect, url_for, flash, request, json, session
from flask.ext.login import login_required, current_user
from . import checkin
from app import db
from app.model import User, Company, Role, Checkin, TimeCache
from app.decorators import admin_required, admin_moderator_required
from app.email import send_email
from app.checkin.forms import CheckinWithCurrentTimeForm, CheckinCustomTimeForm
from datetime import datetime, timedelta, date, time as dt_time
from app.timelock_utils import render_template


@checkin.route('/', methods = ['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type = int)
    graphs_and_time = Checkin.get_checkins_page(page, current_user.id)
    graphs = graphs_and_time[0]
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

    delta = current_user.rate * 60 - graphs_and_time[2]
    bad_work = delta > 0
    if not bad_work:
        delta *= -1
    delta_hours = delta // 60
    delta_minutes = delta % 60
    if delta_minutes < 10:
        delta_minutes = "0{}".format(delta_minutes)
    delta_string = "{}:{}".format(delta_hours, delta_minutes)
    
    return render_template('checkin/checkin_main.html', user = current_user, graphs = graphs, keys = keys, page = page, 
    	need_title = need_week_title, prev_title = prev_week_title, next_title = next_week_title, 
        default_date_strings = default_date_strings, week_total = graphs_and_time[1],
        delta = delta_string, negative_delta = bad_work, pagination_url = "/checkin/?page=")

def create_default_strings(dates):
    dict = {}
    for date in dates:
        dict.update({date: date.strftime("%d %m %Y %H:%M")})
    return dict

def get_checkins_for_date(date, user_id):
    checkins = Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(date, date + timedelta(days = 1))).order_by(Checkin.time)
    checkins_dict = {}
    for checkin in checkins:
        checkins_dict.update({checkin.time.strftime("%A, %d %B %H:%M"): checkin.time.strftime("%d %m %Y %H:%M")})
    return checkins_dict

@checkin.route('/current_time', methods = ['GET', 'POST'])
@login_required
def checkin_with_current_time():
    now = datetime.now()
    now = now.replace(second = 0, microsecond = 0)
    checkin = Checkin(time = now, user_id = current_user.id, trustLevel = True)
    db.session.add(checkin)
    TimeCache.update_cache(current_user.id, now)
    flash('Checkin has been created')
    return redirect(url_for('main.index'))

@checkin.route('/custom_time/<int:user_id>/<default_date_string>', methods = ['GET', 'POST'])
@login_required
def checkin_with_custom_time(user_id, default_date_string):
    form  = CheckinCustomTimeForm()
    if request.method == 'GET':
        redirect_url = json.dumps(request.referrer)
        session['redirect_url'] = redirect_url
    if form.validate_on_submit():
        time_string = "{} {} {} {} {}".format(form.day.data, form.month.data, form.year.data, form.hours.data, form.minutes.data)
        custom_date = datetime.strptime(time_string, "%d %m %Y %H %M")
        checkin = Checkin(time = custom_date, user_id = user_id, trustLevel = False)
        db.session.add(checkin)
        TimeCache.update_cache(user_id, custom_date)
        redirect_url = redirect_url = get_redirect_url_from_session()
        return redirect(redirect_url)
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

@checkin.route('/edit/<int:user_id>/<date_string>', methods = ['GET'])
@login_required
def edit(date_string, user_id):
    redirect_url = json.dumps(request.referrer)
    session['redirect_url'] = redirect_url
    date = datetime.strptime(date_string, "%d %m %Y %H:%M")
    checkins_dict = get_checkins_for_date(date, user_id)
    keys = checkins_dict.keys()
    keys.sort()
    dict_is_empty = True
    if any(checkins_dict):
        dict_is_empty = False
    return render_template('checkin/edit.html', checkins = checkins_dict, keys = keys, dict_is_empty = dict_is_empty, user_id = user_id)

@checkin.route('/edit/checkin/<int:user_id>/<date_string>', methods = ['GET', 'POST'])
@login_required
def edit_checkin(date_string, user_id):
    form  = CheckinCustomTimeForm()
    selected_date = datetime.strptime(date_string, "%d %m %Y %H:%M")
    selected_checkin = Checkin.get_checkin_with_time(selected_date, user_id)
    if not selected_checkin:
        flash("Not found checkins with selected time")
        return redirect(request.referrer)
    if form.validate_on_submit():
        time_string = "{} {} {} {} {}".format(form.day.data, form.month.data, form.year.data, form.hours.data, form.minutes.data)
        custom_date = datetime.strptime(time_string, "%d %m %Y %H %M")
        selected_checkin.time = custom_date
        selected_checkin.trustLevel = False
        db.session.add(selected_checkin)
        TimeCache.update_cache(user_id, custom_date)
        flash("Checkin has been updated")
        redirect_url = redirect_url = get_redirect_url_from_session()
        return redirect(redirect_url)
    form.minutes.data = selected_date.minute
    form.hours.data = selected_date.hour
    form.day.data = selected_date.day
    form.year.data = selected_date.year
    form.month.data = selected_date.month
    selected_date = selected_date.strftime("%A, %d %B %H:%M")
    return render_template('checkin/edit_checkin.html', form = form, selected_date = selected_date)

@checkin.route('/delete/<int:user_id>/<date_string>', methods = ['GET', 'POST'])
@login_required
def delete(date_string, user_id):
    redirect_url = json.dumps(request.referrer)
    session['redirect_url'] = redirect_url
    date = datetime.strptime(date_string, "%d %m %Y %H:%M")
    checkins_dict = get_checkins_for_date(date, user_id)
    keys = checkins_dict.keys()
    keys.sort()
    dict_is_empty = True
    if any(checkins_dict):
        dict_is_empty = False
    return render_template('checkin/delete.html', checkins = checkins_dict, keys = keys, dict_is_empty = dict_is_empty, user_id = user_id)

@checkin.route('/delete/checkin/<int:user_id>/<date_string>')
@login_required
def delete_checkin(date_string, user_id):
    selected_date = datetime.strptime(date_string, "%d %m %Y %H:%M")
    selected_checkin = Checkin.get_checkin_with_time(selected_date, user_id)
    if not selected_checkin:
        flash("Not found checkins with selected time")
        return redirect(request.referrer)
    else:
        db.session.delete(selected_checkin)
        TimeCache.update_cache(user_id, selected_date)
        flash('Selected checkin has been removed')
        redirect_url = get_redirect_url_from_session()
        return redirect(redirect_url)
    return redirect(url_for('checkin.index'))

def get_redirect_url_from_session():
    redirect_url = session['redirect_url']
    if redirect_url[0] == '"':
        redirect_url = redirect_url[1:]
    if redirect_url[-1] == '"':
        redirect_url = redirect_url[:-1]
    return redirect_url




