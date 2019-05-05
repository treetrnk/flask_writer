from flask import render_template, redirect, url_for, flash, session, request, current_app
from app.page import bp
from app.page.forms import SearchForm
from app.models import Page, Tag

@bp.route('/')
def home():
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
