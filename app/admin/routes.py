import pytz
import re
import os
from flask import render_template, redirect, flash, url_for, send_from_directory, current_app, request
from app import db
from app.admin import bp
from app.admin.functions import log_new, log_change, to_utc_date, to_local_tz_date
from app.admin.forms import (
        AddUserForm, AddPageForm, AddTagForm, EditUserForm, DefinitionEditForm, 
        EmailForm, LinkEditForm, ProductEditForm, RecordForm, RecordEditForm,
        SendProductForm, CategoryEditForm, FileUploadForm, CommentEditForm
    )
from app.admin.generic_views import SaveObjView, DeleteObjView
from app.models import (
        Page, User, Tag, PageVersion, Subscriber, Definition, Link, Product, 
        Record, Category, Comment
    )
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime, time, timedelta, timezone
from markdown import markdown
from app.email import send_email
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename

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
        user = User()
        form.populate_obj(user)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"{user.username.upper()} was added successfully!", "success")
        log_new(user, 'added a user')
        return redirect(url_for('admin.users'))
    return render_template('admin/user-edit.html', form=form, tab='users', action='Add', page=page)

@bp.route('/admin/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    page = Page.query.filter_by(slug='admin').first()
    user = User.query.filter_by(id=id).first()
    form = EditUserForm(obj=user)
    form.timezone.choices = [(t, t) for t in pytz.common_timezones]
    if form.validate_on_submit():
        log_orig = log_change(user)
        form.populate_obj(user)
        if form.password.data and user.check_password(form.password.data):
            user.set_password(form.new_password.data)
        log_change(log_orig, user, 'edited a user')
        db.session.commit()
        flash(f"User {user.username} was updated successfully!", "success")
        return redirect(url_for('admin.users'))
    form.username.data = user.username
    form.email.data = user.email
    form.avatar.data = user.avatar
    form.about_me.data = user.about_me
    form.timezone.data = user.timezone
    return render_template('admin/user-edit.html', form=form, tab='users', action='Edit', user=user,page=page)

@bp.route('/admin/pages')
@login_required
def pages(unpub=None):
    page = Page.query.filter_by(slug='admin').first()
    Page.set_nav()
    if unpub:
        pages = Page.query.filter_by(published=False).order_by('dir_path','sort','title')
    else: 
        pages = Page.query.filter_by(published=True).order_by('dir_path','sort','title')
    return render_template('admin/pages.html', 
            tab='pages', 
            pages=pages, 
            unpub=unpub,
            page=page,
        )

@bp.route('/admin/pages/unpublished')
def unpublished_pages():
    return pages(unpub=True)

@bp.route('/admin/page/add', methods=['GET', 'POST'])
@login_required
def add_page():
    form = AddPageForm()
    for field in form:
        print(f"{field.name}: {field.data}")
    form.parent_id.choices = [(0,'---')] + [(p.id, f"{p.title} ({p.path})") for p in Page.query.all()]
    form.user_id.choices = [(u.id, u.username) for u in User.query.all()]
    form.notify_group.choices = [('',''),('all', 'All')] + current_app.config['SUBSCRIPTION_GROUPS'] + [('discord','Discord Only')]
    if form.validate_on_submit():
        parentid = form.parent_id.data if form.parent_id.data else None
        page = Page(
                title = form.title.data,
                slug = form.slug.data,
                template = form.template.data,
                parent_id = parentid,
                cover = form.cover.data,
                banner = form.banner.data,
                body = form.body.data,
                notes = form.notes.data,
                summary = form.summary.data,
                author_note = form.author_note.data,
                author_note_location = form.author_note_location.data,
                sidebar = form.sidebar.data,
                tags = form.tags.data,
                user_id = current_user.id,
                notify_group = form.notify_group.data,
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
        if form.notify_subs.data:
            page.notify_subscribers(form.notify_group.data)
        flash("Page added successfully.", "success")
        log_new(page, 'added a page')
        Page.set_nav()
        return redirect(url_for('admin.edit_page', id=page.id))
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
    was_published = page.published
    print(f"ANCESTORS: {page.ancestors()}")
    for anc in page.ancestors():
        print(f"ANCESTOR: {anc}")
    form = AddPageForm()
    form.parent_id.choices = [(0,'---')] + [(p.id, f"{p.title} ({p.path})") for p in Page.query.all()]
    form.user_id.choices = [(u.id, u.username) for u in User.query.all()]
    form.notify_group.choices = [('',''),('all', 'All')] + current_app.config['SUBSCRIPTION_GROUPS'] + [('discord','Discord Only')]
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
            cover = page.cover,
            banner = page.banner,
            body = page.body,
            notes = page.notes,
            summary = page.summary,
            author_note = page.author_note,
            author_note_location = page.author_note_location,
            sidebar = page.sidebar,
            tags = page.tags,
            user_id = page.user_id,
            notify_group = page.notify_group,
            pub_date = page.pub_date,
            published = page.published,
            path = page.path,
            dir_path = page.dir_path,
        )
        db.session.add(version)

        # Update page
        log_orig = log_change(page)
        parentid = form.parent_id.data if form.parent_id.data else None
        page.title = form.title.data
        page.slug = form.slug.data
        page.template = form.template.data
        page.parent_id = parentid
        page.cover = form.cover.data
        page.banner = form.banner.data
        page.body = form.body.data
        page.notes = form.notes.data
        page.summary = form.summary.data
        page.author_note = form.author_note.data
        page.author_note_location = form.author_note_location.data
        page.sidebar = form.sidebar.data
        page.tags = form.tags.data
        page.user_id = form.user_id.data
        page.notify_group = form.notify_group.data
        page.published = form.published.data
        page.edit_date = datetime.utcnow()

        pdate = form.pub_date.data
        ptime = form.pub_time.data
        local_tz = form.timezone.data if form.timezone.data else current_user.timezone
        if pdate and ptime:
            page.set_local_pub_date(f"{pdate} {ptime}", local_tz)
        else:
            page.pub_date = None
        page.set_path()
        log_change(log_orig, page, 'edited a page')
        db.session.commit()
        if form.notify_subs.data:
            current_app.logger.debug(form.notify_group.data)
            page.notify_subscribers(form.notify_group.data)
        flash("Page updated successfully.", "success")
        Page.set_nav()
        return redirect(url_for('admin.edit_page', id=id))
    if form.errors:
        flash("<b>Error!</b> Please fix the errors below.", "danger")
    versions = PageVersion.query.filter_by(original_id=id).order_by(desc('edit_date')).all()
    version = PageVersion.query.filter_by(id=ver_id).first() if ver_id else None
    if version:
        form.title.data = version.title
        form.slug.data = version.slug
        form.template.data = version.template
        form.parent_id.data = version.parent_id 
        form.cover.data = version.cover
        form.banner.data = version.banner
        form.body.data = version.body
        form.notes.data = version.notes
        form.summary.data = version.summary
        form.author_note.data = version.author_note
        form.author_note_location.data = version.author_note_location
        form.sidebar.data = version.sidebar
        form.tags.data = version.tags
        form.user_id.data = version.user_id
        form.notify_group.data = version.notify_group
        form.pub_date.data = version.local_pub_date(current_user.timezone)
        form.pub_time.data = version.local_pub_date(current_user.timezone)
        form.published.data = version.published
    else:
        form.title.data = page.title
        form.slug.data = page.slug
        form.template.data = page.template
        form.parent_id.data = page.parent_id 
        form.cover.data = page.cover
        form.banner.data = page.banner
        form.body.data = page.body
        form.notes.data = page.notes
        form.summary.data = page.summary
        form.author_note.data = page.author_note
        form.author_note_location.data = page.author_note_location
        form.sidebar.data = page.sidebar
        form.tags.data = page.tags
        form.user_id.data = page.user_id
        form.notify_group.data = page.notify_group
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

class DeletePage(DeleteObjView):
    model = Page
    log_msg = 'deleted a page'
    success_msg = 'Page deleted.'
    redirect = {'endpoint': 'admin.pages'}

bp.add_url_rule("/admin/page/delete", 
        view_func = login_required(DeletePage.as_view('delete_page')))

@bp.route('/admin/page/check-scheduled', methods=['POST'])
def check_scheduled(): # SCHEDULED RELEASE WEBHOOK
    if request.form['webhook_secret'] == current_app.config['WEBHOOK_SECRET']:
        pages = Page.query.filter(
                Page.published == False,
                Page.pub_date,
                Page.pub_date <= datetime.utcnow(),
            ).order_by(Page.pub_date).all()
        if not pages:
            current_app.logger.info('No pages found for automatic release.')
        released_pages = 0
        for page in pages:
            page.published = True
            db.session.commit()
            current_app.logger.info(f'{page.title} ({page.path}) has been released automatically.')
            released_pages += 1
            if page.notify_group:
                current_app.logger.info(f'{page.notify_group} will be notified about the release of {page.title}.')
                page.notify_subscribers(page.notify_group)
        return f'Released Pages: {released_pages}\n'
    return 'Access Denied\n', 404

@bp.route('/admin/tags')
@login_required
def tags():
    page = Page.query.filter_by(slug='admin').first()
    tags = Tag.query.order_by('name')
    return render_template('admin/tags.html', 
            tab='pages', 
            tags=tags, 
            page=page
        )

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
            log_new(tag, 'added a tag')
            return redirect(url_for('admin.tags'))
        else:
            flash("<b>Error!</b> That tag already exists.", "danger")
    return render_template('admin/tag-edit.html', form=form, tab='pages', action='Add', page=page)

@bp.route('/admin/tag/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tag(id):
    page = Page.query.filter_by(slug='admin').first()
    tag = Tag.query.filter_by(id=id).first()
    form = AddTagForm()
    if form.validate_on_submit():
        if form.validate_tag(form.name.data, id):
            log_orig = log_change(tag)
            tag.name = form.name.data
            log_change(log_orig, tag, 'edited a tag')
            db.session.commit()
            flash("Tag updated successfully.", "success")
            return redirect(url_for('admin.tags'))
        else:
            flash("<b>Error!</b> That tag already exists.", "danger")
    form.name.data = tag.name
    return render_template('admin/tag-edit.html', form=form, tab='pages', tag=tag, action='Edit', page=page)

@bp.route('/admin/definitions')
@login_required
def definitions():
    page = Page.query.filter_by(slug='admin').first()
    definitions = Definition.query.order_by('name')
    return render_template('admin/definitions.html', 
            tab='pages', 
            definitions=definitions, 
            page=page,
            len=len,
        )

class AddDefinition(SaveObjView):
    title = "Add Definition"
    model = Definition
    form = DefinitionEditForm
    action = 'Add'
    log_msg = 'added a definition'
    success_msg = 'Definition added.'
    delete_endpoint = 'admin.delete_definition'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.definitions'}

    def extra(self):
        self.form.type.choices = Definition.TYPE_CHOICES
        self.form.tag_id.choices = [(0,'')] + [(t.id, t.name) for t in Tag.query.order_by('name').all()]
        self.form.parent_id.choices = [(0,'')] + [(p.id, str(p)) for p in Page.query.all()]
        self.context['tab'] = 'pages'
        #self.context.update({'form': self.form})

    def pre_post(self):
        if self.form.parent_id.data == 0:
            self.form.parent_id.data = None
        if self.form.tag_id.data == 0:
            self.form.tag_id.data = None

bp.add_url_rule("/admin/definition/add", 
        view_func=login_required(AddDefinition.as_view('add_definition')))

class EditDefinition(SaveObjView):
    title = "Edit Definition"
    model = Definition
    form = DefinitionEditForm
    action = 'Edit'
    log_msg = 'updated a definition'
    success_msg = 'Definition updated.'
    delete_endpoint = 'admin.delete_definition'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.definitions'}

    def extra(self):
        self.form.type.choices = Definition.TYPE_CHOICES
        self.form.tag_id.choices = [(0,'')] + [(t.id, t.name) for t in Tag.query.all()]
        self.form.parent_id.choices = [(0,'')] + [(p.id, str(p)) for p in Page.query.all()]
        self.context['tab'] = 'pages'
        #self.context.update({'form': self.form})

    def pre_post(self):
        if self.form.parent_id.data == 0:
            self.form.parent_id.data = None
        if self.form.tag_id.data == 0:
            self.form.tag_id.data = None

bp.add_url_rule("/admin/definition/edit/<int:obj_id>", 
        view_func=login_required(EditDefinition.as_view('edit_definition')))

class DeleteDefinition(DeleteObjView):
    model = Definition
    log_msg = 'deleted a definition'
    success_msg = 'Definition deleted.'
    redirect = {'endpoint': 'admin.definitions'}

bp.add_url_rule("/admin/Definition/delete", 
        view_func = login_required(DeleteDefinition.as_view('delete_definition')))

@bp.route('/admin/links')
@login_required
def links():
    page = Page.query.filter_by(slug='admin').first()
    links = Link.query.all()
    return render_template('admin/links.html',
            tab='shop',
            page=page,
            links=links,
        )

class AddLink(SaveObjView):
    title = "Add Link"
    model = Link
    form = LinkEditForm
    action = 'Add'
    log_msg = 'added a link'
    success_msg = 'Link added.'
    delete_endpoint = 'admin.delete_link'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}

    def extra(self):
        self.context['tab'] = 'shop'
        self.form.product_id.choices = [(p.id, str(p)) for p in Product.query.all()]
        self.form.format.choices = [(f,f) for f in current_app.config['LINK_FORMATS']]
        current_app.logger.debug(request.args.get('product_id'))
        if request.args.get('product_id'):
            self.form.product_id.data = int(request.args.get('product_id'))

bp.add_url_rule("/admin/link/add", 
        view_func=login_required(AddLink.as_view('add_link')))

class EditLink(SaveObjView):
    title = "Edit Link"
    model = Link
    form = LinkEditForm
    action = 'Edit'
    log_msg = 'updated a link'
    success_msg = 'Link updated.'
    delete_endpoint = 'admin.delete_link'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}

    def extra(self):
        self.context['tab'] = 'shop'
        self.form.product_id.choices = [(p.id, str(p)) for p in Product.query.all()]
        self.form.format.choices = [(f,f) for f in current_app.config['LINK_FORMATS']]

