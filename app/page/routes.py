from flask import (
        render_template, redirect, url_for, flash, session, request, 
        current_app, make_response, send_from_directory
    )
from app.page import bp
from app.page.forms import SearchForm, SubscribeForm
from app.models import Page, Tag, Subscriber
from app import db

@bp.route('/')
def home():
    Page.set_nav()
    page = Page.query.filter_by(path='/home',published=True).first()
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
    tags = Tag.query.all()
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
    for field in form:
        print(f"{field.name}: {field.data}")
    if form.validate_on_submit():
        print("Validated")
        sub = Subscriber(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
        )
        db.session.add(sub)
        db.session.commit()
        sub.welcome()
        flash('You have subscribed successfully!', 'success')
        return redirect(url_for('page.home'))
    return render_template('subscribe.html',
            form=form
        )

@bp.route('/unsubscribe/<string:email>')
def unsubscribe(email):
    sub = Subscriber.query.filter_by(email=email).first()
    if sub:
        db.session.delete(sub)
        db.session.commit()
        flash(f"{email} has been unsubscribed successfully. If you'd like to resubscribe, click the subscribe button in the bottom right of the screen.", "success")
    else:
        flash(f"Subscriber email not found. You are not subscribed.", "danger")
    return redirect(url_for('page.home'))

@bp.route('/uploads/<string:filename>')
def uploads(filename):
    return send_from_directory(current_app.config['UPLOAD_DIR'], filename)

@bp.route('/rss/<path:path>')
def rss(path):
    path = f"/{path}"
    page = Page.query.filter_by(path=path,published=True).first()
    if page:
        return render_template(f'page/rss.xml', page=page)
        #rss_xml = render_template(f'page/rss.xml', page=page)
        #response = make_response(rss_xml)
        #response.headers['Content-Type'] = 'application/rss+xml'
        #return response
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page)    

@bp.route('/<path:path>')
def index(path):
    Page.set_nav()
    path = f"/{path}"
    page = Page.query.filter_by(path=path).first()
    print(f"path: {path}")
    print(f"page: {page}")
    if page:
        code = request.args['code'] if 'code' in request.args else None
        if page.published or page.check_view_code(code):
            return render_template(f'page/{page.template}.html', page=page)    
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page)    

@bp.before_app_first_request
def set_nav():
    Page.set_nav()
