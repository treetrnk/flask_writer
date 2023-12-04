import re
import pytz
import os
import magic
import requests
import json
from flask import current_app, url_for, session, jsonify, render_template
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from datetime import datetime, timedelta, timezone
from time import sleep
from markdown import markdown
from sqlalchemy import desc
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import backref
from flask_mail import Mail, Message
from app import mail
from app.email import send_email
from discord_webhook import DiscordWebhook

tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('page_id', db.Integer, db.ForeignKey('page.id'), primary_key=True)
)

ver_tags = db.Table('ver_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('page_version_id', db.Integer, db.ForeignKey('page_version.id'), primary_key=True)
)

tags_defs = db.Table('tags_defs',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('definition_id', db.Integer, db.ForeignKey('definition.id'), primary_key=True)
)

##########
## USER ##
##########
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(64), index=True, unique=True)
    avatar = db.Column(db.String(500))
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    timezone = db.Column(db.String(150))
    comments = db.relationship('Comment', backref='user', lazy=True)

    def display_name(self):
        if self.name:
            return self.name
        return self.username

    def total_subscribers(self):
        return len(Subscriber.query.all())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __str__(self):
        return self.username

    def __repr__(self):
        return f"<User({self.username})>"


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

#################
## PAGEVERSION ##
#################
class PageVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column('Page', db.ForeignKey('page.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=True)
    dir_path = db.Column(db.String(500), nullable=True)
    path = db.Column(db.String(500), nullable=True)
    parent_id = db.Column(db.Integer(), db.ForeignKey('page.id'), nullable=True)
    template = db.Column(db.String(100))
    cover = db.Column(db.String(500), nullable=True)
    banner = db.Column(db.String(500), nullable=True)
    banner_video = db.Column(db.String(500), nullable=True)
    body = db.Column(db.Text(10000000))
    notes = db.Column(db.Text(5000000))
    tags = db.relationship('Tag', secondary=ver_tags, lazy='subquery', 
            backref=db.backref('page_versions', lazy=True))
    summary = db.Column(db.String(300), nullable=True)
    author_note = db.Column(db.String(5000), nullable=True)
    author_note_location = db.Column(db.String(20), default='bottom')
    sidebar = db.Column(db.String(5000), nullable=True)
    user_id = db.Column('User', db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='versions')
    notify_group = db.Column(db.String(100))
    sort = db.Column(db.Integer(), nullable=False, default=75)
    pub_date = db.Column(db.DateTime(), nullable=True)
    published = db.Column(db.Boolean(), default=False)
    edit_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

    def word_count(self):
        if self.body:
            try:
                return self.words
            except:
                words = len(re.findall("[a-zA-Z']+-?[a-zA-Z']*", self.body))
                read_time = str(round(words / 200)) + " - " + str(round(words / 150)) + " mins."
                self.words = words
            return self.words
        self.words = 0
        return self.words

    def local_pub_date(self, tz):
        if self.pub_date:
            utc = pytz.timezone('utc')
            local_tz = pytz.timezone(tz)
            pub_date = datetime.strptime(str(self.pub_date), '%Y-%m-%d %H:%M:%S')
            utcdate = pytz.UTC.localize(self.pub_date)
            return utcdate.astimezone(tz=local_tz)
        return None

    def __str__(self):
        return f"Ver. {self.id} - {self.title} ({self.path})"

    def __repr__(self):
        return f"<PageVersion({self.id}, {self.title}, {self.path})>"

##########
## PAGE ##
##########
class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=True)
    dir_path = db.Column(db.String(500), nullable=True)
    path = db.Column(db.String(500), nullable=True)
    parent_id = db.Column(db.Integer(), db.ForeignKey('page.id'), nullable=True)
    parent = db.relationship('Page', remote_side=[id], backref='children')
    template = db.Column(db.String(100))
    cover = db.Column(db.String(500), nullable=True)
    banner = db.Column(db.String(500), nullable=True)
    banner_video = db.Column(db.String(500), nullable=True)
    body = db.Column(db.Text(10000000))
    notes = db.Column(db.Text(5000000))
    tags = db.relationship('Tag', secondary=tags, lazy='subquery', 
            backref=db.backref('pages', order_by='Page.path', lazy=True))
    summary = db.Column(db.String(300), nullable=True)
    author_note = db.Column(db.String(5000), nullable=True)
    author_note_location = db.Column(db.String(20), default='bottom')
    sidebar = db.Column(db.String(5000), nullable=True)
    user_id = db.Column('User', db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='pages')
    notify_group = db.Column(db.String(100))
    sort = db.Column(db.Integer(), nullable=False, default=75)
    pub_date = db.Column(db.DateTime(), nullable=True)
    published = db.Column(db.Boolean(), default=False)
    edit_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    products = db.relationship('Product', backref='linked_page', lazy=True)
    versions = db.relationship('PageVersion', backref='current', primaryjoin=
                id==PageVersion.original_id)

    TEMPLATE_CHOICES = [
        ('page', 'Page'),
        ('post', 'Post'),
        ('shelf', 'Shelf'),
        ('story', 'Story'),
        ('book', 'Book'),
        ('chapter', 'Chapter'),
        ('blog', 'Blog'),
    ]

    AUTHOR_NOTE_LOCATIONS = [
        ('bottom', 'Bottom'),
        ('top', 'Top'),
    ]

    #def parent(self):
    #    return Page.query.filter_by(id=self.parent_id).first()

    def set_path(self):
        if self.parent_id:
            #current_app.logger.debug(f"PARENT ID: {self.parent_id}")
            parent = Page.query.filter_by(id=self.parent_id).first()
            #current_app.logger.debug(f"PARENT: {parent}")
            try:
                parent_path = parent.path
            except AttributeError:
                parent.set_path()
            self.path = f"{parent.path}/{self.slug}"
            self.dir_path = parent.path

        else:
            self.path = f"/{self.slug}"
            self.dir_path = "/"

    def replace_page_markup(text, hide=[]):
        result = text
        matches = re.findall('page\[(\d*)\|([a-zA-Z,]*)\]', text)
        #current_app.logger.debug(f'MATCHES: {matches}')
        for match in matches:
            pid = match[0]
            #current_app.logger.debug(f'PID: {pid}')
            hide = []
            hide = hide + match[1].split(',')
            #current_app.logger.debug(f'HIDE: {hide}')
            page = Page.query.filter_by(id = pid).first()
            if page:
                result = result.replace(f'page[{pid}|{match[1]}]', page.card(hide=hide))
                #current_app.logger.debug(result)
            else:
                result = result.replace(f'page[{pid}]', '')
        return result

    def add_lightbox_imgs(self, html):
        matches = re.finditer("(<img.*src=[\'\"](\S+)[\"\'].*\/>)", html)
        edits = []
        for match in matches:
            current_app.logger.debug(match.groups())
            if match.groups()[0] not in edits: 
                add_link = f'<a href="{match.groups()[1]}" data-lightbox="images">{match.groups()[0]}</a>'
                html = html.replace(match.groups()[0], add_link)
                edits += [match.groups()[0]]

        return html


    def html(self, field):
        if field == 'body':
            data = self.body
        if field == 'notes':
            data = self.notes
        if field == 'author_note':
            data = self.author_note
        data = markdown(data.replace('---', '<center>&#127793;</center>').replace('--', '&#8212;'))


        data = data.replace('<img ', '<img data-lightbox="images" ')
        data = Product.replace_product_markup(data)
        data = Page.replace_page_markup(data)
        return data

    def html_body(self):
        if self.body:
            body = markdown(self.body.replace('---', '<center>&#127793;</center>').replace('--', '&#8212;'))
            body = self.add_lightbox_imgs(body)
            body = Product.replace_product_markup(body)
            body = Page.replace_page_markup(body)
            return body
        return ''

    def text_body(self):
        pattern = re.compile(r'<.*?>')
        return pattern.sub('', self.html_body())

    def html_sidebar(self):
        sidebar = self.sidebar
        if self.template == 'chapter' or self.template == 'post':
            if self.parent_id:
                sidebar = self.parent.sidebar
        sidebar = markdown(sidebar)
        sidebar = sidebar.replace('<img ', '<img data-lightbox="images" ')
        sidebar = Product.replace_product_markup(sidebar)
        sidebar = Page.replace_page_markup(sidebar)
        return sidebar
    
    def description(self, length=247):
        if self.summary:
            return self.summary
        return self.text_body()[0:length] + '...'

    def view_code(self):
        #return str(datetime.now().year) + str(datetime.now().isocalendar()[1]) + self.slug
        return str(datetime.now().year) + str(datetime.now().month) + self.path + current_app.config['SECRET_KEY']

    def gen_view_code(self):
        if not self.published:
            return '?code=' + generate_password_hash(self.view_code())
        return ''

    def check_view_code(self, code):
        if code:
            return check_password_hash(code, self.view_code())
        return False
        
    def cover_path(self, always_return_img=False):
        cover = self.cover 
        if not self.cover and (self.template == 'chapter' or self.template == 'post'):
            if self.parent_id:
                cover = self.parent.cover 
        if cover:
            if 'http' in cover[0:5]:
                return cover
            else:
                return str(current_app.config['BASE_URL']) + cover
        if not always_return_img:
            return False
        else: 
            return str(current_app.config.get('DEFAULT_COVER_PATH'))
        
    def banner_path(self, always_return_img=False):
        banner = self.banner 
        if not self.banner and (self.template == 'chapter' or self.template == 'post'):
            if self.parent_id:
                banner = self.parent.banner 
        if banner:
            if 'http' in banner[0:5]:
                return banner
            else:
                return str(current_app.config['BASE_URL']) + banner
        if not always_return_img:
            return False
        else: 
            return str(current_app.config['DEFAULT_BANNER_PATH'])

    def cover_path(self, always_return_img=False, get_parent=True):
        cover = self.cover 
        if not self.cover and (self.template == 'chapter' or self.template == 'post'):
            if self.parent_id and get_parent:
                cover = self.parent.cover 
        if cover:
            if 'http' in cover[0:5]:
                return cover
            else:
                return str(current_app.config['BASE_URL']) + cover
        return False

    def meta_img(self):
        cover = self.cover_path(get_parent=False)
        banner = self.banner_path()
        if cover:
            return cover
        if banner:
            return banner
        return str(current_app.config['DEFAULT_FAVICON'])

    def section_name(self):
        if self.template == 'chapter' or self.template == 'post':
            if self.parent_id:
                return self.parent.title
        return self.title

    def pub_children(self, published_only=True, chapter_post_only=False):
        if published_only:
            if chapter_post_only:
                return Page.query.filter(
                        Page.template.in_(['chapter','post'])
                    ).filter_by(
                            parent_id=self.id,
                            published=True
                    ).order_by('sort','pub_date','title').all()
            return Page.query.filter_by(
                        parent_id=self.id,
                        published=True
                ).order_by('sort','pub_date','title').all()
        if chapter_post_only:
            return Page.query.filter(
                    Page.template.in_(['chapter','post'])
                ).filter_by(
                        parent_id=self.id,
                ).order_by('sort','pub_date','title').all()
        return Page.query.filter_by(
                    parent_id=self.id,
            ).order_by('sort','pub_date','title').all()

    def nav_children(self, cap=9):
        children = self.pub_children()
        if self.template == 'blog':
            return children[::-1][0:cap] if len(children) > cap else children[::-1]
        return children[0:cap] if len(children) > cap else children

    def child_comments(self, published_only=True, chapter_post_only=False):
        children = self.pub_children(published_only, chapter_post_only)
        comment_count = len(self.comments) or 0
        for child in children:
            comment_count += len(child.comments)
        return comment_count

    def comment_count(self):
        if self.template in ['blog','shelf','story']:
            return self.child_comments()
        return len(self.comments)

    def latest(self):
        if self.template == 'chapter' or self.template == 'post':
            return self.pub_siblings(chapter_post_only=True)[::-1][0]
        return self.pub_children(chapter_post_only=True)[::-1][0]

    def pub_siblings(self, published_only=True, chapter_post_only=False):
        if published_only: 
            if chapter_post_only:
                return Page.query.filter(
                        Page.template.in_(['chapter','post'])
                    ).filter_by(
                        parent_id=self.parent_id,
                        published=True
                    ).order_by('sort','pub_date','title').all()
            return Page.query.filter_by(
                    parent_id=self.parent_id,
                    published=True
                ).order_by('sort','pub_date','title').all()
        if chapter_post_only:
            return Page.query.filter(
                    Page.template.in_(['chapter','post'])
                ).filter_by(
                    parent_id=self.parent_id
                ).order_by('sort','title','pub_date').all()
        return Page.query.filter_by(parent_id=self.parent_id).order_by('sort','title','pub_date').all()

    def child_count(self, include_unpublished=False):
        if include_unpublished:
            return len(self.pub_children(published_only=False,chapter_post_only=True))
        return len(self.pub_children(chapter_post_only=True))

    def next_pub_sibling(self, published_only=True, chapter_post_only=True):
        try:
            if not published_only:
                raise Exception
            return self.next_sibling
        except Exception:
            siblings = self.pub_siblings(published_only, chapter_post_only=True)
            #current_app.logger.debug(siblings)
            current = False
            for sibling in siblings:
                if current:
                    if sibling.id != self.id:
                        self.next_sibling = sibling
                        return self.next_sibling
                if sibling.id == self.id:
                    current = True
            self.next_sibling = None
            return None

    def prev_pub_sibling(self, published_only=True, chapter_post_only=True):
        try:
            if not published_only:
                raise Exception
            return self.prev_sibling
        except Exception:
            siblings = self.pub_siblings(published_only, chapter_post_only=chapter_post_only)
            #current_app.logger.debug(siblings)
            prev = None
            for sibling in siblings:
                if sibling.id == self.id:
                    if prev and prev.id != self.id: 
                        self.prev_sibling = prev
                        return self.prev_sibling
                prev = sibling
            self.prev_sibling = None
            return None

    def ancestors(self):
        ancestors = []
        parent = Page.query.filter_by(id=self.parent_id).first()
        if parent:
            ancestors.append(parent)
            for p in parent.ancestors():
                ancestors.append(p)
        return ancestors

    def descendents(self):
        descendents = []
        children = Page.query.filter_by(parent_id=self.id).all()
        for child in children:
            descendents.append(child)
            for c in child.all_children():
                descendents.append(c)
        return descendents

    def card(self, hide=[]):
        return render_template('page/card.html',
                card_page=self,
                hide=hide,
            )

    def live_products(self, total=0, random=False):
        products = Product.query.filter_by(linked_page_id=self.id, active=True)
        if random:
            products = products.order_by(func.rand())
        else:
            products = products.order_by('sort','name')
        if total > 0:
            products = products.limit(total)
        return products.all()

    def word_count(self):
        if self.body:
            try:
                return self.words
            except:
                words = len(re.findall("[a-zA-Z']+-?[a-zA-Z']*", self.body))
                read_time = str(round(words / 200)) + " - " + str(round(words / 150)) + " mins."
                self.words = words
            return self.words
        self.words = 0
        return self.words

    def read_time(self):
        words = self.word_count()
        if words / 200 < 120:
            return str(round(words / 200)) + " - " + str(round(words / 150)) + " mins."
        return str(round(words / 200 / 60)) + " - " + str(round(words / 150 / 60)) + " hrs."

    def child_word_count(self, published_only=True):
        #try:
        #    return self.child_words
        #except:
        words = 0
        children = self.pub_children(published_only=published_only, chapter_post_only=True)
        for child in children:
            words += child.word_count()
        self.child_words = words
        return self.child_words

    def page_count(self, published_only=True):
        words_per_page = 275
        if self.template in ['blog','story']:
            return round(self.child_word_count(published_only) / words_per_page)
        return round(self.word_count() / words_per_page)

    def avg_child_word_count(self, published_only=True):
        total = 0
        children = self.pub_children(published_only=published_only, chapter_post_only=True)
        for child in children:
            total += child.word_count()
        return int(total / len(children)) if len(children) else total

    def child_read_time(self, published_only=True):
        words = self.child_word_count(published_only)
        if words / 200 < 120:
            return str(round(words / 200)) + " - " + str(round(words / 150)) + " mins."
        return str(round(words / 200 / 60)) + " - " + str(round(words / 150 / 60)) + " hrs."

    def child_write_time(self, published_only=True):
        hourly_words = 350
        words = self.child_word_count(published_only)
        #current_app.logger.debug(words)
        #current_app.logger.debug(published_only)
        if words / hourly_words < 2:
            return str(round(words / hourly_words * 60)) + " mins."
        if words / hourly_words > 48:
            return str(round(words / hourly_words / 24)) + " days"
        return str(round(words / hourly_words)) + " hrs."
    
    def local_pub_date(self, tz=None):
        if self.pub_date:
            utc = pytz.timezone('utc')
            try: 
                local_tz = pytz.timezone(tz)
            except:
                local_tz = datetime.now(timezone(timedelta(0))).astimezone().tzinfo 
            pub_date = datetime.strptime(str(self.pub_date), '%Y-%m-%d %H:%M:%S')
            utcdate = pytz.UTC.localize(self.pub_date)
            return utcdate.astimezone(tz=local_tz)
        return None

    def set_local_pub_date(self, date, tz):
        pub_date = datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(tz)
        pub_date = local_tz.localize(pub_date)
        self.pub_date = pub_date.astimezone(pytz.utc) 

    def send_to_discord_webhook(self):
        #current_app.logger.debug(current_app.config['DISCORD_WEBHOOK'])
        if current_app.config['DISCORD_WEBHOOK']:
            try: 
                #current_app.logger.debug('Trying to contact discord webhook')
                if self.notify_group in current_app.config['DISCORD_RELAY_GROUPS']:
                    sleep(3)
                    content = f"New {self.template} released! Here's **{self.title}**:\n"
                    content += current_app.config['BASE_URL'] + self.path
                    webhook = DiscordWebhook(url=current_app.config['DISCORD_WEBHOOK'], content=content)
                    response = webhook.execute()
            except Exception as e:
                current_app.logger.info(f'Failed to notify discord webhook ({self.title} - {self.id}). Exception: {e}')
                
    def notify_subscribers(self, group):
        current_app.logger.info('Notifying Group: ' + group)
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        parent_title = self.parent.title + ' - ' if self.parent else ''
        parent_title = '🌱' + parent_title if parent_title == 'Sprig - ' else parent_title
        subject=f"[New {self.template.title()}] {parent_title}{self.title}"
        body=f"Stories by Houston Hare\nNew Post: {parent_title}{self.title}\n{self.description()}\nRead more: {current_app.config['BASE_URL']}{self.path}"

        # DISCORD WEBHOOK
        self.send_to_discord_webhook()

        if group == "all":
            subs = Subscriber.query.all()
        else:
            subs = Subscriber.query.filter(Subscriber.subscription.contains(f",{group},")).all()
        
        if subs:
            for recipient in subs:
                send_email(
                        subject,
                        sender,
                        [recipient.email],
                        body,
                        render_template('email/subscriber-notification.html', page=self, recipient=recipient),
                    )

    def nav_list(self):
        nav = []
        return nav

    def set_nav():
        nav = []
        top_pages = Page.query.filter_by(published=True,parent_id=None).order_by('sort','pub_date','title').all()
        for top_page in top_pages:
            page = {
                    'id': top_page.id,
                    'title': top_page.title,
                    'path': top_page.path,
                    'children': [],
                }
            for child in top_page.nav_children():
                kid = {
                        'id': child.id,
                        'title': child.title,
                        'path': child.path,
                        'children': [],
                    }
                for grandchild in child.nav_children():
                    kid['children'].append({
                            'id': grandchild.id,
                            'title': grandchild.title,
                            'path': grandchild.path,
                            'children': [],
                         })
                page['children'].append(kid)
            nav.append(page)
        session['nav'] = nav


    def __str__(self):
        return f"{self.title} ({self.path})"

    def __repr__(self):
        return f"<Page({self.id}, {self.title}, {self.path})>"

#########
## TAG ##
#########
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(75), nullable=False)
    definitions = db.relationship('Definition', backref='tag', lazy='dynamic')

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Tag({self.name})>"