bp.add_url_rule("/admin/link/edit/<int:obj_id>", 
        view_func=login_required(EditLink.as_view('edit_link')))

class DeleteLink(DeleteObjView):
    model = Link
    log_msg = 'deleted a link'
    success_msg = 'Link deleted.'
    redirect = {'endpoint': 'admin.products'}

bp.add_url_rule("/admin/link/delete", 
        view_func = login_required(DeleteLink.as_view('delete_link')))

@bp.route('/admin/products')
@login_required
def products():
    page = Page.query.filter_by(slug='admin').first()
    products = Product.query.all()
    return render_template('admin/products.html',
            tab='shop',
            page=page,
            products=products,
        )

@bp.route('/admin/send-product/<obj_id>', methods=['GET','POST'])
@login_required
def send_product(obj_id):
    product = Product.query.filter_by(id=obj_id).first()
    form = SendProductForm()
    if form.validate_on_submit():
        product.send([form.email.data])
        flash(f'Sent product <b>{product.name}</b> to <b>{form.email.data}</b>.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/send-product.html',
            form=form,
            product=product,
            title='Send Product',
        )

class AddProduct(SaveObjView):
    title = "Add Product"
    model = Product
    form = ProductEditForm
    action = 'Add'
    log_msg = 'added a product'
    success_msg = 'Product added.'
    delete_endpoint = 'admin.delete_product'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}

    def extra(self):
        self.context['tab'] = 'shop'
        self.form.linked_page_id.choices = [(0,'')] + [(p.id, str(p)) for p in Page.query.all()]
        self.form.category_id.choices = [(0,'')] + [(c.id, c.name) for c in Category.query.all()]

    def pre_post(self):
        self.obj.updater_id = current_user.id

