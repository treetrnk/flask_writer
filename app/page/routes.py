from flask import (
        render_template, redirect, url_for, flash, session, request, 
        current_app, make_response, send_from_directory
    )
from app.page import bp
from app.page.forms import SearchForm, SubscribeForm, SubscriptionForm
from sqlalchemy import or_, desc
from app.models import Page, Tag, Subscriber, Definition, Link, Product
from app import db

@bp.route('/')
def home():
    Page.set_nav()
    page = Page.query.filter_by(slug='home',published=True).first()
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

@bp.route('/search', methods=['GET','POST'])
@bp.route('/search/tag/<string:tag>')
@bp.route('/search/keyword/<string:keyword>', methods=['GET', 'POST'])
@bp.route('/search/keyword', methods=['GET','POST'])
def search(tag=None,keyword=None):
    Page.set_nav()
    tags = Tag.query.filter(Tag.pages != None).order_by('name').all()
    form = SearchForm()
    results = None
    if keyword != None:
        form.keyword.data = keyword
    print(keyword)
    if form.validate_on_submit():
        print(keyword)
        keyword = form.keyword.data
    if form.errors:
        for error in form.errors:
            print(error)
    if tag:
        results = Page.query.filter(
                Page.tags.any(name=tag), 
                Page.published == True
            ).order_by('sort','pub_date','title').all()
    if keyword:
        results = Page.query.filter(
                Page.body.ilike(f'%{keyword}%'),
                Page.published == True
            ).order_by('sort','pub_date','title').all()
    return render_template('page/search.html',
            form=form,
            keyword=keyword,
            tag=tag,
            tags=tags,
            results=results,
            page=Page.query.filter_by(slug='search').first()
        )

@bp.route('/subscribe', methods=['GET','POST'])
def subscribe():
    Page.set_nav()
    form = SubscribeForm()
    form.subscription.choices = Subscriber.SUBSCRIPTION_CHOICES
    for field in form:
        print(f"{field.name}: {field.data}")
    if form.validate_on_submit():
        print("Validated")
        sub = Subscriber(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
        )
        current_app.logger.debug(form.subscription.choices)
        if "all" in form.subscription.data:
            choices = [c[0] for c in form.subscription.choices]
            current_app.logger.debug(choices)
            choices.remove("all")
            sub.subscription = "," + ",".join(choices) + ","
        else:
            sub.subscription = "," + ",".join(form.subscription.data) + ","
        current_app.logger.debug(sub.subscription)
        #raise Exception('pause')
        db.session.add(sub)
        db.session.commit()
        sub.welcome()
        current_app.logger.info(f'New Subscriber!\n    {repr(sub)}')
        flash('You have subscribed successfully!', 'success')
        return redirect(url_for('page.home'))
    form.subscription.data = [i[0] for i in Subscriber.SUBSCRIPTION_CHOICES]
    return render_template('subscribe.html',
            form=form
        )

@bp.route('/update-subscription/<string:email>/<string:code>', methods=['GET','POST'])
def subscription(email, code):
    sub = Subscriber.query.filter_by(email=email).first()
    if sub and sub.check_update_code(code):
        Page.set_nav()
        form = SubscriptionForm()
        form.subscription.choices = Subscriber.SUBSCRIPTION_CHOICES
        choices = [c[0] for c in form.subscription.choices]
        for field in form:
            print(f"{field.name}: {field.data}")
        if form.validate_on_submit():
            print("Validated")
            current_app.logger.debug(form.subscription.data)
            if "all" in form.subscription.data:
                choices.remove("all")
                sub.subscription = "," + ",".join(choices) + ","
            else:
                sub.subscription = "," + ",".join(form.subscription.data) + ","
            current_app.logger.debug(sub.subscription)
            db.session.commit()
            current_app.logger.info(f'Subscription Updated!\n    {repr(sub)}')
            flash('Your subscription has been updated!', 'success')
            return redirect(url_for('page.subscription', email=email, code=code))
        form.subscription.data = sub.subscription[1:-1].split(',')
        return render_template('update-subscription.html',
                form=form,
                subscriber=sub,
            )
    else: 
        flash('Invalid code to update subscription!', 'danger')
        return redirect(url_for('page.home'))

