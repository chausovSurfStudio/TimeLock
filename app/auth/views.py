from flask import redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required, current_user
from . import auth
from app import db
from app.model import User
from .forms import LoginForm, ChangePasswordForm
from app.timelock_utils import render_template

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()

@auth.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if not user:
            flash('Unknown email')
            return render_template('auth/login.html', form = form)
        if not user.confirmed:
            flash('First, you have to verify your account. Click on the link in your mail.')
            return redirect(url_for('main.index'))
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form = form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/change_password', methods = ['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.password.data
        db.session.add(current_user)
        db.session.commit()
        login_user(current_user)
        flash('Password has been reset')
        return redirect(url_for('main.index'))
    return render_template('auth/change_password.html', form = form)