bp.add_url_rule("/admin/product/add", 
        view_func=login_required(AddProduct.as_view('add_product')))

class EditProduct(SaveObjView):
    title = "Edit Product"
    model = Product
    form = ProductEditForm
    action = 'Edit'
    log_msg = 'updated a product'
    success_msg = 'Product updated.'
    delete_endpoint = 'admin.delete_product'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}

    def extra(self):
        self.context['tab'] = 'shop'
        self.form.linked_page_id.choices = [(0,'')] + [(p.id, str(p)) for p in Page.query.all()]
        self.form.category_id.choices = [(0,'')] + [(c.id, c.name) for c in Category.query.all()]

    def pre_post(self):
        self.obj.updater_id = current_user.id

bp.add_url_rule("/admin/product/edit/<int:obj_id>", 
        view_func=login_required(EditProduct.as_view('edit_product')))

class DeleteProduct(DeleteObjView):
    model = Product
    log_msg = 'deleted a product'
    success_msg = 'Product deleted.'
    redirect = {'endpoint': 'admin.products'}

bp.add_url_rule("/admin/product/delete", 
        view_func = login_required(DeleteProduct.as_view('delete_product')))

@bp.route('/admin/categories')
@login_required
def categories():
    page = Page.query.filter_by(slug='admin').first()
    categories = Category.query.all()
    return render_template('admin/categories.html',
            tab='shop',
            page=page,
            categories=categories,
        )

