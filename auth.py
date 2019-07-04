from flask import Blueprint, render_template, redirect, url_for, request, flash
from server import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required

auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['Post'])
def signup_post():
    email = request.form.get('registerEmail')
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    password = request.form.get('registerPassword')
    repeatPassword = request.form.get('registerRepeatPassword')
    institution = request.form.get('institution')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists!')
        return redirect(url_for('main.index'))

    if password != repeatPassword:
        flash('Password and Repeat Password must be same!')
        return redirect(url_for('main.index'))


    new_user = User(email, generate_password_hash(password), first_name, last_name, institution)

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('main.index'))

@auth.route('/login', methods=['Post'])
def login_post():
    email = request.form.get('loginEmail')
    password = request.form.get('loginPassword')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.')
        return redirect(url_for('main.index'))

    login_user(user, remember=True)

    return redirect(url_for('main.browser'))


@auth.route('/logout')
# @login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
