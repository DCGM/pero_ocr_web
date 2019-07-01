from flask import Blueprint, render_template, redirect, url_for, request, flash
from server import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['Post'])
def signup_post():
    email = request.form.get('registerEmail')
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    password = request.form.get('registerPassword')
    institution = request.form.get('institution')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists!')
        return render_template('index.html')

    new_user = User(email, generate_password_hash(password), first_name, last_name, institution)

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('main.profile'))


@auth.route('/logout')
def logout():
    return 'Logout'
