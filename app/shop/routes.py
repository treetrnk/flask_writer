import stripe
import json
from flask import (
        render_template, redirect, url_for, flash, session, request, 
        current_app, make_response, send_from_directory
    )
from app.shop import bp
from sqlalchemy import or_, desc
from app.models import Link, Product, Page
from app import db

@bp.route('/shop')
def index():
    Page.set_nav()
    products = Product.query.filter_by(active=True).order_by('sort','name').all()
    page = Page.query.filter_by(slug='shop').first()
    if products and page:
        return render_template(f'shop/index.html', 
                page=page,
                products=products,
            )
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page), 404

@bp.route('/shop/buy/<string:slug>')
def buy(slug):
    product = Product.query.filter_by(slug=slug).first()
    stripe.api_key = current_app.config['STRIPE_SECRET']
    success = (current_app.config['BASE_URL'] +
            url_for('shop.process') +
            '?session_id={CHECKOUT_SESSION_ID}')
    current_app.logger.debug(request.referrer)
    if request.referrer:
        cancel = request.referrer 
    else: 
        cancel = current_app.config['BASE_URL'] + url_for('shop.view', slug=product.slug)
    current_app.logger.debug(cancel)
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'name': product.name + " eBook",
            'description': product.description + " Paperback not included.",
            'images': [product.image],
            'amount': product.simple_price(),
            'currency': 'usd',
            'quantity': 1,
        }],
        metadata={
            'item_ids': product.id,
            'item_slugs': product.slug,
        },
        success_url=success,
        cancel_url=cancel,
    )

    return render_template('shop/buy.html', session=session)

@bp.route('/shop/process-purchase')
def process():
    flash('Thank you for your purchase! Your eBooks will be emailed to you shortly.', 'success')
    return redirect(url_for('shop.index'))

@bp.route('/shop/subscribe/<int:obj_id>')
def subscribe(obj_id):
    product = Product.query.filter_by(id=obj_id).first()
    if product:
        flash(f'Please subscribe to receive a free copy of <b><i>{product.name}</i></b>.', 'info')
    else:
        flash(f'Please subscribe to receive all subscription downloadables.', 'info')
    return redirect(url_for('page.subscribe'))

@bp.route('/shop/webhook', methods=['POST'])
def success():
    current_app.logger.debug('TRYING TO ACCESS SUCCESSFUL PURCHASE')
    stripe.api_key = current_app.config['STRIPE_SECRET']
    endpoint_secret = current_app.config['STRIPE_WEBHOOK']
    payload = request.get_data()
    sig_header = request.headers['Stripe-Signature']

    try:
        event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        current_app.logger.info('STRIPE: Invalid payload')
        page = Page.query.filter_by(slug='404-error').first()
        return render_template(f'page/{page.template}.html', page=page), 404
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.info('STRIPE: Invalid signature')
        page = Page.query.filter_by(slug='404-error').first()
        return render_template(f'page/{page.template}.html', page=page), 404

    current_app.logger.debug('STRIPE WEBHOOK')
    current_app.logger.debug(event['type'])

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
    
        json_payload = json.loads(payload)
        customer = stripe.Customer.retrieve(json_payload['data']['object']['customer'])
        item_ids = json_payload['data']['object']['metadata']['item_ids'].split(',')
        for item_id in item_ids:
            product = Product.query.filter_by(id=item_id).first()
            if not product:
                current_app.logger.info(f"STRIPE: Product not found. ({item_id})")
                page = Page.query.filter_by(slug='404-error').first()
                return render_template(f'page/{page.template}.html', page=page), 404
            product.send([customer['email']])
            current_app.logger.info(f'PURCHASE EMAIL SENT TO: {customer["email"]}  - {product.name} ({product.download_path})')

    return 'True'

@bp.route('/shop/<string:slug>')
def view(slug):
    Page.set_nav()
    product = Product.query.filter_by(slug=slug,active=True).first()
    page = Page.query.filter_by(slug='shop').first()
    if product:
        if product.active or current_user.is_authenticated:
            related = Product.query.filter(
                    Product.linked_page_id == product.linked_page_id,
                    Product.id != product.id,
                ).order_by('sort','name').limit(4).all()
            page.title = f"Shop: {product.name}"
            price = product.price
            sale_text = ''
            if product.on_sale:
                price = product.sale_price if product.sale_price else product.price
                sale_text = "On Sale! "
            description=f'{sale_text}{product.description} Starting at {price}'
            return render_template(f'shop/view.html', 
                    page=page,
                    product=product,
                    related=related,
                    banner=product.image,
                    description=description,
                )
    page = Page.query.filter_by(slug='404-error').first()
    return render_template(f'page/{page.template}.html', page=page), 404   

@bp.route('/shop/download/<int:obj_id>')
def download(obj_id):
    days_until_expired = 7
    Page.set_nav()
    product = Product.query.filter_by(id=obj_id,active=True).first()
    access_code = request.args.get('code')
    if product.verify_download(access_code, days=days_until_expired):
        return send_from_directory(current_app.config['PRODUCT_DIR'], product.download_path, as_attachment=True)
    flash(f'The access code for <b>{product.name}</b> is either invalid or expired. Download links expire after {days_until_expired} days. If there was a problem with your purchase, please contact <a href="mailto:{current_app.config.get("ADMINS")[0]}">{current_app.config.get("ADMINS")[0]}</a>.')
    return redirect(url_for('shop.index'))

