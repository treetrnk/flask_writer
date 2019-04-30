from flask import render_template, redirect, url_for, flash, session, request
from app.page import bp
from app.models import Page

@bp.route('/')
def home():
    page = Page.query.filter_by(path='/home',published=True).first()
    if page:
        return render_template(f'page/{page.template}.html', page=page)
    return render_template('home.html', page='page')

@bp.route('/set-theme/<string:theme>')
def set_theme(theme):
    session['theme'] = theme
    prev_path = request.args['path']
    if prev_path:
        return redirect(prev_path)
    return redirect(url_for('page.home'))

@bp.route('/<path:path>')
def index(path):
    path = f"/{path}"
    page = Page.query.filter_by(path=path,published=True).first()
    print(f"path: {path}")
    print(f"page: {page}")
    if page:
        return render_template(f'page/{page.template}.html', page=page)    
    return redirect(url_for('page.index'))
