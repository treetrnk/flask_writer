from flask import render_template, redirect, flash, url_for
from app import db
from app.admin import bp
from app.models import Page, User, Tag
from app.admin.forms import AddUserForm, AddPageForm, AddTagForm 
from flask_login import login_required

@bp.route('/admin/users')
@login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', tab='users', users=users)

@bp.route('/admin/user/add', methods=['GET', 'POST'])
@login_required
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
    return render_template('admin/user-edit.html', form=form, tab='users')

@bp.route('/admin/pages')
@login_required
def pages():
    pages = Page.query.all()
    return render_template('admin/pages.html', tab='pages', pages=pages)

@bp.route('/admin/page/add', methods=['GET', 'POST'])
@login_required
def add_page():
    form = AddPageForm()
    if form.validate_on_submit():
        page = Page(
                title = form.title.data,
                slug = form.slug.data,
                template = form.template.data,
                parent_id = form.parent_id.data,
                banner = form.banner.data,
                body = form.body.data,
                summary = form.summary.data,
                sidebar = form.sidebar.data,
                #tags = form.tags.data,
                user_id = form.user_id.data,
                pub_date = form.pub_date.data,
                published = form.published.data,
            )
        db.session.add(page)
        db.session.commit()
        flash("Page added successfully.", "success")
        return redirect(url_for('admin.pages'))
    form.parent_id.choices = [(p.id, p.title) for p in Page.query.order_by('slug')]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.order_by('name')]
    form.user_id.choices = [(u.id, u.username) for u in User.query.order_by('username')]
    return render_template('admin/page-edit.html', form=form, tab='pages')

@bp.route('/admin/tags')
@login_required
def tags():
    tags = Tag.query.all()
    return render_template('admin/tags.html', tab='tags', tags=tags)

@bp.route('/admin/tag/add', methods=['GET', 'POST'])
@login_required
def add_tag():
    form = AddTagForm()
    if form.validate_on_submit():
        if form.validate_tag(form.name.data):
            tag = Tag(
                    name=form.name.data
                )
            db.session.add(tag)
            db.session.commit()
            flash("Tag added successfully.", "success")
            return redirect(url_for('admin.tags'))
    return render_template('admin/tag-edit.html', form=form, tab='tags')

