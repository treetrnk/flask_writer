from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Email, ValidationError
from app.models import Subscriber

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class SearchForm(FlaskForm):
    keyword = StringField(f'Username', validators=[DataRequired()])
    submit = SubmitField("<i class='fas fa-search'></i> Search")

class SubscribeForm(FlaskForm):
    email = StringField(f'Email', validators=[DataRequired(),Email()])
    first_name = StringField('Name')
    last_name = StringField('Last Name')
    subscription = MultiCheckboxField(f'Subscriptions', 
            validators=[DataRequired()], 
            description="Please select one or more.",
        )

    def validate_email(self, email):
        subscriber = Subscriber.query.filter_by(email=email.data).first()
        if subscriber is not None:
            raise ValidationError(f"{email.data} is already subscribed.")

class SubscriptionForm(FlaskForm):
    subscription = MultiCheckboxField(f'Subscriptions', 
            validators=[DataRequired()], 
            description="Please select one or more.",
        )
