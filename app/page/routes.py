import sys
import requests
from flask import (
        render_template, redirect, url_for, flash, session, request, 
        current_app, make_response, send_from_directory, send_file
    )
from app.page import bp
from app.page.forms import SearchForm, SubscribeForm, SubscriptionForm, CommentForm, AuthenticatedCommentForm
from sqlalchemy import or_, desc
from app.models import Page, Tag, Subscriber, Definition, Link, Product, Comment
from app import db
from gtts import gTTS
from app.admin.functions import log_new, log_change
from flask_login import current_user

@bp.route('/')
def home():
    comment_form = AuthenticatedCommentForm() if current_user.is_authenticated else CommentForm()
    comment_form.subscribe.data = False if current_user.is_authenticated else True
    Page.set_nav()
    page = Page.query.filter_by(slug='home',published=True).first()
    if page:
        comment_form.page_id.data = page.id
        return render_template(f'page/{page.template}.html', page=page)
    return render_template('home.html', 
            page='page', 
            comment_form=comment_form,
            js='comments.js'
        )

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
            )
    if keyword:
        results = Page.query.filter(
                Page.body.ilike(f'%{keyword}%'),
                Page.published == True
            )
    results = results.order_by(Page.sort.desc(), Page.pub_date.desc(),'title').all() if results else None
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
    form.subscription.choices = current_app.config['SUBSCRIPTION_GROUPS']
    form.subscription.choices += [('Comment Replies', 'Comment Replies')]
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
    form.subscription.data = [i[0] for i in current_app.config['SUBSCRIPTION_GROUPS']]
    return render_template('subscribe.html',
            form=form
        )

@bp.route('/update-subscription/<string:email>/<string:code>', methods=['GET','POST'])
def subscription(email, code):
    sub = Subscriber.query.filter_by(email=email).first()
    if sub and sub.check_update_code(code):
        Page.set_nav()
        form = SubscriptionForm()
        form.subscription.choices = current_app.config['SUBSCRIPTION_GROUPS'] + [('Comment Replies', 'Comment Replies')]
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

@bp.route('/submit-comment', methods=['POST'])
def submit_comment():
    form = AuthenticatedCommentForm() if current_user.is_authenticated else CommentForm()
    if form.validate_on_submit():
        current_app.logger.debug(request.form)
        captcha_data = {
                'secret': current_app.config['RECAPTCHA_SECRET'],
                'response': request.form.get('token'),
            }
        resp = requests.post('https://www.google.com/recaptcha/api/siteverify', captcha_data)
        response_data = resp.json()
        current_app.logger.debug(response_data)
        if current_app.config.get('DEVELOPMENT'):
            response_data['success'] = True #REMOVE
        if response_data.get('success'):
            form.reply_id.data = form.reply_id.data if form.reply_id.data else None
            form.page_id.data = form.page_id.data if form.page_id.data else None
            form.product_id.data = form.product_id.data if form.product_id.data else None
            comment = Comment()
            form.populate_obj(comment)
            current_app.logger.debug(f'REPLY ID: {comment.reply_id}')
            comment.ip = request.remote_addr
            if current_user.is_authenticated:
                comment.user_id = current_user.id
                comment.name = current_user.display_name()
                comment.email = current_user.email
            db.session.add(comment)
            db.session.commit()
            log_new(comment, 'added a comment')
            flash('Comment added.', 'success')
            comment.notify() # notify admin
            if comment.email:
                subscriber = Subscriber.query.filter_by(email=comment.email).first()
                if not subscriber: 
                    subscriber = Subscriber(
                            first_name = comment.name,
                            email = comment.email,
                            subscription = ',Comment Replies,'
                        )
                    if form.subscribe.data:
                        subscriber.subscription += ','.join([i[0] for i in current_app.config['SUBSCRIPTION_GROUPS']]) + ','
                    db.session.add(subscriber)
                    db.session.commit()

                    if form.subscribe.data:
                        log_new(subscriber, 'subscribed')
                        flash('Subscribed!', 'success')
                        subscriber.welcome()
                else:
                    log_orig = log_change(subscriber)
                    subscriber.subscription = ',Comment Replies,' 
                    if form.subscribe.data:
                        subscriber.subscription += ','.join([i[0] for i in current_app.config['SUBSCRIPTION_GROUPS']]) + ','
                    log_change(log_orig, subscriber, 'updated subscriptions')
                    db.session.commit()
                    flash('You are already subscribed!', 'info')
            else:
                if form.subscribe.data:
                    flash('You must provide an email address to subscribe. Please <a href="/subscribe">subscribe here</a> instead.', 'info')
            comment.notify_reply() # Notify commenter replied to        
        else:
            flash('Unable to save comment. Recaptcha flagged you as a bot. If you are not a bot, please try submitting your comment again.', 'danger')
    return redirect(request.referrer)

@bp.route('/hide-subscribe-banner', methods=['POST'])
def hide_subscribe_banner():
    session['hide_subscribe_banner'] = True
    current_app.logger.debug('Subscribe banner hidden')
    return 'true'

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

@bp.route('/tts/<path:path>')
def tts(path):
    path = f"/{path}"
    page = Page.query.filter_by(path=path,published=True).first()
    if page:
        parent = page.parent.title if page.parent and page.template in ['post','chapter'] else ''
        text = f'You are listening to a generated audio file of {parent}, {page.title} by {current_app.config["SITE_NAME"]}. For more of this storie, please visit {current_app.config["PRETTY_URL"]}. '
        output = gTTS(text=text + page.text_body(), lang='en')
        filename = '/tmp/' + parent + page.slug + '.mp3'
        output.save(filename)
        return send_file(filename, as_attachment=True)

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
    comment_form = AuthenticatedCommentForm() if current_user.is_authenticated else CommentForm()
    comment_form.subscribe.data = False if current_user.is_authenticated else True
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
        comment_form.page_id.data = page.id
        code = request.args['code'] if 'code' in request.args else None
        if page.published or page.check_view_code(code):
            return render_template(f'page/{page.template}.html', 
                    page=page, 
                    comment_form=comment_form,
                    js='comments.js')    
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page), 404
