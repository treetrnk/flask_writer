from flask_wtf import FlaskForm
from wtforms import (
        StringField, TextAreaField, SelectField, IntegerField, SubmitField, 
        BooleanField, SubmitField, DateTimeField, SelectMultipleField
)
from wtforms.validators import DataRequired, Length
from app.models import Page, User

required = "<span class='text-danger'>*</span>"

class NewPageForm(FlaskForm):
   title = StringField(f'Title{required}', validators=[DataRequired()]) 
   slug = StringField(f'Slug{required}', validators=[DataRequired()]) 
   template = SelectField(f'Template{required}', choices=Page.TEMPLATE_CHOICES)
   parent_id = SelectField('Parent', coerce=int)
   banner = StringField('Banner Image')
   summary = TextAreaField('Summary', validators=[Length('250')])
   sidebar = TextAreaField('Sidebar', validators=[Length('1000')])
   body = TextAreaField(f'Body{required}', validators=[DataRequired()])
   tags = SelectMultipleField('Tags', coerce=int)
   user_id = SelectField(f'Author{required}', coerce=int, validators=[DataRequired()])
   pub_date = DateTimeField('Published Date')
   published = BooleanField('Published?')
   submit = SubmitField('Submit Post')

