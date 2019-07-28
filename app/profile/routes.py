from app.profile import bp
from flask_login import login_required
from flask import render_template


@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
