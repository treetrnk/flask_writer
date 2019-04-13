from flask import Blueprint

bp = Blueprint('blog', __name__)

from app.blog import routes
