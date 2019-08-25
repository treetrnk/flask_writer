from flask import current_app, url_for, session, jsonify, render_template
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from datetime import datetime
from markdown import markdown
from sqlalchemy import desc
from flask_mail import Mail, Message
from app import mail
from app.email import send_email
import re
import pytz

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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    pages = db.relationship('Page', backref='user', lazy='dynamic')
    about_me = db.Column(db.String(140))
    timezone = db.Column(db.String(150))

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

class PageVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column('Page', db.ForeignKey('page.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=True)
    dir_path = db.Column(db.String(500), nullable=True)
    path = db.Column(db.String(500), nullable=True)
    parent_id = db.Column(db.Integer(), db.ForeignKey('page.id'), nullable=True)
    template = db.Column(db.String(100))
    banner = db.Column(db.String(500), nullable=True)
    body = db.Column(db.String(10000000))
    notes = db.Column(db.Text(5000000))
    tags = db.relationship('Tag', secondary=ver_tags, lazy='subquery', 
            backref=db.backref('page_versions', lazy=True))
    summary = db.Column(db.String(300), nullable=True)
    sidebar = db.Column(db.String(5000), nullable=True)
    user_id = db.Column('User', db.ForeignKey('user.id'), nullable=False)
    sort = db.Column(db.Integer(), nullable=False, default=75)
    pub_date = db.Column(db.DateTime(), nullable=True)
    published = db.Column(db.Boolean(), default=False)
    edit_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

    def word_count(self):
        try:
            return self.words
        except:
            words = len(re.findall("[a-zA-Z']+-?[a-zA-Z']*", self.body))
            read_time = str(round(words / 200)) + " - " + str(round(words / 150)) + " mins."
            self.words = words
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

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=True)
    dir_path = db.Column(db.String(500), nullable=True)
    path = db.Column(db.String(500), nullable=True)
    parent_id = db.Column(db.Integer(), db.ForeignKey('page.id'), nullable=True)
    parent = db.relationship('Page', remote_side=[id], backref='children')
    template = db.Column(db.String(100))
    banner = db.Column(db.String(500), nullable=True)
    body = db.Column(db.String(10000000))
    notes = db.Column(db.Text(5000000))
    tags = db.relationship('Tag', secondary=tags, lazy='subquery', 
            backref=db.backref('pages', lazy=True))
    summary = db.Column(db.String(300), nullable=True)
    sidebar = db.Column(db.String(5000), nullable=True)
    user_id = db.Column('User', db.ForeignKey('user.id'), nullable=False)
    sort = db.Column(db.Integer(), nullable=False, default=75)
    pub_date = db.Column(db.DateTime(), nullable=True)
    published = db.Column(db.Boolean(), default=False)
    edit_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    versions = db.relationship('PageVersion', backref='current', primaryjoin=
                id==PageVersion.original_id)

    TEMPLATE_CHOICES = [
        ('page', 'Page'),
        ('post', 'Post'),
        ('story', 'Story'),
        ('book', 'Book'),
        ('chapter', 'Chapter'),
        ('blog', 'Blog'),
    ]

    #def parent(self):
    #    return Page.query.filter_by(id=self.parent_id).first()

    def set_path(self):
        if self.parent_id:
            print(f"PARENT ID: {self.parent_id}")
            parent = Page.query.filter_by(id=self.parent_id).first()
            print(f"PARENT: {parent}")
            try:
                parent_path = parent.path
            except AttributeError:
                parent.set_path()
            self.path = f"{parent.path}/{self.slug}"
            self.dir_path = parent.path

        else:
            self.path = f"/{self.slug}"
            self.dir_path = "/"

    def html(self, field):
        if field == 'body':
            return markdown(self.body.replace('---', '<center>&#127793;</center>').replace('--', '&#8212;'))
        if field == 'notes':
            return markdown(self.notes.replace('---', '<center>&#127793;</center>').replace('--', '&#8212;'))

    def html_body(self):
        return markdown(self.body.replace('---', '<center>&#127793;</center>').replace('--', '&#8212;'))

    def text_body(self):
        pattern = re.compile(r'<.*?>')
        return pattern.sub('', self.html_body())

    def html_sidebar(self):
        if self.template == 'chapter' or self.template == 'post':
            if self.parent_id:
                return markdown(self.parent.sidebar)
        return markdown(self.sidebar)
    
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
        
    def banner_path(self):
        banner = self.banner 
        if not self.banner and (self.template == 'chapter' or self.template == 'post'):
            if self.parent_id:
                banner = self.parent.banner 
        if banner:
            if 'http' in banner[0:5]:
                return banner
            else:
                return str(current_app.config['BASE_URL']) + banner
        return False

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

    def next_pub_sibling(self, published_only=True):
        try:
            if not published_only:
                raise Exception
            return self.next_sibling
        except Exception:
            siblings = self.pub_siblings(published_only)
            print(siblings)
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

    def prev_pub_sibling(self, published_only=True):
        try:
            if not published_only:
                raise Exception
            return self.prev_sibling
        except Exception:
            siblings = self.pub_siblings(published_only)
            print(siblings)
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

    def word_count(self):
        try:
            return self.words
        except:
            words = len(re.findall("[a-zA-Z']+-?[a-zA-Z']*", self.body))
            read_time = str(round(words / 200)) + " - " + str(round(words / 150)) + " mins."
            self.words = words
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

    def avg_child_word_count(self, published_only=True):
        total = 0
        children = self.pub_children(published_only=published_only, chapter_post_only=True)
        for child in children:
            total += child.word_count()
        return int(total / len(children))

    def child_read_time(self, published_only=True):
        words = self.child_word_count(published_only)
        if words / 200 < 120:
            return str(round(words / 200)) + " - " + str(round(words / 150)) + " mins."
        return str(round(words / 200 / 60)) + " - " + str(round(words / 150 / 60)) + " hrs."

    def child_write_time(self, published_only=True):
        hourly_words = 500
        words = self.child_word_count(published_only)
        print(words)
        print(published_only)
        if words / hourly_words < 2:
            return str(round(words / hourly_words * 60)) + " mins."
        return str(round(words / hourly_words)) + " hrs."
    
    def local_pub_date(self, tz):
        if self.pub_date:
            utc = pytz.timezone('utc')
            local_tz = pytz.timezone(tz)
            pub_date = datetime.strptime(str(self.pub_date), '%Y-%m-%d %H:%M:%S')
            utcdate = pytz.UTC.localize(self.pub_date)
            return utcdate.astimezone(tz=local_tz)
        return None

    def set_local_pub_date(self, date, tz):
        pub_date = datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(tz)
        pub_date = local_tz.localize(pub_date)
        self.pub_date = pub_date.astimezone(pytz.utc) 
                
    def notify_subscribers(self):
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        parent_title = self.parent.title + ' - ' if self.parent else ''
        parent_title = '🌱' + parent_title if parent_title == 'Sprig - ' else parent_title
        subject=f"New Post: {parent_title}{self.title}"
        body=f"Stories by Houston Hare\nNew Post: {parent_title}{self.title}\n{self.description()}\nRead more: {current_app.config['BASE_URL']}{self.path}"
        for recipient in Subscriber.query.all():
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
            for child in top_page.pub_children():
                kid = {
                        'id': child.id,
                        'title': child.title,
                        'path': child.path,
                        'children': [],
                    }
                for grandchild in child.pub_children():
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

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(75), nullable=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Tag({self.name})>"

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True) 
    first_name = db.Column(db.String(75), nullable=True)
    last_name = db.Column(db.String(75), nullable=True)
    subscription = db.Column(db.String(100), nullable=False, default='all')
    sub_date = db.Column(db.DateTime(), default=datetime.utcnow)

    SUBSCRIPTION_CHOICES = [
            ('all','All'),
            ('sprig','Sprig'),
            ('blog','Blog'),
        ]

    def all_subscribers():
        return [s.email for s in Subscriber.query.all()]

    def name_if_given(self, full=False):
        if full:
            if self.first_name and self.last_name:
                return f'{self.first_name} {self.last_name}'
        return self.first_name if self.first_name else ''

    def welcome(self):
        page=Page.query.filter_by(slug='subscriber-welcome').order_by('pub_date').first()
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        send_email(
                page.title, #subject
                sender,
                [self.email],
                page.text_body(), #body
                render_template('email/with-greeting.html', 
                        page=page, 
                        html=page.html_body(),
                        recipient=self,
                    ),
            )

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

    def __repr__(self):
        return f"<Subscriber({self.email}, {self.first_name} {self.last_name})>"

class Definition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    body = db.Column(db.String(5000), nullable=False)
    hidden_body = db.Column(db.String(5000))
    tags = db.relationship('Tag', secondary=tags_defs, lazy='subquery', 
            backref=db.backref('definitions', lazy=True))
    parent_id = db.Column(db.Integer(), db.ForeignKey('page.id'), nullable=True)
    parent = db.relationship('Page', backref='definitions')

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