class AddCategory(SaveObjView):
    title = "Add Category"
    model = Category
    form = CategoryEditForm
    action = 'Add'
    log_msg = 'added a category'
    success_msg = 'Category added.'
    delete_endpoint = 'admin.delete_category'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.categories'}

    def extra(self):
        self.context['tab'] = 'shop'

    def pre_post(self):
        self.obj.updater_id = current_user.id

bp.add_url_rule("/admin/category/add", 
        view_func=login_required(AddCategory.as_view('add_category')))

class EditCategory(SaveObjView):
    title = "Edit Category"
    model = Category
    form = CategoryEditForm
    action = 'Edit'
    log_msg = 'updated a category'
    success_msg = 'Category updated.'
    delete_endpoint = 'admin.delete_category'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.categories'}

    def extra(self):
        self.context['tab'] = 'shop'

    def pre_post(self):
        self.obj.updater_id = current_user.id

bp.add_url_rule("/admin/category/edit/<int:obj_id>", 
        view_func=login_required(EditCategory.as_view('edit_category')))

class DeleteCategory(DeleteObjView):
    model = Category
    log_msg = 'deleted a category'
    success_msg = 'Category deleted.'
    redirect = {'endpoint': 'admin.categories'}

bp.add_url_rule("/admin/category/delete", 
        view_func = login_required(DeleteCategory.as_view('delete_category')))