@bp.route('/unsubscribe/<string:email>/<string:code>')
def unsubscribe(email, code):
    sub = Subscriber.query.filter_by(email=email).first()
    if sub and sub.check_update_code(code):
        db.session.delete(sub)
        db.session.commit()
        flash(f"{email} has been unsubscribed successfully. If you'd like to resubscribe, <a href='/subscribe'>click here</a>.", "success")
        current_app.logger.info(f'User unsubscribed :(\n    {repr(sub)}')
    else:
        if not sub:
            flash(f"Subscriber email not found. You are not subscribed.", "danger")
        else:
            flash(f"Unable to unsubscribe. Incorrect update code.", "danger")
        current_app.logger.info(f'Failed to unsubscribe:\n    {email}')
    return redirect(url_for('page.home'))

@bp.route('/uploads/<string:filename>')
def uploads(filename):
    return send_from_directory(current_app.config['UPLOAD_DIR'], filename)

@bp.route('/rss/<path:path>')
def rss(path):
    path = f"/{path}"
    posts = None
    if path == '/all':
        page = Page.query.filter_by(slug='home').first()
        posts = Page.query.filter(or_(Page.template == 'post',Page.template == 'chapter'), Page.published == True).order_by(desc('pub_date')).all()
        current_app.logger.debug(posts)
    else:
        page = Page.query.filter_by(path=path,published=True).first()
        posts = Page.query.filter(or_(Page.template == 'post',Page.template == 'chapter'), Page.published == True, Page.parent_id == page.id).order_by(desc('pub_date')).all()
    if page:
        return render_template(f'page/rss.xml', page=page, posts=posts)
        rss_xml = render_template(f'page/rss.xml', page=page)
        response = make_response(rss_xml)
        response.headers['Content-Type'] = 'application/rss+xml'
        return response
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page), 404  

@bp.route('/<path:path>/glossary')
def glossary(path):
    Page.set_nav()
    path = f"/{path}"
    page = Page.query.filter_by(path=path).first()
    definitions = {}
    for t in Definition.TYPE_CHOICES:
        definitions[t[1]] = []

    current_app.logger.debug(f'DEFINITIONS: {definitions}')
    if page:
        for d in Definition.query.filter_by(parent_id=page.id).order_by('name').all():
            definitions[d.type.title()] += [d]
        code = request.args['code'] if 'code' in request.args else None
        if page.published or page.check_view_code(code):
            return render_template(f'page/glossary.html', 
                    page=page, 
                    glossary=True,
                    definitions=definitions,
                    type_choices=Definition.TYPE_CHOICES,
                    sorted=sorted,
                    len=len,
                )    
    current_app.logger.debug(f'DEFINITIONS: {definitions}')
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page), 404   

@bp.route('/<path:path>/latest')
def latest(path):
    Page.set_nav()
    path = f"/{path}"
    page = Page.query.filter_by(path=path).first()
    return redirect(url_for('page.index', path=page.latest().path))
    

@bp.route('/<path:path>')
def index(path):
    Page.set_nav()
    current_app.logger.debug(request.host_url)
    current_app.logger.debug(request.host.lower())
    if request.host.lower() == "sprig.houstonhare.com":
        path = f"/stories/sprig/{path}"
    else:
        path = f"/{path}"
    page = Page.query.filter_by(path=path).first()
    print(f"path: {path}")
    print(f"page: {page}")
    if page:
        code = request.args['code'] if 'code' in request.args else None
        if page.published or page.check_view_code(code):
            return render_template(f'page/{page.template}.html', page=page)    
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page), 404

@bp.before_app_first_request
def set_nav():
    Page.set_nav()
