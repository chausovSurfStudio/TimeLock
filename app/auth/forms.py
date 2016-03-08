from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.model import User
from flask.ext.login import current_user


class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class ChangePasswordForm(Form):
    oldPassword = PasswordField('Old password', validators = [Required()])
    password = PasswordField('New password', validators = [Required(), EqualTo('password2', message = 'Passwords must much')])
    password2 = PasswordField('Confirm new password', validators = [Required()])
    submit = SubmitField('Change password')

    def validate_oldPassword(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('You must input old password there')