@bp.route('/admin/records', methods=['GET','POST'])
@bp.route('/admin/records/<string:day>', methods=['GET','POST'])
@login_required
def records(day=None):
    form = RecordForm()
    if form.validate_on_submit():
        record = Record()
        current_app.logger.debug('VALIDATED')
        for field in form:
            current_app.logger.debug(f'{field.name}: {field.data}')
        form.populate_obj(record)
        record.words = form.end_words.data - form.start_words.data
        record.words_per_minute = int(record.words/record.minutes) if record.minutes else None
        current_app.logger.debug(repr(record))
        db.session.add(record)
        db.session.commit()
        log_new(record, 'added a record')
        flash('Record added!','success')
        return redirect(url_for('admin.records', day=day))
    page = Page.query.filter_by(slug='admin').first()
    today = datetime(int(day[0:4]), int(day[4:6]), int(day[-2:])) if day else datetime.utcnow()
    current_app.logger.debug(f'here is day: {today}')
    today = datetime.combine(today, time(0,0,0))
    end_date = today.date()
    prev_month = today + relativedelta(months=-1)
    start_date = prev_month.date()
    chart_records = []
    #records = Record.query.filter(Record.date >= day, Record.date < next_month).order_by(desc('created')).all()
    records = Record.query.filter(Record.date >= prev_month, Record.date <= today).order_by(desc('created')).all()
    total_query = db.session.query(Record, db.func.sum(Record.words).label('data'))
    stats = {
            'week': total_query.filter(
                    Record.date >= (today - timedelta(days=7)),
                    Record.date <= today
                ).all()[0].data,
            'month': total_query.filter(
                    Record.date >= (today - timedelta(days=30)),
                    Record.date <= today
                ).all()[0].data,
            'year': total_query.filter(
                    Record.date >= (today - timedelta(days=365)),
                    Record.date <= today
                ).all()[0].data,
        }
    #stats['week'] = stats['week'].data if stats['week'] else 0
    #stats['month'] = stats['month'].data if stats['month'] else 0
    #stats['year'] = stats['year'].data if stats['year'] else 0
    stats['week_avg'] = int(stats['week'] / 7) if stats['week'] else 0
    stats['month_avg'] = int(stats['month'] / 30) if stats['month'] else 0
    stats['year_avg'] = int(stats['year'] / 365) if stats['year'] else 0
    best_query = db.session.query(Record, db.func.sum(Record.words).label('best')).group_by(Record.date).order_by(desc('best'))
    stats['week_best'] = best_query.filter(
            Record.date >= (today - timedelta(days=7)),
            Record.date <= today
        ).first()
    stats['week_best'] = stats['week_best'].best if stats['week_best'] else 0
    stats['month_best'] = best_query.filter(
            Record.date >= (today - timedelta(days=30)),
            Record.date <= today
        ).first()
    stats['month_best'] = stats['month_best'].best if stats['month_best'] else 0
    stats['year_best'] = best_query.filter(
            Record.date >= (today - timedelta(days=365)),
            Record.date <= today
        ).first()
    stats['year_best'] = stats['year_best'].best if stats['year_best'] else 0
    current_app.logger.debug(datetime.utcnow().date())
    stats['today'] = Record.words_by_day(today.date())
    while (prev_month <= today):
        chart_records += [Record.words_by_day(prev_month)]
        prev_month += timedelta(days=1)
    return render_template('admin/records.html', 
            tab='pages', 
            chart_records=chart_records,
            records=records,
            page=page,
            form=form,
            start_date=start_date,
            end_date=end_date,
            stats=stats,
        )

