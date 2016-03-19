from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.model import User, Checkin

class CheckinWithCurrentTimeForm(Form):
    submit = SubmitField('Checkin with current time')



