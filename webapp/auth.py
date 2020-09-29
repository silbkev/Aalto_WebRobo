import os
import signal
import subprocess
import time
from webapp import db
from flask import current_app, Blueprint, render_template, Response, redirect, request, url_for, flash, abort, jsonify
from flask_login import login_user, login_required, logout_user
from webapp.models import User, Measurement, Setting
from webapp.forms import LoginForm, RegistrationForm
from sqlalchemy.orm import sessionmaker

bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
    static_folder="static",
    static_url_path="/static",
)

# Logout and Stop Robot Process
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    with current_app.app_context():
        current_app.config['ROBOT'].stop()
    flash('You logged out!')
    return redirect(url_for('general.index', clear = True))

# Login User and check authorization
@bp.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        # Grab the user from our User Models table
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            # Log in the user
            if user.check_password(form.password.data) and user is not None:
                login_user(user)
                flash('Logged in successfully.')
                next = request.args.get('next')
                if next == None or not next[0] == '/':
                    next = url_for('robot.dashboard')
                return redirect(next)
        flash("Invalid username, please try again or register an account.")
    return render_template('login.html', form=form)

# Register User
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data,
                    password=form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('Thanks for registering! Now you can login!')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)