################
## SUBSCRIBER ##
################
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True) 
    first_name = db.Column(db.String(75), nullable=True)
    last_name = db.Column(db.String(75), nullable=True)
    subscription = db.Column(db.String(1000), nullable=False, default='all')
    sub_date = db.Column(db.DateTime(), default=datetime.utcnow)

    def all_subscribers():
        return [s.email for s in Subscriber.query.all()]

    def name_if_given(self, full=False):
        if full:
            if self.first_name and self.last_name:
                return f'{self.first_name} {self.last_name}'
        return self.first_name if self.first_name else ''

    def update_code(self):
        return self.email + current_app.config['SECRET_KEY']

    def gen_update_code(self):
        return generate_password_hash(self.update_code())

    def check_update_code(self, code):
        if code:
            return check_password_hash(code, self.update_code())
        return False

    def welcome(self):
        page=Page.query.filter_by(slug='subscriber-welcome').order_by('pub_date').first()
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        relative_path = '/products/subscriber-downloads'
        path = current_app.config['BASE_DIR'] + relative_path
        product = Product.query.filter_by(active=True,download_path='subscriber-download.zip').first()
        if product:
            dl_output = product.download_output()
        else:
            dl_output = {'text':'','html':''}
        #attachments = []
        #current_app.logger.debug(path)
        #current_app.logger.debug('..' + relative_path)
        #if os.path.isdir(path):
        #    current_app.logger.debug('IT IS A DIR')
        #    for filename in os.listdir(path):
        #        file_path = path + '/' + filename
        #        attachments += [(
        #            filename, 
        #            magic.Magic(mime=True).from_file(file_path), 
        #            current_app.open_resource(file_path).read(),
        #        )]
        send_email(
                page.title, #subject
                sender,
                [self.email],
                page.text_body() + dl_output['text'], #body
                render_template('email/with-greeting.html', 
                        page=page, 
                        html=page.html_body() + dl_output['html'],
                        recipient=self,
                    ),
                #attachments = attachments,
            )
        """
        [
            (
                'sprig-issue-1.zip',
                'application/zip',
                current_app.open_resource('../products/sprig-issue-1.zip').read(),
            ),
            (
                'sprig-bookmarks.pdf',
                'application/pdf',
                current_app.open_resource('../products/sprig-bookmarks.pdf').read(),
            ),
        ],
        """

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

    def __repr__(self):
        return f"<Subscriber({self.email}, {self.first_name} {self.last_name})>"

