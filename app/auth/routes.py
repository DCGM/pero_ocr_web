from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from flask import flash, redirect, url_for, render_template
from flask_login import login_user, logout_user, login_required
from app.db.general import get_user_by_email
from app.auth.general import create_user, check_user


@bp.route('/signup', methods=['GET', 'Post'])
def signup_post():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)

        if user:
            flash('Email address already exists!')
            return render_template('forms/signup.html', form=form)

        if form.password.data != form.password2.data:
            flash('Passwords are not same!')
            return render_template('forms/signup.html', form=form)

        new_user = create_user(form.email.data, form.password.data, form.first_name.data, form.last_name.data, form.institution.data)

        login_user(new_user, remember=True)

        return redirect(url_for('document.documents'))
    else:
        return render_template('forms/signup.html', form=form)


@bp.route('/login', methods=['Post'])
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        user = check_user(form.email.data, form.password.data)

        if not user:
            flash('Please check your login details and try again.')
            return redirect(url_for('main.index'))

        login_user(user, remember=True)
        return redirect(url_for('document.documents'))
    else:
        return render_template('index.html', form_login=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))