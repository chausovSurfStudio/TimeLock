from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.model import Company, User, Role

class NewCompanyForm(Form):
    name = StringField('Company name', validators = [Required(), Length(1, 64)])
    email = StringField('Moderator email', validators = [Required(), Length(1, 64), Email()])
    password = StringField('Password', validators = [Required(), Length(1, 64)])
    first_name = StringField('First Name', validators = [Length(1, 64)])
    last_name = StringField('Last Name', validators = [Length(1, 64)])
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

class EditProfileAdminForm(Form):
    username = StringField('Username', validators = [Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
    first_name = StringField('First Name', validators = [Length(0, 64)])
    last_name = StringField('Last Name', validators = [Length(0, 64)])
    middle_name = StringField('Middle Name', validators = [Length(0, 64)])
    nfc_label = StringField('NFC-label', validators = [Length(0, 64)])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce = int)
    company = SelectField('Company', coerce = int)
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.company.choices = [(company.id, company.company_name) for company in Company.query.order_by(Company.company_name).all()]
        self.user = user

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username = field.data).first():
            raise ValidationError('Username already in use')

    def validate_nfc_label(self, field):
        if field.data != self.user.nfc_label and User.query.filter_by(nfc_label = field.data).first():
            raise ValidationError('NFC label already in use')

class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
    submit = SubmitField('Send mail to reset password')

    def validate_email(self, field):
        user = User.query.filter_by(email = field.data).first()
        if not user:
            raise ValidationError('Specified address is not registered')

class NewUserForm(Form):
    email = StringField('User email', validators = [Required(), Length(1, 64), Email()])
    password = StringField('Password', validators = [Required(), Length(1, 64)])
    first_name = StringField('First Name', validators = [Length(1, 64)])
    last_name = StringField('Last Name', validators = [Length(1, 64)])
    submit = SubmitField('Submit')

    def validate_email(self, field):
        user = User.query.filter_by(email = field.data).first()
        if user is not None:
            raise ValidationError('Email already registered')



