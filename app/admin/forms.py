from flask_wtf import FlaskForm
from wtforms import (
        StringField, TextAreaField, SelectField, IntegerField, SubmitField, 
        BooleanField, SubmitField, DateTimeField, SelectMultipleField, 
        PasswordField, HiddenField
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo, ValidationError
from app.models import Page, User, Tag

required = "<span class='text-danger'>*</span>"

class AddUserForm(FlaskForm):
    username = StringField(f'Username{required}', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), Optional()])
    about_me = TextAreaField('About Me')
    timezone = SelectField('Timezone')
    password = PasswordField(f'Password{required}', validators=[DataRequired()])
    confirm_password = PasswordField(f'Confirm Password{required}', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Add User")

class EditUserForm(FlaskForm):
    username = StringField(f'Username{required}', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), Optional()])
    about_me = TextAreaField('About Me')
    timezone = SelectField('Timezone')

    password = PasswordField('Password')
    new_password = PasswordField(f'New Password')
    confirm_password = PasswordField(f'Confirm Password{required}', validators=[EqualTo('password')])
    submit = SubmitField("Update User")

def all_tags():
    return Tag.query.order_by('name')
    
class AddPageForm(FlaskForm):
   title = StringField(f'Title{required}', validators=[DataRequired()]) 
   slug = StringField(f'Slug{required}', validators=[DataRequired()]) 
   template = SelectField(f'Template{required}', choices=Page.TEMPLATE_CHOICES)
   parent_id = SelectField('Parent', coerce=int)
   banner = StringField('Banner Image')
   summary = TextAreaField('Summary')#, validators=[Length('250')])
   sidebar = TextAreaField('Sidebar')#, validators=[Length('1000')])
   body = TextAreaField(f'Body{required}', validators=[DataRequired()])
   tags = QuerySelectMultipleField('Tags', query_factory=all_tags, allow_blank=True)
   user_id = SelectField(f'Author{required}', coerce=int, validators=[DataRequired()])
   pub_date = DateTimeField('Published Date', validators=[Optional()])
   published = BooleanField('Published?')
   timezone = HiddenField('Timezone')
   submit = SubmitField('Submit Post')

class AddTagForm(FlaskForm):
    name = StringField('Tag', validators=[DataRequired()])
    submit = SubmitField('Save Tag')

    def validate_tag(self, tag, id=0):
        t = Tag.query.filter_by(name=tag).first()
        if id == 0:
            if t:
                return False
            return True
        if t:
            if t.id == id:
                return True
            else:
                return False
        return True
