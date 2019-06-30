from flask import Blueprint, render_template, redirect, url_for, request, flash
from server import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/signup')
def signup():
    return render_template('signup.html')


@auth.route('/signup', methods=['Post'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists!')
        return redirect(url_for('auth.signup'))
    
    new_user = User(email, generate_password_hash(password), name)

    db.session.add(new_user)
    db.session.commit()
    
    return redirect(url_for('auth.login'))


@auth.route('/logout')
def logout():
    return 'Logout'
