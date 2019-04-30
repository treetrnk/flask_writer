from app.auth import bp
from flask import flash, redirect, render_template, url_for
from app import db
from app.models import User
from app.auth.forms import LoginForm
from flask_login import current_user, login_user, logout_user

@bp.route('/admin', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.pages'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user)
        flash("You have logged in successfully!", "success")
        return redirect(url_for("admin.pages"))
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('page.home'))
