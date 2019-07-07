from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
from app.models import Subscriber

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

    def validate_email(self, email):
        print("VALIDATING EMAIL ADDRESS")
        subscriber = Subscriber.query.filter_by(email=email.data).first()
        print(subscriber)
        if subscriber is not None:
            raise ValidationError(f"{email.data} is already subscribed.")
