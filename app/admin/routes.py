import pytz
import re
from flask import render_template, redirect, flash, url_for, send_from_directory, current_app, request
from app import db
from app.admin import bp
from app.admin.functions import log_new, log_change
from app.admin.forms import (
        AddUserForm, AddPageForm, AddTagForm, EditUserForm, EditDefinitionForm, 
        EmailForm, LinkEditForm, ProductEditForm, RecordForm, RecordEditForm
    )
from app.admin.generic_views import SaveObjView, DeleteObjView
from app.models import (
        Page, User, Tag, PageVersion, Subscriber, Definition, Link, Product, 
        Record
    )
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime, time, timedelta
from markdown import markdown
from app.email import send_email
from dateutil.relativedelta import relativedelta

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
        log_new(user, 'added a user')
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
        log_orig = log_change(user)
        user.username = form.username.data
        user.email = form.email.data
        user.about_me = form.about_me.data
        user.timezone = form.timezone.data
        if form.password.data and user.check_password(form.password.data):
            user.set_password(form.new_password.data)
        log_change(log_orig, user, 'edited a user')
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
    form.notify_group.choices = Subscriber.SUBSCRIPTION_CHOICES
    if form.validate_on_submit():
        parentid = form.parent_id.data if form.parent_id.data else None
        page = Page(
                title = form.title.data,
                slug = form.slug.data,
                template = form.template.data,
                parent_id = parentid,
                banner = form.banner.data,
                body = form.body.data,
                notes = form.notes.data,
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
        if form.notify_subs.data:
            page.notify_subscribers(form.notify_group.data)
        db.session.add(page)
        db.session.commit()
        flash("Page added successfully.", "success")
        log_new(page, 'added a page')
        Page.set_nav()
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
    was_published = page.published
    print(f"ANCESTORS: {page.ancestors()}")
    for anc in page.ancestors():
        print(f"ANCESTOR: {anc}")
    form = AddPageForm()
    form.parent_id.choices = [(0,'---')] + [(p.id, f"{p.title} ({p.path})") for p in Page.query.all()]
    form.user_id.choices = [(u.id, u.username) for u in User.query.all()]
    form.notify_group.choices = Subscriber.SUBSCRIPTION_CHOICES
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
            notes = page.notes,
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
        log_orig = log_change(page)
        parentid = form.parent_id.data if form.parent_id.data else None
        page.title = form.title.data
        page.slug = form.slug.data
        page.template = form.template.data
        page.parent_id = parentid
        page.banner = form.banner.data
        page.body = form.body.data
        page.notes = form.notes.data
        page.summary = form.summary.data
        page.sidebar = form.sidebar.data
        page.tags = form.tags.data
        page.user_id = form.user_id.data
        page.published = form.published.data
        page.edit_date = datetime.utcnow()

        pdate = form.pub_date.data
        ptime = form.pub_time.data
        local_tz = form.timezone.data if form.timezone.data else current_user.timezone
        if pdate and ptime:
            page.set_local_pub_date(f"{pdate} {ptime}", local_tz)
        page.set_path()
        if form.notify_subs.data:
            current_app.logger.debug(form.notify_group.data)
            page.notify_subscribers(form.notify_group.data)
        log_change(log_orig, page, 'edited a page')
        db.session.commit()
        flash("Page updated successfully.", "success")
        Page.set_nav()
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
        form.notes.data = version.notes
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
        form.notes.data = page.notes
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
            log_new(tag, 'added a tag')
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
            log_orig = log_change(tag)
            tag.name = form.name.data
            log_change(log_orig, tag, 'edited a tag')
            db.session.commit()
            flash("Tag updated successfully.", "success")
            return redirect(url_for('admin.tags'))
        else:
            flash("<b>Error!</b> That tag already exists.", "danger")
    form.name.data = tag.name
    return render_template('admin/tag-edit.html', form=form, tab='tags', tag=tag, action='Edit', page=page)

@bp.route('/admin/definitions')
@login_required
def definitions():
    page = Page.query.filter_by(slug='admin').first()
    definitions = Definition.query.order_by('name')
    return render_template('admin/definitions.html', 
            tab='definitions', 
            definitions=definitions, 
            page=page,
            len=len,
        )

@bp.route('/admin/definition/add', methods=['GET', 'POST'])
@login_required
def add_definition():
    page = Page.query.filter_by(slug='admin').first()
    form = EditDefinitionForm()
    form.parent_id.choices = [(p.id, str(p)) for p in Page.query.all()]
    form.type.choices = Definition.TYPE_CHOICES
    form.tag_id.choices = [(0, '')] + [(t.id, t.name) for t in Tag.query.order_by('name').all()]
    if form.validate_on_submit():
        definition = Definition(
                name=form.name.data,
                type=form.type.data,
                body=form.body.data,
                hidden_body=form.hidden_body.data,
                parent_id=form.parent_id.data,
            )
        if form.tag_id.data > 0:
            definition.tag_id = form.tag_id.data
        db.session.add(definition)
        db.session.commit()
        log_new(definition, 'added a definition')
        flash("Definition added successfully.", "success")
        return redirect(url_for('admin.definitions'))
    return render_template('admin/definition-edit.html', 
            form=form, 
            tab='definitions', 
            action='Add', 
            page=page
        )

@bp.route('/admin/definition/edit/<int:definition_id>', methods=['GET', 'POST'])
@login_required
def edit_definition(definition_id):
    page = Page.query.filter_by(slug='admin').first()
    definition = Definition.query.filter_by(id=definition_id).first()
    form = EditDefinitionForm()
    form.parent_id.choices = [(p.id, str(p)) for p in Page.query.all()]
    form.type.choices = Definition.TYPE_CHOICES
    form.tag_id.choices = [(0, '')] + [(t.id, t.name) for t in Tag.query.order_by('name').all()]
    if form.validate_on_submit():
        log_orig = log_change(definition)
        definition.name=form.name.data
        definition.type=form.type.data
        definition.body=form.body.data
        definition.hidden_body=form.hidden_body.data
        definition.parent_id=form.parent_id.data
        if form.tag_id.data > 0:
            definition.tag_id=form.tag_id.data
        #definition.tags=form.tags.data
        log_change(log_orig, definition, 'edited a definition')
        db.session.commit()
        flash("Definition updated successfully.", "success")
        return redirect(url_for('admin.definitions'))
    form.name.data = definition.name
    form.type.data = definition.type
    form.body.data = definition.body
    form.hidden_body.data = definition.hidden_body
    form.tag_id.data = definition.tag_id
    form.parent_id.data = definition.parent_id
    #form.tags.data = definition.tags
    return render_template('admin/definition-edit.html', 
            form=form, 
            tab='definitions', 
            definition=definition, 
            action='Edit', 
            page=page
        )

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
        self.form.product_id.choices = [(p.id, str(p)) for p in Product.query.filter_by(active=True).all()]
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
        self.form.product_id.choices = [(p.id, str(p)) for p in Product.query.filter_by(active=True).all()]

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
    current_app.logger.debug(int(day[0:4]))
    current_app.logger.debug(int(day[4:6]))
    current_app.logger.debug(int(day[-2:]))
    today = datetime(int(day[0:4]), int(day[4:6]), int(day[-2:])) if day else datetime.utcnow()
    current_app.logger.debug(f'here is day: {today}')
    today = datetime.combine(today, time(0,0,0))
    end_date = today.date()
    prev_month = today + relativedelta(months=-1)
    start_date = prev_month.date()
    chart_records = []
    #records = Record.query.filter(Record.date >= day, Record.date < next_month).order_by(desc('created')).all()
    records = Record.query.order_by(desc('created')).all()
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
            tab='records', 
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
