from flask import render_template
from app.main import bp

@bp.route('/')
def home():
    return render_template('home.html', page='page')
