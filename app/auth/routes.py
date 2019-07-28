from app.auth import bp
from app.auth.forms import LoginForm
from flask import request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required
from app.db.general import get_user_by_email
from app.auth.general import create_user, check_user


@bp.route('/signup', methods=['Post'])
def signup_post():
    email = request.form.get('registerEmail')
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    password = request.form.get('registerPassword')
    repeatPassword = request.form.get('registerRepeatPassword')
    institution = request.form.get('institution')

    user = get_user_by_email(email)

    if user:
        flash('Email address already exists!')
        return redirect(url_for('main.index'))

    if password != repeatPassword:
        flash('Password and Repeat Password must be same!')
        return redirect(url_for('main.index'))

    new_user = create_user(email, password, first_name, last_name, institution)

    login_user(new_user, remember=True)

    return redirect(url_for('document.documents'))


@bp.route('/login', methods=['Post'])
def login_post():
    email = request.form.get('Email')
    password = request.form.get('Password')

    user = check_user(email, password)

    if not user:
        flash('Please check your login details and try again.')
        return redirect(url_for('main.index'))

    login_user(user, remember=True)

    return redirect(url_for('document.documents'))


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))