from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.model import User, Checkin
from datetime import datetime

class CheckinWithCurrentTimeForm(Form):
    submit = SubmitField('Checkin with current time')

class CheckinCustomTimeForm(Form):
	hours = StringField('Hours', validators = [Required(), Length(1, 2)])
	minutes = StringField('Minutes', validators = [Required(), Length(1, 2)])
	day = StringField('Day', validators = [Required(), Length(1, 2)])
	month = SelectField('Month', coerce = int)
	year = SelectField('Year', coerce = int)
	submit = SubmitField('Checkin')

	def __init__(self, *args, **kwargs):
		super(CheckinCustomTimeForm, self).__init__(*args, **kwargs)
		month_choices = []
		year_choices = []
		current_year = datetime.now().date().year
		febrary_day = 28
		if current_year % 4 == 0:
			febrary_day = 29
		self.days_and_month = [('January', 31), ('Febrary', febrary_day), ('March', 31), ('April', 30), ('May', 31), ('June', 30), 
						('July', 31), ('August', 31), ('September', 30), ('October', 31), ('November', 30), ('December', 31)]
		i = 0
		for item in self.days_and_month:
			month_choices.append((i, item[0]))
			i += 1
		i = 0
		while current_year - i >= 2015:
			year_choices.append((i, current_year - i))
			i += 1
		self.month.choices = month_choices
		self.year.choices = year_choices

	def validate_day(self, field):
		if not field.data.isdigit():
			raise ValidationError('You must input number of day there, not string')
		digit = int(field.data)
		day_in_selected_month = self.days_and_month[self.month.data][1]
		if digit > day_in_selected_month or digit < 1:
			raise ValidationError('This day not exists in selected month')

	def validate_hours(self, field):
		if not field.data.isdigit():
			raise ValidationError('You must input number of hours there, between 0 - 23')
		digit = int(field.data)
		if digit > 23 or digit < 0:
			raise ValidationError('Wrong value, it takes value in range 0 - 23 ')

	def validate_minutes(self, field):
		if not field.data.isdigit():
			raise ValidationError('You must input number of minutes there, between 0 - 59')
		digit = int(field.data)
		if digit > 59 or digit < 0:
			raise ValidationError('Wrong value, it takes value in range 0 - 59 ')



