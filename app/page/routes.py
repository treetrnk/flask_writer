from flask import render_template, redirect
from app.page import bp
from app.models import Page, User, Tag
from app.page.forms import NewPageForm

@bp.route('/admin/add/page')
def add_page():
    form = NewPageForm()
    form.parent_id.choices = [(p.id, p.title) for p in Page.query.order_by('slug')]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.order_by('name')]
    form.user_id.choices = [(u.id, u.username) for u in User.query.order_by('username')]
    return render_template('page/edit.html', form=form, tab='pages')

@bp.route('/<path:path>')
def index():
    page = Page.query.filter(
        Page.path + "/" + Page.slug == path
    ).first()
    if page:
        render_template(f'pages/{page.type}', page=page)    
    return redirect(url_for('main.index'))
