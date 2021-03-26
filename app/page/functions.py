import re
from app.models import Product

def replace_product_markup(text):
    result = text
    matches = re.findall('p\[(\d*)\]', text)
    for match in matches:
        pid = match[0]
        product = Product.query.filter_by(id = pid).first()
        product.unghosted()
        if product:
            result = result.replace(f'p[{pid}]', product.card())
        else:
            result = result.replace(f'p[{pid}]', '')
    return result
