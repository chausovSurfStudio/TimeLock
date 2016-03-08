from flask import render_template, redirect, url_for, flash
from flask.ext.login import login_required, current_user
from . import main
from app import db
from app.model import User, Company, Role
from app.decorators import admin_required
from forms import NewCompanyForm, SetPasswordForm, EditProfileForm
from app.email import send_email

@main.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('index.html')

@admin_required
@main.route('/new_company', methods = ['GET', 'POST'])
def new_company():
	form = NewCompanyForm()
	if form.validate_on_submit():
		company = Company(company_name = form.name.data)
		db.session.add(company)
		db.session.commit()
		user = User.query.filter_by(email = form.email.data).first()
		if user is None:
			user = User(email = form.email.data)
		moderator_role = Role.query.filter_by(name = 'Moderator').first()
		user.role = moderator_role
		user.company = company
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_email(user.email, 'Confirm Your Account', 'mail/confirm_moderator', company_name = company.company_name, token = token, email = form.email.data)
		flash('You create new company, message to moderator has been sent')
		return redirect(url_for('main.index'))
	return render_template('new_company.html', form = form)

@admin_required
@main.route('/companies', methods = ['GET'])
def companies():
	companies = Company.query.order_by(Company.company_name).all()
	return render_template('companies.html', companies = companies)

@admin_required
@main.route('/clear_companies', methods = ['GET', 'POST'])
def clear_companies():
	Company.query.delete()
	return redirect(url_for('main.index'))

@admin_required
@main.route('/clear_users', methods = ['GET', 'POST'])
def clear_users():
	User.query.delete()
	return redirect(url_for('main.index'))

@main.route('/confirm_moderator/<token>/<email>/<company_name>', methods = ['GET', 'POST'])
def confirm_moderator(token, email, company_name):
	if current_user.is_anonymous:
		user = User.query.filter_by(email = email).first()
		if user is not None:
			if user.confirmed and not user.password_is_empty():
				flash('You already confirmed your account')
				return redirect(url_for('main.index'))
			if user.confirm(token):
				flash('You have confirmed your account, thanks! Please, set new password')
				return redirect(url_for('main.set_password', email = email, company_name = company_name))
			else:
				flash('The confirmation link is invalid or has expired')
				return redirect(url_for('main.index'))
		else:
			flash('User with email ',email,' not found')
			return redirect(url_for('main.index'))
	else:
		if current_user.confirmed:
			return redirect(url_for('main.index'))
		if current_user.email != email:
			flash('Email in this link is not mutch with current account')
			return redirect(url_for('main.index'))
	return redirect(url_for('main.index'))

@main.route('/set_password/<email>/<company_name>', methods = ['GET', 'POST'])
def set_password(email, company_name):
	user = User.query.filter_by(email = email).first()
	form = SetPasswordForm()
	if form.validate_on_submit():
		user.password = form.password.data
		db.session.add(user)
		db.session.commit()
		return redirect(url_for('main.index'))
	return render_template('set_password.html', form = form, email = email, company_name = company_name)

@main.route('/user/<int:user_id>')
@login_required
def user(user_id):
    user = User.query.filter_by(id = user_id).first_or_404()
    return render_template('user.html', user=user)

@main.route('/edit_profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
    	current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.middle_name = form.middle_name.data
        current_user.nfc_label = form.nfc_label.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('main.user', user_id = current_user.id))
    form.username.data = current_user.username
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.middle_name.data = current_user.middle_name
    form.nfc_label.data = current_user.nfc_label
    return render_template('edit_profile.html', form = form)


@main.route('/edit-profile/<int:id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)



