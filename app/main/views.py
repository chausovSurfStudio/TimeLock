from flask import redirect, url_for, flash, request, abort
from flask.ext.login import login_required, current_user
from . import main
from app import db
from app.model import User, Company, Role, Checkin, TimeCache, Post, Permission
from app.decorators import admin_required, admin_moderator_required
from forms import NewCompanyForm, SetPasswordForm, EditProfileForm, EditProfileAdminForm, ResetPasswordRequestForm, NewUserForm, EditProfileModeratorForm, PostForm
from forms import ConfirmDeleteDBEntityForm
from app.email import send_email
from datetime import datetime, timedelta, date, time as dt_time
from app.production_calendar import work_days_count
from app.timelock_utils import render_template, delete_company_with_id, delete_user_with_id, get_user_work_time_for_month_page, format_full_time_string_from_minutes

@main.route('/', methods = ['GET', 'POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		post = Post(body = form.body.data, author = current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('main.index'))
	posts = Post.query.order_by(Post.timestamp.desc()).all()
	return render_template('index.html', form = form, posts = posts)

@main.route('/new_company', methods = ['GET', 'POST'])
@admin_required
def new_company():
	form = NewCompanyForm()
	if form.validate_on_submit():
		company = Company(company_name = form.name.data)
		db.session.add(company)
		db.session.commit()
		user = User.query.filter_by(email = form.email.data).first()
		if user is None:
			user = User(email = form.email.data)
		user.role = Role.query.filter_by(name = 'Moderator').first()
		user.company = company
		user.first_name = form.first_name.data
		user.last_name = form.last_name.data
		user.password = form.password.data
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_email(user.email, 'Confirm Your Account', 'mail/confirm_moderator', company_name = company.company_name, token = token, email = form.email.data, password = form.password.data)
		flash('You create new company, message to moderator has been sent')
		return redirect(url_for('main.index'))
	return render_template('new_company.html', form = form)

@main.route('/companies', methods = ['GET'])
@admin_required
def companies():
	companies = Company.query.order_by(Company.company_name).all()
	return render_template('companies.html', companies = companies)

@main.route('/clear_companies', methods = ['GET', 'POST'])
@admin_required
def clear_companies():
	Company.query.delete()
	return redirect(url_for('main.index'))

@main.route('/clear_users', methods = ['GET', 'POST'])
@admin_required
def clear_users():
	User.query.delete()
	Checkin.query.delete()
	return redirect(url_for('main.index'))

@main.route('/user/<int:user_id>')
@login_required
def user(user_id):
    user = User.query.filter_by(id = user_id).first_or_404()
    if current_user.is_moderator():
	    page = request.args.get('page', 1, type = int)
	    graphs_and_time = Checkin.get_checkins_page(page, user_id)
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

	    delta = user.rate * 60 - graphs_and_time[2]
	    bad_work = delta > 0
	    if not bad_work:
	        delta *= -1
	    delta_hours = delta // 60
	    delta_minutes = delta % 60
	    if delta_minutes < 10:
	        delta_minutes = "0{}".format(delta_minutes)
	    delta_string = "{}:{}".format(delta_hours, delta_minutes)

	    pagination_url = "/user/{}?page=".format(user.id)
	    print("pagination_url = ", pagination_url)

	    return render_template('user.html', user = user, graphs = graphs, keys = keys, page = page, 
	    	need_title = need_week_title, prev_title = prev_week_title, next_title = next_week_title, 
	        default_date_strings = default_date_strings, week_total = graphs_and_time[1],
	        delta = delta_string, negative_delta = bad_work, pagination_url = pagination_url)
    return render_template('user.html', user = user)

def create_default_strings(dates):
    dict = {}
    for date in dates:
        dict.update({date: date.strftime("%d %m %Y %H:%M")})
    return dict

@main.route('/edit_profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(user = current_user)
    if form.validate_on_submit():
    	current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.middle_name = form.middle_name.data
        current_user.nfc_label = form.nfc_label.data
        if form.nfc_label.data != "":
        	current_user.nfc_label = form.nfc_label.data
        else:
        	current_user.nfc_label = None
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user', user_id = current_user.id))
    form.username.data = current_user.username
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.middle_name.data = current_user.middle_name
    form.nfc_label.data = current_user.nfc_label
    return render_template('edit_profile.html', form = form)

@main.route('/edit_profile_admin/<int:id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user = user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.middle_name = form.middle_name.data
        user.rate = form.rate.data
        user.role = Role.query.get(form.role.data)
        user.company = Company.query.get(form.company.data)
        if form.nfc_label.data != "":
        	user.nfc_label = form.nfc_label.data
        else:
        	user.nfc_label = None
        user.confirmed = form.confirmed.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('main.user', user_id = user.id))
    form.username.data = user.username
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.middle_name.data = user.middle_name
    form.rate.data = user.rate
    form.role.data = user.role_id
    form.company.data = user.company_id
    form.nfc_label.data = user.nfc_label
    form.confirmed.data = user.confirmed
    return render_template('edit_profile.html', form = form, user = user)

@main.route('/edit_profile/<int:id>', methods = ['GET', 'POST'])
@login_required
@admin_moderator_required
def edit_profile_moderator(id):
    user = User.query.get_or_404(id)
    if user.is_moderator() or user.is_administrator():
    	return abort(403)
    if user.company != current_user.company:
    	return abort(403)
    form = EditProfileModeratorForm(user = user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.middle_name = form.middle_name.data
        user.rate = form.rate.data
        user.role = Role.query.get(form.role.data)
        if form.nfc_label.data != "":
        	user.nfc_label = form.nfc_label.data
        else:
        	user.nfc_label = None
        user.confirmed = form.confirmed.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('main.user', user_id = user.id))
    form.username.data = user.username
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.middle_name.data = user.middle_name
    form.rate.data = user.rate
    form.role.data = user.role_id
    form.nfc_label.data = user.nfc_label
    form.confirmed.data = user.confirmed
    return render_template('edit_profile.html', form = form, user = user)

import time

class Profiler(object):
	def __enter__(self):
		self._startTime = time.time()

	def __exit__(self, type, value, traceback):
		print "Elepsed time : {:.3f} sec".format(time.time() - self._startTime)

@main.route('/my_company', methods = ['GET'])
@admin_moderator_required
def my_company():

########################################################################################################################

	# i = 0
	# while i < 10:
	# 	with Profiler() as p:
	# 		i += 1
	# 		page = request.args.get('page', 1, type = int)
	# 		week_titles, month_title = get_titles_for_employee_header(page)
	# 		company = current_user.company;
	# 		clear_times = {}
	# 		needed_count = 100
	# 		count = 1
	# 		for employee in company.users:
	# 			clear_times[employee.id] = TimeCache.get_cached_week_time(employee.id, page)
	# 			if count > needed_count:
	# 				break
	# 			else:
	# 				count += 1
	# 		count = 1
	# 		string_times = {}
	# 		delta_string_times = {}
	# 		for employee in company.users:
	# 			string_times[employee.id] = []
	# 			delta_string_times[employee.id] = []
	# 			for time in clear_times[employee.id]:
	# 				string_times[employee.id].append(get_work_time_string(time))
	# 				delta_string_times[employee.id].append(get_delta_work_time_string(time, employee.rate))
	# 			if count > needed_count:
	# 				break
	# 			else:
	# 				count += 1

########################################################################################################################

	page = request.args.get('page', 1, type = int)
	week_titles, month_title = get_titles_for_employee_header(page)
	company = current_user.company;
	clear_times = {}
	for employee in company.users:
		clear_times[employee.id] = TimeCache.get_cached_week_time(employee.id, page)
	string_times = {}
	delta_string_times = {}
	for employee in company.users:
		string_times[employee.id] = []
		delta_string_times[employee.id] = []
		for time in clear_times[employee.id]:
			string_times[employee.id].append(get_work_time_string(time))
			delta_string_times[employee.id].append(get_delta_work_time_string(time, employee.rate))
	return render_template('company.html', company = company, string_times = string_times, delta_string_times = delta_string_times, 
		month_title = month_title, week_titles = week_titles, pagination_url = "my_company?page=", page = page)

def get_work_time_string(time):
	value_hours = time // 60
	value_minutes = time % 60
	if value_minutes < 10:
		value_minutes = "0{}".format(value_minutes)
	return "{}:{}".format(value_hours, value_minutes)

def get_delta_work_time_string(time, rate):
	rate_in_minutes = rate * 60
	delta = rate_in_minutes - time
	good_work = delta < 0
	if good_work:
		delta *= -1
		sign = "+"
	else:
		sign = "-"
	delta_hours = delta // 60
	delta_minutes = delta % 60
	if delta_minutes < 10:
		delta_minutes = "0{}".format(delta_minutes)
	delta_string = "({}{}:{})".format(sign, delta_hours, delta_minutes)
	return [delta_string, good_work]

def get_titles_for_employee_header(month_page):
	current_day = datetime.now().date()
	first_day = TimeCache.get_first_day(current_day, 0, -month_page + 1)
	last_day = TimeCache.get_last_day(first_day)
	monday = first_day - timedelta(days = first_day.weekday())
	titles = []
	while monday <= last_day:
		sunday = monday + timedelta(days = 6)
		titles.append("{:02d}.{:02d} - {:02d}.{:02d}".format(monday.day, monday.month, sunday.day, sunday.month))
		monday = monday + timedelta(days = 7)
	month_title = first_day.strftime("%B %Y")
	return titles, month_title


@main.route('/company/<company_name>', methods = ['GET'])
@admin_required
def company(company_name):
	page = request.args.get('page', 1, type = int)
	week_titles, month_title = get_titles_for_employee_header(page)
	company = Company.query.filter_by(company_name = company_name).first_or_404()
	clear_times = {}
	for employee in company.users:
		clear_times[employee.id] = TimeCache.get_cached_week_time(employee.id, page)
	string_times = {}
	delta_string_times = {}
	for employee in company.users:
		string_times[employee.id] = []
		delta_string_times[employee.id] = []
		for time in clear_times[employee.id]:
			string_times[employee.id].append(get_work_time_string(time))
			delta_string_times[employee.id].append(get_delta_work_time_string(time, employee.rate))
	return render_template('company.html', company = company, string_times = string_times, delta_string_times = delta_string_times, 
		month_title = month_title, week_titles = week_titles, pagination_url = "{}?page=".format(company.company_name), page = page)

@main.route('/reset_password_request', methods = ['GET', 'POST'])
def reset_password_request():
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first_or_404()
		token = user.generate_confirmation_token()
		send_email(user.email, 'Reset your password', 'mail/reset_password', token = token, user = user)
		flash('Mail with special link has been send in your email address')
		return redirect(url_for('main.index'))
	return render_template('reset_password_request.html', form = form)

@main.route('/reset_password/<token>/<email>', methods = ['GET', 'POST'])
def reset_password(token, email):
	user = User.query.filter_by(email = email).first()
	if user is not None and user.confirm(token):
		form = SetPasswordForm()
		if form.validate_on_submit():
			user.password = form.password.data
			db.session.add(user)
			flash('Password has been updated')
			return redirect(url_for('auth.login'))
		return render_template('set_password.html', form = form)
	else:
		flash('The confirmation link is invalid or has expired')
		return redirect(url_for('main.index'))

@main.route('/user_add/<company_name>', methods = ['GET', 'POST'])
@admin_moderator_required
def user_add(company_name):
	form = NewUserForm()
	if form.validate_on_submit():
		user = User(email = form.email.data, first_name = form.first_name.data, last_name = form.last_name.data)
		user.password = form.password.data
		user.company = Company.query.filter_by(company_name = company_name).first()
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_email(user.email, 'New user registered', 'mail/new_user', token = token, user = user, password = form.password.data)
		flash('New user has been create')
		return redirect(url_for('main.index'))
	return render_template('user_add.html', form = form, company_name = company_name)

@main.route('/comfirm/<token>/<email>')
def confirm(token, email):
	if current_user.is_anonymous:
		user = User.query.filter_by(email = email).first()
		if user is not None:
			if user.confirmed:
				flash('You already confirmed your account')
				return redirect(url_for('main.index'))
			if user.confirm(token):
				flash('You have confirmed your account, thanks!')
				return redirect(url_for('main.index'))
			else:
				flash('The confirmation link is invalid or has expired')
				return redirect(url_for('main.index'))
		else:
			flash('User with email ',email,' not found')
			return redirect(url_for('main.index'))
	else:
		if current_user.email != email:
			flash('Email in this link is not much with current account')
			return redirect(url_for('main.index'))
		else:
			flash('You already confirmed your account')
			return redirect(url_for('main.index'))
	return redirect(url_for('main.index'))

@main.route('/send_confirmed_mail', methods = ['GET', 'POST'])
def send_confirmed_mail():
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first_or_404()
		token = user.generate_confirmation_token()
		send_email(user.email, 'Confirmed your account', 'mail/mail_with_confirmation_link', token = token, user = user)
		flash('Mail with special link has been send in your email address')
		return redirect(url_for('main.index'))
	return render_template('reset_password_request.html', form = form)

@main.route('/delete/company/<int:comp_id>', methods = ['GET', 'POST'])
def delete_company(comp_id):
	form = ConfirmDeleteDBEntityForm(current_user)
	if form.validate_on_submit():
		delete_company_with_id(comp_id)
		flash('Company has been deleted')
		return redirect(url_for('main.index'))
	return render_template('confirm_delete_company.html', form = form)

@main.route('/delete/user/<int:user_id>', methods = ['GET', 'POST'])
def delete_user(user_id):
	form = ConfirmDeleteDBEntityForm(current_user)
	if form.validate_on_submit():
		delete_user_with_id(user_id)
		flash('User has been deleted')
		return redirect(url_for('main.index'))
	return render_template('confirm_delete_user.html', form = form)

@main.route('/work_time_in_percent', methods = ['GET'])
@admin_moderator_required
def work_time_in_percent():
	page = request.args.get('page', 1, type = int)
	company = current_user.company;
	current_day = datetime.now().date()
	first_day = TimeCache.get_first_day(current_day, 0, -page + 1)
	time_dict = {}
	for user in company.users:
		time_dict[user.id] = []
		minutes = get_user_work_time_for_month_page(user.id, page)
		time_dict[user.id].append(format_full_time_string_from_minutes(minutes))
		minutes_in_day = float(user.rate) / 5 * 60
		work_day = work_days_count(first_day.year, first_day.month)
		full_minutes = work_day * minutes_in_day
		percent = float(minutes) / full_minutes * 100
		time_dict[user.id].append("{:.2f}%".format(percent))
		time_dict[user.id].append(format_full_time_string_from_minutes(full_minutes))
	month_title = first_day.strftime("%B %Y")
	work_days = work_days_count(first_day.year, first_day.month)
	return render_template('employees_and_work_in_percent.html', company = company, pagination_url = "work_time_in_percent?page=", page = page, 
		time_dict = time_dict, month_title = month_title, work_days = work_days)











