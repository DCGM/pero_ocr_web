from flask import Blueprint, render_template, redirect, url_for, request
from server import db
from flask_login import current_user, login_required

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.browser'))
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/browser')
@login_required
def browser():
    return render_template('browser.html')

@main.route('/document/new', methods=['GET', 'POST'])
@login_required
def new_document():
    if request.method == 'POST':
        return redirect(url_for('main.browser'))
    else:
        return render_template('new_document.html')
