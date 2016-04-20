import flask
from datetime import datetime, timedelta
from app.model import Checkin
from sqlalchemy import desc
from flask.ext.login import current_user

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
	query = Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(today, tomorrow)).order_by(desc(Checkin.time))
	checkin = query.first()
	if query.count() % 2 == 1:
		return checkin
	else:
		return None