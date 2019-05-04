from flask import render_template, redirect, url_for, flash, session, request, current_app
from app.page import bp
from app.models import Page

@bp.route('/')
def home():
    page = Page.query.filter_by(path='/home',published=True).first()
    if page:
        return render_template(f'page/{page.template}.html', page=page)
    return render_template('home.html', page='page')

@bp.route('/set-theme')
@bp.route('/set-theme/<string:theme>')
def set_theme(theme=None):
    if theme:
        session['theme'] = theme
    elif 'theme' in session and session['theme'] == 'dark':
        session['theme'] = 'light'
    else:
        session['theme'] = 'dark'
    prev_path = request.args['path']
    if prev_path:
        return redirect(prev_path)
    return redirect(url_for('page.home'))

@bp.route('/<path:path>')
def index(path):
    path = f"/{path}"
    page = Page.query.filter_by(path=path).first()
    print(f"path: {path}")
    print(f"page: {page}")
    if page:
        code = request.args['code'] if 'code' in request.args else None
        if page.published or page.check_view_code(code):
            return render_template(f'page/{page.template}.html', page=page)    
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page)    

@bp.before_app_first_request
def set_nav():
    Page.set_nav()
