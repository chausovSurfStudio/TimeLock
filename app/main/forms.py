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

class EditProfileForm(Form):
    username = StringField('Username', validators = [Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
    first_name = StringField('First Name', validators = [Length(0, 64)])
    last_name = StringField('Last Name', validators = [Length(0, 64)])
    middle_name = StringField('Middle Name', validators = [Length(0, 64)])
    nfc_label = StringField('NFC-label', validators = [Length(0, 64)])
    submit = SubmitField('Submit')