################
## DEFINITION ##
################
class Definition(db.Model):
    
    TYPE_CHOICES = [
        ('events', 'Events'),
        ('locations', 'Locations'),
        ('people', 'People'),
        ('races', 'Races'),
        ('other', 'Other'),
    ]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    body = db.Column(db.String(5000), nullable=False)
    hidden_body = db.Column(db.String(5000))
    type = db.Column(db.String(20), nullable=False, default='other')
    #tags = db.relationship('Tag', secondary=tags_defs, lazy='subquery', 
    #        backref=db.backref('definitions', lazy=True))
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=True)
    parent_id = db.Column(db.Integer(), db.ForeignKey('page.id'), nullable=True)
    parent = db.relationship('Page', backref='definitions')
    active = db.Column(db.Boolean, default=True)

    def html_body(self, hidden=False):
        body = self.hidden_body if hidden else self.body
        if body is None:
            body = ''
        return markdown(body.replace('---', '<center>&#127793;</center>').replace('--', '&#8212;'))

    def text_body(self, hidden=False):
        body = self.html_body(hidden)
        pattern = re.compile(r'<.*?>')
        return pattern.sub('', body)

    def short_body(self):
        threshold = 37
        body = self.text_body()
        if len(body) > threshold:
            return body[0:threshold] + '...'
        return body

    def __str__(self):
        return f"{self.name} ({self.short_body()})"

    def __repr__(self):
        return f"<Definition({self.id}, {self.name}, {self.short_body()})>"


