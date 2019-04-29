from flask import render_template, redirect, url_for, flash
from app.page import bp
from app.models import Page

@bp.route('/')
def index():
    page = Page.query.filter_by(path='/home',published=True).first()
    if page:
        return render_template(f'page/{page.template}.html', page=page)
    return render_template('home.html', page='page')

@bp.route('/<path:path>')
def catch_all(path):
    path = f"/{path}"
    page = Page.query.filter_by(path=path,published=True).first()
    print(f"path: {path}")
    print(f"page: {page}")
    if page:
        return render_template(f'page/{page.template}.html', page=page)    
    return redirect(url_for('page.index'))
