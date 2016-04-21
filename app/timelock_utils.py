import flask
from app import db
from datetime import datetime, timedelta
from app.model import Checkin
from sqlalchemy import desc
from flask.ext.login import current_user
from app.model import User, Company, Checkin, TimeCache, Post

def render_template(tmpl_name, **kwargs):
	checkin = get_last_checkin_in_current_day()
	current_work_time = None
	if checkin is not None:
		hours = checkin.time.hour
		minutes = checkin.time.minute
		current_work_time = hours * 60 + minutes
	return flask.render_template(tmpl_name, current_work_time = current_work_time, **kwargs)

def get_last_checkin_in_current_day():
	today = datetime.now().date()
	tomorrow = today + timedelta(days = 1)
	if not current_user.is_authenticated:
		return None
	query = Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(today, tomorrow)).order_by(desc(Checkin.time))
	checkin = query.first()
	if query.count() % 2 == 1:
		return checkin
	else:
		return None

def delete_company_with_id(company_id):
	company = Company.query.filter_by(id = company_id).first_or_404()
	for user in company.users:
		delete_user_with_id(user.id)
	db.session.delete(company)

def delete_user_with_id(user_id):
	user = User.query.filter_by(id = user_id).first_or_404()
	for checkin in user.checkins:
		delete_checkin_with_id(checkin.id)
	for time_cache in user.timeCaches:
		delete_time_cach_with_id(time_cache.id)
	for post in user.posts:
		delete_post_with_id(post.id)
	db.session.delete(user)

def delete_time_cach_with_id(timecach_id):
	time_cach = TimeCache.query.filter_by(id = timecach_id).first_or_404()
	db.session.delete(time_cach)

def delete_checkin_with_id(checkin_id):
	checkin = Checkin.query.filter_by(id = checkin_id).first_or_404()
	db.session.delete(checkin)

def delete_post_with_id(post_id):
	post = Post.query.filter_by(id = post_id).first_or_404()
	db.session.delete(post)