##########
## LINK ##
##########
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    text = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100))
    format = db.Column(db.String(100))
    url = db.Column(db.String(500), nullable=False)
    sort = db.Column(db.Integer, default=500)
    product = db.relationship('Product', backref=backref('links', order_by=sort))

    def set_default(self):
        links = Link.query.filter_by(product_id=self.product_id).all()
        for link in links:
            link.default = False
        self.default = True

    def text_simple(self):
        return self.text.replace('Buy it on ','').replace('Buy it at ','').replace('Buy on ','').replace('Buy at ', '')

    def format_icon(self):
        if self.format == 'Paperback':
          return '<i class="fas fa-book-open"></i>'
        elif self.format == 'Hardcover':
          return '<i class="fas fa-book"></i>'
        elif self.format == 'eBook':
          return '<i class="fas fa-file"></i>'
        return ''

    def __str__(self):
        return f"{self.text} ({self.url[0:20]}...)"

    def __repr__(self):
        return f"<Link({self.id}, {self.text}, {self.url[:20]}...)>"
    

#############
## PRODUCT ##
#############
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), nullable=False)
    ghost_link = db.Column(db.String(500))
    price = db.Column(db.String(10), nullable=False, default='$0.00')
    sale_price = db.Column(db.String(10), default='$0.00')
    description = db.Column(db.String(1000))
    image = db.Column(db.String(500), default="/uploads/missing-product.png")
    download_path = db.Column(db.String(500))
    sort = db.Column(db.Integer, default=500)
    linked_page_id = db.Column(db.Integer(), db.ForeignKey('page.id'), nullable=True)
    category_id = db.Column(db.Integer(), db.ForeignKey('category.id'), nullable=True)
    on_sale = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=False)

    def card(self, hide=[]):
        return render_template('shop/card.html',
                product=self.unghosted(),
                hide=hide,
            )

    def simple_price(self):
        if self.on_sale and self.sale_price:
            return self.sale_price.replace('$', '').replace('.','')
        return self.price.replace('$', '').replace('.','')

    def grouped_links(self, export_json=False):
        try:
            if self.ghost:
                return self.glinks
        except:
            pass
        links = Link.query.filter_by(product_id=self.id).order_by('format','sort','text').all()
        link_list = []
        current_format = ''
        current_list = []
        for link in links:
            if link.format != current_format:
                current_format = link.format
                link_list.insert(0, current_list)
                current_list = []
            if export_json:
                ldata = {}
                ldata['id'] = link.id
                ldata['text'] = link.text
                ldata['icon'] = link.icon
                ldata['format'] = link.format
                ldata['url'] = link.url
                ldata['sort'] = link.sort
                current_list += [ldata]
            else:
                current_list += [link]
        link_list.insert(0, current_list)
        link_list = [i for i in link_list if i]
        #current_app.logger.debug(link_list)
        return link_list

    def replace_product_markup(text, hide=[]):
        result = text
        matches = re.findall('product\[(\d*)\|([a-zA-Z,]*)\]', text)
        #current_app.logger.debug(f'MATCHES: {matches}')
        for match in matches:
            pid = match[0]
            #current_app.logger.debug(f'PID: {pid}')
            hide = []
            hide = hide + match[1].split(',')
            #current_app.logger.debug(f'HIDE: {hide}')
            product = Product.query.filter_by(id = pid).first()
            if product:
                result = result.replace(f'product[{pid}|{match[1]}]', product.card(hide=hide))
                #current_app.logger.debug(result)
            else:
                result = result.replace(f'product[{pid}]', '')
        return result

    def ghosted(self):
        #current_app.logger.debug('SOURCE LINKS')
        #current_app.logger.debug(self.links)
        data = {}
        data['name'] = self.name
        data['ghost_link'] = self.ghost_link
        data['price'] = self.price
        data['sale_price'] = self.sale_price
        data['description'] = self.description
        data['image'] = self.image
        data['on_sale'] = self.on_sale
        data['links'] = []

        ldata = {}
        ldata['text'] = current_app.config.get('SITE_NAME')
        ldata['icon'] = 'fas fa-shopping-bag'
        ldata['format'] = ''
        ldata['url'] = f'{current_app.config.get("BASE_URL")}/shop/{self.slug}'
        ldata['sort'] = 1

        data['links'] += [ldata]
            
        for link in self.links:
            ldata = {}
            ldata['id'] = link.id
            ldata['text'] = link.text
            ldata['icon'] = link.icon
            ldata['format'] = link.format
            ldata['url'] = link.url
            ldata['sort'] = link.sort

            data['links'] += [ldata]
        
        data['grouped_links'] = self.grouped_links(export_json=True)
        #current_app.logger.debug('GROUPED LINKS')
        #current_app.logger.debug(data['grouped_links'])

        return data

    def unghosted(self):
        if not self.ghost_link:
            return self

        try:
            response = requests.get(self.ghost_link)
            data = json.loads(response.text)
        except Exception:
            return self
        
        new_self = Product()
        new_self.id = self.id + 5555
        new_self.name = data.get('name') or self.name
        new_self.slug = self.slug
        new_self.ghost_link = self.ghost_link
        new_self.price = data.get('price') or self.price
        new_self.sale_price = data.get('sale_price') or self.sale_price
        new_self.description = data.get('description') or self.description
        new_self.image = data.get('image') or self.image
        new_self.on_sale = data.get('on_sale') or self.on_sale
        new_self.active = self.active
        new_self.glinks = []
        
        #current_app.logger.debug('MID SELF LINKS')
        #current_app.logger.debug(data.get('links'))
        for link_data in data.get('links'):
            link = Link()
            link.id = (link_data.get('id') or 0) + 5555
            link.product_id = new_self.id
            link.text = link_data.get('text')
            link.icon = link_data.get('icon')
            link.format = link_data.get('format')
            link.url = link_data.get('url')
            link.sort = link_data.get('sort')

            new_self.links.append(link)

        for form in data.get('grouped_links'):
            format_group = []
            for link_data in form:
                link = Link()
                link.id = (link_data.get('id') or 0) + 5555
                link.product_id = new_self.id
                link.text = link_data.get('text')
                link.icon = link_data.get('icon')
                link.format = link_data.get('format')
                link.url = link_data.get('url')
                link.sort = link_data.get('sort')
                
                format_group += [link]
            new_self.glinks += [format_group]

        #current_app.logger.debug('NEW SELF LINKS')
        #current_app.logger.debug(new_self.links)

        new_self.ghost = True
        return new_self

    def send(self, recipients=[]):
        page=Page.query.filter_by(slug='purchase-thank-you').order_by('pub_date').first()
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        relative_path = '/products'
        path = current_app.config['BASE_DIR'] + relative_path
        #current_app.logger.debug(path)
        #current_app.logger.debug('..' + relative_path)
        file_path = path + '/' + self.download_path
        dl_output = self.download_output()
        #attachments = [(
        #    os.path.basename(file_path), 
        #    magic.Magic(mime=True).from_file(file_path), 
        #    current_app.open_resource(file_path).read(),
        #)]
        send_email(
                f'{self.name} - eBook Delivery', #subject
                sender,
                recipients,
                page.text_body() + dl_output['text'], #body
                render_template('email/manual.html', 
                        page=page, 
                        body=page.html_body() + dl_output['html'],
                    ),
         #       attachments = attachments,
            )

    def download_code(self, day_offset=0):
        today = datetime.now().date() + timedelta(days=day_offset)
        return today.strftime('%Y%m%d') + str(self.id) + current_app.config['SECRET_KEY']

    def gen_download_code(self, day_offset=0):
        return '?code=' + generate_password_hash(self.download_code(day_offset=day_offset))

    def verify_download(self, access_code, days=7):
        result = False
        if access_code:
            while days >= 0 and result == False:
                if check_password_hash(access_code, self.download_code(day_offset = 0 - days)):
                    result = True
                days -= 1
        return result

    def download_link(self, day_offset=0):
        return current_app.config.get('BASE_URL') + url_for('shop.download', obj_id=self.id) + self.gen_download_code(day_offset=day_offset)

    def download_output(self, include_instructions=True):
        valid_until = (datetime.now() + timedelta(days = 7)).strftime('%b. %-d, %Y')
        instructions = f"The following link is valid until {valid_until}. Please download your file before then.\n\r"
        text = "\n\r"
        html = "<br />"
        if include_instructions:
            text += f"YOUR DOWNLOAD\n{instructions}\n\r"
            html += f"<h3>Your Download</h3><p>{instructions}</p>"
        text += self.name + ' - ' + self.download_link()
        html += f"""
            <ul>
                <li>
                    <h4>
                        <a href="{self.download_link()}">
                            {self.name} - Download Here
                        </a>
                    </h4>
                </li>
            </ul>
            """
        return {
                'text': text,
                'html': html
            }



    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<Product({self.id}, {self.name})>"

