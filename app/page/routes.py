from flask import render_template, redirect, url_for, flash
from app.page import bp
from app.models import Page

@bp.route('/<path:path>')
def index(path):
    page = Page.query.filter(
        Page.path + "/" + Page.slug == path
    ).first()
    if page:
        render_template(f'pages/{page.type}', page=page)    
    flash("Passed through catchall route!", "warning")
    return redirect(url_for('main.home'))
