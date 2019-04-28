from flask_wtf import FlaskForm
from wtforms import (
        StringField, TextAreaField, SelectField, IntegerField, SubmitField, 
        BooleanField, SubmitField, DateTimeField, SelectMultipleField, 
        PasswordField
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo, ValidationError
from app.models import Page, User, Tag

required = "<span class='text-danger'>*</span>"

class AddUserForm(FlaskForm):
    username = StringField(f'Username{required}', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), Optional()])
    about_me = TextAreaField('About Me')
    password = PasswordField(f'Password{required}', validators=[DataRequired()])
    confirm_password = PasswordField(f'Confirm Password{required}', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Add User")

class EditUserForm(FlaskForm):
    username = StringField(f'Username{required}', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), Optional()])
    about_me = TextAreaField('About Me')

    current_password = PasswordField('Current Password')
    new_password = PasswordField(f'Password{required}', validators=[DataRequired()])
    confirm_password = PasswordField(f'Confirm Password{required}', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Update User")

def all_users():
    return User.query.order_by('username')
    
def all_pages():
    return Page.query.order_by('slug')
    
def all_tags():
    return Tag.query.order_by('name')
    
class AddPageForm(FlaskForm):
   title = StringField(f'Title{required}', validators=[DataRequired()]) 
   slug = StringField(f'Slug{required}', validators=[DataRequired()]) 
   template = SelectField(f'Template{required}', choices=Page.TEMPLATE_CHOICES)
   parent_id = QuerySelectField('Parent', query_factory=all_pages, allow_blank=True)
   banner = StringField('Banner Image')
   summary = TextAreaField('Summary')#, validators=[Length('250')])
   sidebar = TextAreaField('Sidebar')#, validators=[Length('1000')])
   body = TextAreaField(f'Body{required}', validators=[DataRequired()])
   tags = QuerySelectMultipleField('Tags', query_factory=all_tags, allow_blank=True)
   user_id = QuerySelectField(f'Author{required}', query_factory=all_users, validators=[DataRequired()])
   pub_date = DateTimeField('Published Date', validators=[Optional()])
   published = BooleanField('Published?')
   submit = SubmitField('Submit Post')

class AddTagForm(FlaskForm):
    name = StringField('Tag', validators=[DataRequired()])
    submit = SubmitField('Add Tag')

    def validate_tag(self, tag):
        t = Tag.query.filter_by(name=tag).first()
        if t:
            return False
        return True