##############
## CATEGORY ##
##############
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    icon = db.Column(db.String(150), nullable=True)
    default = db.Column(db.Boolean, default=False, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updater_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<Category({self.id}, {self.name})>"

############
## RECORD ##
############
class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(150), nullable=False, default='write')
    words = db.Column(db.Integer)
    start_words = db.Column(db.Integer, nullable=False)
    end_words = db.Column(db.Integer, nullable=False)
    overall_words = db.Column(db.Integer)
    comment = db.Column(db.String(200))
    minutes = db.Column(db.Float)
    words_per_minute = db.Column(db.Integer)
    date = db.Column(db.Date, default=datetime.now)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    ACTION_CHOICES = [
            ('write', 'Write'),
            ('edit', 'Edit'),
            ('plan', 'Plan'),
        ]

    def words_by_day(day):
        records = Record.query.filter_by(date=day,action='write').order_by(desc('words')).all()
        daily_total = 0
        minutes = 0
        for r in records:
            daily_total += r.words
            minutes += r.minutes if r.minutes else 0
        overall_words = records[0].overall_words if records else 0
        return {
                'daily': daily_total, 
                'total': overall_words, 
                'sessions': len(records), 
                'session_avg': int(daily_total / len(records)) if records else 0,
                'minutes': minutes,
                'words_per_minute': int(daily_total / minutes) if minutes else 0,
                'best': records[0].words if records else 0,
                'date': f'{day.strftime("%a %b")} {day.day}',
            }

    def stats():
        highest_daily = Record.query(func.sum(Record.words).label('daily_total')).group_by(Record.date).order_by(desc('daily_total')).all()
        best_session = Record.query.order_by(desc('words')).all()
        most_sessions = Record.query(func.count(Record.words).label('sessions')).group_by(Record.date).all()

    def __str__(self):
        return f"{self.date} ({self.words} words)"

    def __repr__(self):
        return f"<Record:{self.date} ({self.words} words)>"

