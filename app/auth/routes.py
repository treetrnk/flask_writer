from app.auth import bp

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
