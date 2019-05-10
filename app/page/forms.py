from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

required = "<span class='text-danger'>*</span>"

class SearchForm(FlaskForm):
    keyword = StringField(f'Username{required}', validators=[DataRequired()])
    submit = SubmitField("<i class='fas fa-search'></i> Search")

class SubscribeForm(FlaskForm):
    email = StringField(f'Email{required}', validators=[DataRequired(),Email()])
    first_name = StringField('Name')
    last_name = StringField('Last Name')
    subscription = StringField('Subscription')
    submit = SubmitField('Subscribe')