#############
## COMMENT ##
#############
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150))
    body = db.Column(db.String(5000), nullable=False)
    reaction = db.Column(db.String(50), nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    reply_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replied_comment = db.relationship('Comment', remote_side=[id], backref='replies')
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=True)
    page = db.relationship('Page', backref=backref('comments', order_by='Comment.created.asc()', lazy=True))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product = db.relationship('Product', backref=backref('comments', order_by='Comment.created.asc()', lazy=True))
    ip = db.Column(db.String(40), nullable=False)
    session_id =db.Column(db.String(200), nullable=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def author(self):
        if self.user_id:
            return self.user.display_name()
        return self.name


    def html_body(self):
        links = re.findall(r'https?:\/\/\S*', self.body)
        unique_links = []
        for link in links:
            if link not in unique_links:
                unique_links += [link]
        body = re.sub('<[^<]+?>', '', self.body)
        for link in unique_links:
            body = body.replace(
                    link,
                    f' <a href="{link}" target="_blank">{link}</a> '
                )
        body = re.sub(r'\n[\n\r]+', '<br /><br />', body)
        body = body.replace('\n', '<br />')

        return body

    def snippet(self):
        cutoff = 40
        if len(self.body) > cutoff:
            return self.body[0:cutoff] + '...'
        return self.body

    def notify(self):
        current_app.logger.info('Notifiying admin of comment')
        obj = None
        obj_name = ''
        obj_link = ''
        page = None

        if self.page_id:
            obj = self.page
            obj_name = obj.title
            obj_link = current_app.config['BASE_URL'] + obj.path
            page = self.page
        else:
            obj = self.product
            obj_name = obj.name
            obj_link = url_for('shop.view', slug=obj.slug)
            page = Page.query.filter_by(slug='home').first()

        sender = current_app.config['MAIL_DEFAULT_SENDER']
        subject=f"[New Comment] {obj_name} - {self.author()}"
        body=f"The following comment was made by {self.author()} on the {obj.__class__.__name__} {obj_name}.\n\n{self.body}\n\nRead more: {obj_link}"

        if current_app.config.get('ADMINS'):
            for recipient in current_app.config['ADMINS']:
                send_email(
                        subject,
                        sender,
                        [recipient],
                        body,
                        render_template('email/comment-notification.html', 
                                page=page, 
                                comment=self,
                                recipient=recipient,
                                obj=obj,
                                obj_name=obj_name,
                                obj_link=obj_link,
                            ),
                    )

    def notify_reply(self):
        if self.reply_id and self.replied_comment:
            if self.replied_comment.email or self.replied_comment.user:
                recipient_sub = Subscriber.query.filter_by(email=self.replied_comment.email).first()
                if recipient_sub and ',Comment Replies,' in recipient_sub.subscription:
                    current_app.logger.info('Notifiying commenter of reply')
                    recipients = [recipient_sub]
                    obj = None
                    obj_name = ''
                    obj_link = ''
                    page = None

                    if self.page_id:
                        obj = self.page
                        obj_name = obj.title
                        obj_link = current_app.config['BASE_URL'] + obj.path
                        page = self.page
                    else:
                        obj = self.product
                        obj_name = obj.name
                        obj_link = url_for('shop.view', slug=obj.slug)
                        page = Page.query.filter_by(slug='home').first()

                    sender = current_app.config['MAIL_DEFAULT_SENDER']
                    subject=f"[Comment Reply] {obj_name} - {self.author()}"
                    body=f"{self.author()} replied to your comment on the {obj.__class__.__name__} {obj_name}.\n\n{self.body}\n\nRead more: {obj_link}"

                    for recipient in recipients:
                        send_email(
                                subject,
                                sender,
                                [recipient.email],
                                body,
                                render_template('email/comment-notification.html', 
                                        page=page, 
                                        comment=self,
                                        recipient=recipient,
                                        obj=obj,
                                        obj_name=obj_name,
                                        obj_link=obj_link,
                                        reply=True,
                                    ),
                            )

    def __str__(self):
        return f"{self.name} - {self.snippet()}"

    def __repr__(self):
        return f"<Comment:{self.name} {self.snippet()}>"

