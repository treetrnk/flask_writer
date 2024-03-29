import os

basedir = os.path.abspath(os.path.dirname(__file__))
datadir = os.path.join(os.path.dirname(basedir), 'data/flask_writer/')
templatedir = os.path.join(basedir, 'app/templates/')
uploaddir = os.path.join(basedir, 'uploads/')
productdir = os.path.join(basedir, 'products/')

class Config(object):
    env = os.environ.get('FLASK_ENV')
    if env and env == 'development':
        DEBUG = True
        DEVELOPMENT = True
        MAIL_SUPPRESS_SEND = False if os.environ.get('MAIL_SUPPRESS_SEND') == 'False' else True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(datadir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ['MAIL_USERNAME']
    MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    BASE_DIR = basedir
    DATA_DIR = datadir
    TEMPLATE_DIR = templatedir
    UPLOAD_DIR = uploaddir
    PRODUCT_DIR = productdir
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'
    PRETTY_URL = os.environ.get('PRETTY_URL') or BASE_URL
    ADMINS=os.environ.get('ADMINS') or MAIL_USERNAME
    ADMINS=ADMINS.split(',')
    SUBSCRIPTION_GROUPS=os.environ.get('SUBSCRIPTION_GROUPS') or 'All'
    SUBSCRIPTION_GROUPS=[(sg,sg) for sg in SUBSCRIPTION_GROUPS.split(',')]
    DEFAULT_BANNER_PATH = os.environ.get('DEFAULT_BANNER_PATH') or None
    DEFAULT_FAVICON = os.environ.get('DEFAULT_FAVICON') or None
    LINK_FORMATS = os.environ.get('LINK_FORMATS')
    LINK_FORMATS = LINK_FORMATS.split(',') if LINK_FORMATS else ['Paperback','Hardcover','eBook','Other','']
    STRIPE_PUBLISHABLE = os.environ.get('STRIPE_PUBLISHABLE') or ''
    STRIPE_SECRET = os.environ.get('STRIPE_SECRET') or ''
    STRIPE_WEBHOOK = os.environ.get('STRIPE_WEBHOOK') or ''
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET') or 'bananas'
    DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK') or ''
    DISCORD_RELAY_GROUPS = os.environ.get('DISCORD_RELAY_GROUPS') or 'all,discord'
    DISCORD_RELAY_GROUPS = DISCORD_RELAY_GROUPS.split(',')
    TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE') or ''
    SITE_NAME = os.environ.get('SITE_NAME') or 'Flask Writer'
    DISQUS_SITE_NAME = os.environ.get('DISQUS_SITE_NAME') or SITE_NAME
    RECAPTCHA_PUBLIC = os.environ.get('RECAPTCHA_PUBLIC') or ''
    RECAPTCHA_SECRET = os.environ.get('RECAPTCHA_SECRET') or ''
    SUBSCRIBE_BANNER_SHOW = bool(os.environ.get('SUBSCRIBE_BANNER_SHOW')) or False
    SUBSCRIBE_CTA = os.environ.get('SUBSCRIBE_CTA') or 'Join the newsletter!'
    SUBSCRIBE_CTA_IMAGE = os.environ.get('SUBSCRIBE_CTA_IMAGE') 

