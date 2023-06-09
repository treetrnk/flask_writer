from app import create_app, db
from app.models import User, Page, Tag, Subscriber, Definition, Link, Product, Record, Comment
from datetime import datetime

app = create_app()

def install():
    objects = []
    objects += [User.query.filter_by(username='admin').first()]
    objects += [Page.query.filter_by(slug='home').first()]
    objects += [Page.query.filter_by(slug='admin').first()]
    objects += [Page.query.filter_by(slug='search').first()]
    objects += [Page.query.filter_by(slug='shop').first()]
    objects += [Page.query.filter_by(slug='subscriber-welcome').first()]
    objects += [Page.query.filter_by(slug='purchase-thank-you').first()]
    if any(objects):
        return print('Flask writer was previously installed. Command not run. Create a new database and run \'flask db upgrade\' to run this command.')
    user = User(username='admin')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()

    home_page = Page(title='Home',slug='home',template='page',published=True,user_id=user.id)
    home_page.set_path()
    db.session.add(home_page)
    
    admin_page = Page(title='Admin',slug='admin',template='page',published=False,user_id=user.id)
    admin_page.set_path()
    db.session.add(admin_page)
    
    search_page = Page(title='Search',slug='search',template='page',user_id=user.id,published=False)
    search_page.set_path()
    db.session.add(search_page)
    
    shop_page = Page(title='Shop',slug='shop',template='page',user_id=user.id,published=False)
    shop_page.set_path()
    db.session.add(shop_page)
    
    error_page = Page(title='404 Error',slug='404-error',template='page',user_id=user.id,published=False)
    error_page.set_path()
    db.session.add(error_page)
    
    sub_email = Page(title='Subscription Confirmation',slug='subscriber-welcome',template='page',user_id=user.id,published=False)
    sub_email.set_path()
    db.session.add(sub_email)
    
    product_email = Page(title='eBook Delivery',slug='purchase-thank-you',template='page',user_id=user.id,published=False)
    product_email.set_path()
    db.session.add(product_email)
    
    db.session.commit()
    return print('Insttalled!')

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'User': User, 
            'Page': Page, 
            'Tag': Tag, 
            'Subscriber': Subscriber,
            'Definition': Definition,
            'Link': Link,
            'Product': Product,
            'Record': Record,
            'Comment': Comment,
            'install': install,
        }

@app.before_first_request
def set_nav():
    Page.set_nav()