class EditRecord(SaveObjView):
    title = "Edit Record"
    model = Record
    form = RecordEditForm
    action = 'Edit'
    log_msg = 'updated a record'
    success_msg = 'Record updated.'
    delete_endpoint = 'admin.delete_record'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.records'}

    def extra(self):
        self.context['tab'] = 'pages'

    def pre_post(self):
        self.obj.words = self.form.end_words.data - self.form.start_words.data
        self.obj.words_per_minute = int(self.obj.words/self.form.minutes.data) if self.form.minutes.data else None

bp.add_url_rule("/admin/record/edit/<int:obj_id>", 
        view_func=login_required(EditRecord.as_view('edit_record')))

class DeleteRecord(DeleteObjView):
    model = Record
    log_msg = 'deleted a record'
    success_msg = 'Record deleted.'
    redirect = {'endpoint': 'admin.records'}

bp.add_url_rule("/admin/record/delete", 
        view_func = login_required(DeleteRecord.as_view('delete_record')))

@bp.route('/admin/files')
@bp.route('/admin/files/<string:folder>')
@login_required
def files(folder='upload'):
    page = Page.query.filter_by(slug='admin').first()
    config_folder = current_app.config.get(folder.upper() + "_DIR")
    filenames = [f for f in os.listdir(config_folder)]
    files = []
    for f in filenames:
        mtime = os.stat(os.path.join(config_folder, f)).st_mtime
        modified = datetime.fromtimestamp(mtime, tz=timezone.utc)
        files += [(f, modified)]
    return render_template('admin/files.html',
            tab='files',
            folder=folder,
            page=page,
            files=files,
        )

@bp.route('/admin/files/<string:folder>/add', methods=['GET','POST'])
@login_required
def add_file(folder):
    page = Page.query.filter_by(slug='admin').first()
    form = FileUploadForm()
    form.folder.choices = [('product', 'Products'),('upload','Uploads')] 
    if form.validate_on_submit():
        current_app.logger.debug(form.file_data.data)
        form.file_data.data.save(
                os.path.join(
                    current_app.config.get(form.folder.data.upper() + '_DIR'), 
                    secure_filename(form.file_data.data.filename)
                )
            )
        current_app.logger.info(f'{current_user.username} uploaded the file "{form.file_data.data.filename}" to {folder.title()}s.')
        flash(f'The file <b>{form.file_data.data.filename}</b> was uploaded successfully', 'success')
        return redirect(url_for('admin.files', folder=form.folder.data))
    form.folder.data = folder.lower()
    return render_template('admin/file-upload.html',
            tab='files',
            folder=folder,
            page=page,
            form=form,
        )

