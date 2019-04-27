from app.auth import bp
from flask import flash, redirect, render_template, url_for
from app import db
from app.auth.forms import AddUserForm
from app.models import User

@bp.route('/admin/add/user', methods=['GET', 'POST'])
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        user = User(
                username=form.username.data, 
                email=form.email.data,
                about_me=form.about_me.data,
            )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"{user.username.upper()} was added successfully!", "success")
        return redirect(url_for('main.home'))
    return render_template('auth/edit.html', form=form, tab='users')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
