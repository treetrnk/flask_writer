from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

required = "<span class='text-danger'>*</span>"

class SearchForm(FlaskForm):
    keyword = StringField(f'Username{required}', validators=[DataRequired()])
    submit = SubmitField("<i class='fas fa-search'></i> Search")

