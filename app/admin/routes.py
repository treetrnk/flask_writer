from flask import render_template, redirect, flash, url_for
from app import db
from app.admin import bp
from app.models import Page, User, Tag, PageVersion, Subscriber
from app.admin.forms import AddUserForm, AddPageForm, AddTagForm, EditUserForm 
from flask_login import login_required, current_user
from sqlalchemy import desc
import pytz

@bp.route('/admin/users')
@login_required
def users():
    page = Page.query.filter_by(slug='admin').first()
    users = User.query.order_by('username')
    return render_template('admin/users.html', tab='users', users=users, page=page)

@bp.route('/admin/user/add', methods=['GET', 'POST'])
@login_required
def add_user():
    page = Page.query.filter_by(slug='home').first()
    form = AddUserForm()
    form.timezone.choices = [(t, t) for t in pytz.common_timezones]
    if form.validate_on_submit():
        user = User(
                username=form.username.data, 
                email=form.email.data,
                about_me=form.about_me.data,
                timezone=form.timezone.data,
            )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"{user.username.upper()} was added successfully!", "success")
        return redirect(url_for('admin.users'))
    return render_template('admin/user-edit.html', form=form, tab='users', action='Add', page=page)

@bp.route('/admin/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    page = Page.query.filter_by(slug='admin').first()
    user = User.query.filter_by(id=id).first()
    form = EditUserForm()
    form.timezone.choices = [(t, t) for t in pytz.common_timezones]
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.about_me = form.about_me.data
        user.timezone = form.timezone.data
        if form.password.data and user.check_password(form.password.data):
            user.set_password(form.new_password.data)
        db.session.commit()
        flash(f"User {user.username} was updated successfully!", "success")
        return redirect(url_for('admin.users'))
    form.username.data = user.username
    form.email.data = user.email
    form.about_me.data = user.about_me
    form.timezone.data = user.timezone
    return render_template('admin/user-edit.html', form=form, tab='users', action='Edit', user=user,page=page)

@bp.route('/admin/pages')
@login_required
def pages():
    page = Page.query.filter_by(slug='admin').first()
    Page.set_nav()
    pub_pages = Page.query.filter_by(published=True).order_by('dir_path','sort','title')
    unpub_pages = Page.query.filter_by(published=False).order_by('dir_path','sort','title')
    return render_template('admin/pages.html', tab='pages', pub_pages=pub_pages, unpub_pages=unpub_pages,page=page)

@bp.route('/admin/page/add', methods=['GET', 'POST'])
@login_required
def add_page():
    form = AddPageForm()
    for field in form:
        print(f"{field.name}: {field.data}")
    form.parent_id.choices = [(0,'---')] + [(p.id, f"{p.title} ({p.path})") for p in Page.query.all()]
    form.user_id.choices = [(u.id, u.username) for u in User.query.all()]
    if form.validate_on_submit():
        parentid = form.parent_id.data if form.parent_id.data else None
        page = Page(
                title = form.title.data,
                slug = form.slug.data,
                template = form.template.data,
                parent_id = parentid,
                banner = form.banner.data,
                body = form.body.data,
                summary = form.summary.data,
                sidebar = form.sidebar.data,
                tags = form.tags.data,
                user_id = current_user.id,
                published = form.published.data,
            )
        pdate = form.pub_date.data
        ptime = form.pub_time.data
        local_tz = form.timezone.data if form.timezone.data else current_user.timezone
        if pdate and ptime:
            page.set_local_pub_date(f"{pdate} {ptime}", local_tz)
        page.set_path()
        db.session.add(page)
        db.session.commit()
        Page.set_nav()
        flash("Page added successfully.", "success")
        return redirect(url_for('admin.pages'))
    if form.errors:
        flash("<b>Error!</b> Please fix the errors below.", "danger")
    return render_template('admin/page-edit.html', 
            form=form, 
            tab='pages',
            action='Add',
            page = Page.query.filter_by(slug='admin').first()
        )

@bp.route('/admin/page/edit/<int:id>', methods=['GET', 'POST'])
@bp.route('/admin/page/edit/<int:id>/version/<int:ver_id>', methods=['GET', 'POST'])
@login_required
def edit_page(id, ver_id=None):
    page = Page.query.filter_by(id=id).first()
    print(f"ANCESTORS: {page.ancestors()}")
    for anc in page.ancestors():
        print(f"ANCESTOR: {anc}")
    form = AddPageForm()
    form.parent_id.choices = [(0,'---')] + [(p.id, f"{p.title} ({p.path})") for p in Page.query.all()]
    form.user_id.choices = [(u.id, u.username) for u in User.query.all()]
    for field in form:
        print(f"{field.name}: {field.data}")
    if form.validate_on_submit():
        
        prev_parentid = page.parent_id if page.parent_id else None
        # Create version from current
        version = PageVersion(
            original_id = id,
            title = page.title,
            slug = page.slug,
            template = page.template,
            parent_id = prev_parentid,
            banner = page.banner,
            body = page.body,
            summary = page.summary,
            sidebar = page.sidebar,
            tags = page.tags,
            user_id = page.user_id,
            pub_date = page.pub_date,
            published = page.published,
            path = page.path,
            dir_path = page.dir_path,
        )
        db.session.add(version)

        # Update page
        parentid = form.parent_id.data if form.parent_id.data else None
        page.title = form.title.data
        page.slug = form.slug.data
        page.template = form.template.data
        page.parent_id = parentid
        page.banner = form.banner.data
        page.body = form.body.data
        page.summary = form.summary.data
        page.sidebar = form.sidebar.data
        page.tags = form.tags.data
        page.user_id = form.user_id.data
        page.published = form.published.data

        pdate = form.pub_date.data
        ptime = form.pub_time.data
        local_tz = form.timezone.data if form.timezone.data else current_user.timezone
        if pdate and ptime:
            page.set_local_pub_date(f"{pdate} {ptime}", local_tz)
        page.set_path()
        db.session.commit()
        Page.set_nav()
        flash("Page updated successfully.", "success")
    if form.errors:
        flash("<b>Error!</b> Please fix the errors below.", "danger")
    versions = PageVersion.query.filter_by(original_id=id).order_by(desc('edit_date')).all()
    version = PageVersion.query.filter_by(id=ver_id).first() if ver_id else None
    if version:
        form.title.data = version.title
        form.slug.data = version.slug
        form.template.data = version.template
        form.parent_id.data = version.parent_id 
        form.banner.data = version.banner
        form.body.data = version.body
        form.summary.data = version.summary
        form.sidebar.data = version.sidebar
        form.tags.data = version.tags
        form.user_id.data = version.user_id
        form.pub_date.data = version.local_pub_date(current_user.timezone)
        form.pub_time.data = version.local_pub_date(current_user.timezone)
        form.published.data = version.published
    else:
        form.title.data = page.title
        form.slug.data = page.slug
        form.template.data = page.template
        form.parent_id.data = page.parent_id 
        form.banner.data = page.banner
        form.body.data = page.body
        form.summary.data = page.summary
        form.sidebar.data = page.sidebar
        form.tags.data = page.tags
        form.user_id.data = page.user_id
        form.pub_date.data = page.local_pub_date(current_user.timezone)
        form.pub_time.data = page.local_pub_date(current_user.timezone)
        form.published.data = page.published
    return render_template('admin/page-edit.html', 
            form=form, 
            tab='pages', 
            action='Edit',
            edit_page=page,
            versions=versions,
            version=version,
            page = Page.query.filter_by(slug='admin').first()
        )


@bp.route('/admin/tags')
@login_required
def tags():
    page = Page.query.filter_by(slug='admin').first()
    tags = Tag.query.order_by('name')
    return render_template('admin/tags.html', tab='tags', tags=tags, page=page)

@bp.route('/admin/tag/add', methods=['GET', 'POST'])
@login_required
def add_tag():
    page = Page.query.filter_by(slug='admin').first()
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
    return render_template('admin/tag-edit.html', form=form, tab='tags', action='Add', page=page)

@bp.route('/admin/tag/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tag(id):
    page = Page.query.filter_by(slug='admin').first()
    tag = Tag.query.filter_by(id=id).first()
    form = AddTagForm()
    if form.validate_on_submit():
        if form.validate_tag(form.name.data, id):
            tag.name = form.name.data
            db.session.commit()
            flash("Tag updated successfully.", "success")
            return redirect(url_for('admin.tags'))
        else:
            flash("<b>Error!</b> That tag already exists.", "danger")
    form.name.data = tag.name
    return render_template('admin/tag-edit.html', form=form, tab='tags', tag=tag, action='Edit', page=page)

@bp.route('/admin/subscribers')
@login_required
def subscribers():
    page = Page.query.filter_by(slug='admin').first()
    subscribers = Subscriber.query.order_by('email').all()
    return render_template('admin/subscribers.html', tab='subscribers', subscribers=subscribers, page=page)

