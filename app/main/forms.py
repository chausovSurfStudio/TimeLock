from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.model import Company, User

class NewCompanyForm(Form):
    name = StringField('Company name', validators = [Required(), Length(1, 64)])
    email = StringField('Moderator email', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField('Create Company')

    def validate_email(self, field):
    	user = User.query.filter_by(email = field.data).first()
        if user is not None and user.confirmed == True:
            raise ValidationError('Email already registered')

    def validate_name(self, field):
        if Company.query.filter_by(company_name = field.data).first():
            raise ValidationError('Company name already in use')

class SetPasswordForm(Form):
	password = PasswordField('Password', validators = [Required(), EqualTo('password2', message = 'Passwords must much')])
	password2 = PasswordField('Confirm password', validators = [Required()])
	submit = SubmitField('Register')