@bp.route('/admin/files/<string:folder>/<string:filename>/delete')
@login_required
def delete_file(folder,filename):
    page = Page.query.filter_by(slug='admin').first()
    directory = current_app.config.get(folder.upper() + '_DIR')
    os.remove(os.path.join(directory, filename))
    current_app.logger.info(f'{current_user.username} deleted the file "{filename}" from {folder.title()}s.')
    flash(f'The file <b>{filename}</b> was deleted from {folder.title()}s.', 'success')
    return redirect(url_for('admin.files', folder=folder))

@bp.route('/admin/comments')
def comments():
    page = Page.query.filter_by(slug='admin').first()
    comments = Comment.query.all()
    return render_template('admin/comments.html',
            tab='comments',
            page=page,
            comments=comments,
        )

class EditComment(SaveObjView):
    title = "Edit Comment"
    model = Comment
    form = CommentEditForm
    action = 'Edit'
    log_msg = 'updated a comment'
    success_msg = 'Comment updated.'
    delete_endpoint = 'admin.delete_comment'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.comments'}

    def extra(self):
        self.context['tab'] = 'comments'
        self.form.user_id.choices = [(0, '')] + [(u.id, u.username) for u in User.query.all()]
        self.form.reply_id.choices = [(0, '')] + [(r.id, str(r)) for r in Comment.query.filter(Comment.id!=self.obj.id).all()]

    def pre_get(self):
        if self.obj:
            created = to_local_tz_date(self.obj.created, current_user.timezone)
            self.form.created_date.data = created.date()
            self.form.created_time.data = created.time()

    def post_post(self):
        self.obj.created = to_utc_date(f'{self.form.created_date.data} {self.form.created_time.data}', self.form.timezone.data)
        self.obj.user_id = self.form.user_id.data if self.form.user_id.data > 0 else None

bp.add_url_rule("/admin/comment/edit/<int:obj_id>", 
        view_func=login_required(EditComment.as_view('edit_comment')))

class DeleteComment(DeleteObjView):
    model = Comment
    log_msg = 'deleted a comment'
    success_msg = 'Comment deleted.'
    redirect = {'endpoint': 'admin.comments'}

bp.add_url_rule("/admin/comment/delete", 
        view_func = login_required(DeleteComment.as_view('delete_comment')))

@bp.route('/admin/products/<string:filename>')
@login_required
def product_direct(filename):
    return send_from_directory(current_app.config['PRODUCT_DIR'], filename)

@bp.route('/admin/subscribers')
@login_required
def subscribers():
    page = Page.query.filter_by(slug='admin').first()
    subscribers = Subscriber.query.order_by('email').all()
    return render_template('admin/subscribers.html', tab='subscribers', subscribers=subscribers, page=page)

@bp.route('/admin/subscriber/email', methods=['GET','POST'])
@login_required
def send_mail():
    page = Page.query.filter_by(slug='admin').first()
    form = EmailForm()
    form.recipients.choices = [(s.id, f'{s.name_if_given(True)} ({s.email})') for s in Subscriber.query.all()] 
    if form.validate_on_submit():
        html = markdown(form.body.data.replace('--', '&#8212;').replace('---', '<center>&#127793;</center>'))
        pattern = re.compile(r'<.*?>')
        body = pattern.sub('', html)
        banner = form.banner.data if form.banner.data else ''
        sent_to = []
        for recipient_id in form.recipients.data:
            recipient = Subscriber.query.filter_by(id=recipient_id).first()
            if recipient:
                send_email(
                        form.subject.data,
                        current_app.config['MAIL_DEFAULT_SENDER'],
                        [recipient.email],
                        body,
                        render_template('email/manual.html', body=html, recipient=recipient, banner=banner)
                    )
            sent_to += [recipient.email]
        flash(f'Email(s) sent to: <b>{", ".join(sent_to)}</b>', 'success')
    return render_template('admin/email-send.html', tab='subscribers', page=page, form=form)

@bp.route('/admin/logs')
@login_required
def logs():
    return send_from_directory(current_app.config['TEMPLATE_DIR'] + 'admin','logs.html')

@bp.route("/admin/logs/info")
@login_required
def textlogs():
    return send_from_directory('../textlogs', 'flask_writer.log')

@bp.route("/admin/logs/error")
@login_required
def errorlogs():
    return send_from_directory('../textlogs', 'flask_writer_errors.log')
