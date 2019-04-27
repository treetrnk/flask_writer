from app import create_app, db
from app.models import User, Page, Tag

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Page': Page, 'Tag': Tag}
