from flask import render_template, redirect, flash, url_for
from app import db
from app.admin import bp
from app.models import Page, User, Tag
from app.admin.forms import AddUserForm, AddPageForm, AddTagForm 
from flask_login import login_required, current_user

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
    #for field in form:
    #    print(f"{field.name}: {field.data}")
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
                tags = form.tags.data,
                user_id = current_user.id,
                pub_date = form.pub_date.data,
                published = form.published.data,
            )
        page.set_path()
        db.session.add(page)
        db.session.commit()
        flash("Page added successfully.", "success")
        return redirect(url_for('admin.pages'))
    if form.errors:
        flash("<b>Error!</b> Please fix the errors below.", "danger")
    return render_template('admin/page-edit.html', 
            form=form, 
            tab='pages',
            action='Edit'
        )

@bp.route('/admin/page/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_page(id):
    edit_page = Page.query.filter_by(id=id).first()
    form = AddPageForm()
    
    if form.validate_on_submit():
        edit_page.title = form.title.data
        edit_page.slug = form.slug.data
        edit_page.template = form.template.data
        edit_page.parent_id = form.parent_id.data
        edit_page.banner = form.banner.data
        edit_page.body = form.body.data
        edit_page.summary = form.summary.data
        edit_page.sidebar = form.sidebar.data
        edit_page.tags = form.tags.data
        edit_page.user_id = form.user_id.data
        edit_page.pub_date = form.pub_date.data
        edit_page.published = form.published.data
        db.session.commit()
        flash("Page updated successfully.", "success")
        return redirect(url_for('admin.pages'))
    if form.errors:
        flash("<b>Error!</b> Please fix the errors below.", "danger")
    form.title.data = edit_page.title
    form.slug.data = edit_page.slug
    form.template.data = edit_page.template
    form.parent_id.data = edit_page.parent_id
    form.banner.data = edit_page.banner
    form.body.data = edit_page.body
    form.summary.data = edit_page.summary
    form.sidebar.data = edit_page.sidebar
    form.tags.data = edit_page.tags
    form.user_id.data = edit_page.user_id
    form.pub_date.data = edit_page.pub_date
    form.published.data = edit_page.published
    return render_template('admin/page-edit.html', 
            form=form, 
            tab='pages', 
            action='Edit',
        )


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
        else:
            flash("<b>Error!</b> That tag already exists.", "danger")
    return render_template('admin/tag-edit.html', form=form, tab='tags')

