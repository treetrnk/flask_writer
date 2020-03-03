from flask import Blueprint

bp = Blueprint('shop', __name__)

from app.shop import routes
