from flask import render_template, redirect, url_for, flash
from app.page import bp
from app.models import Page

@bp.route('/<path:path>')
def index(path):
    path = f"/{path}"
    page = Page.query.filter_by(path=path).first()
    print(f"path: {path}")
    print(f"page: {page}")
    if page:
        return render_template(f'page/{page.template}.html', page=page)    
    return redirect(url_for('main.home'))
