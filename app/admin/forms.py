from flask_wtf import FlaskForm
from wtforms import (
        StringField, TextAreaField, SelectField, IntegerField, SubmitField, 
        BooleanField, SubmitField, DateTimeField, SelectMultipleField, 
        PasswordField, HiddenField, DateField, TimeField
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo, ValidationError, InputRequired
from app.models import Page, User, Tag, Definition, Link, Product

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
   notes = TextAreaField('Notes')
   tags = QuerySelectMultipleField('Tags', query_factory=all_tags, allow_blank=True)
   user_id = SelectField(f'Author{required}', coerce=int, validators=[DataRequired()])
   pub_date = DateField('Published Date', validators=[Optional()])
   pub_time = TimeField('Published Date', validators=[Optional()])
   published = BooleanField('Published?')
   notify_subs = BooleanField('Notify Subscribers?')
   notify_group = SelectField('Notify Group')
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

class EditDefinitionForm(FlaskForm):
    name = StringField(f'Name{required}', validators=[DataRequired()])
    type = SelectField(f'Type{required}', validators=[DataRequired()])
    body = TextAreaField(f'Body{required}', validators=[DataRequired()])
    hidden_body = TextAreaField("Author's Notes")
    parent_id = SelectField('Parent', coerce=int)
    tag_id = SelectField(f'Linked Tag', coerce=int)
    #tags = QuerySelectMultipleField('Tags', query_factory=all_tags, allow_blank=True)

    #def validate_name(self, name):
    #    definition = Definition.query.filter_by(name=name, parent_id=self.parent_id, tags=self.tags).first()
    #    if definition is not None:
    #        raise ValidationError('Definition already exists.', 'Error')
    #    return True

class ProductEditForm(FlaskForm):
    name = StringField(f'Name{required}', validators=[DataRequired()])
    price = StringField(f'Price{required}', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    image = StringField('Image URL', validators=[Length(max=500)])
    sort = IntegerField('Sort #', render_kw={'placeholder':"500"})
    active = BooleanField('Active')

class LinkEditForm(FlaskForm):
    text = StringField(f'Link Text{required}', validators=[Length(max=1000)])
    product_id = SelectField(f'Product{required}', coerce=int, validators=[DataRequired()])
    url = StringField('URL', validators=[Length(max=500)])
    sort = IntegerField('Sort #', render_kw={'placeholder':"500"})

class EmailForm(FlaskForm):
    subject = StringField('Subject')
    recipients = SelectMultipleField('Recipients', coerce=int)
    banner = StringField('Banner URL')
    body = TextAreaField('Body')

class RecordForm(FlaskForm):
    start_words = IntegerField(f'Start{required}', validators=[InputRequired()])
    end_words = IntegerField(f'End{required}', validators=[DataRequired()])
    overall_words = IntegerField('Overall Total', validators=[Optional()])
    comment = StringField('Comment', validators=[Length(max=200)])
    
class RecordEditForm(FlaskForm):
    start_words = IntegerField(f'Start{required}', validators=[InputRequired()])
    end_words = IntegerField(f'End{required}', validators=[DataRequired()])
    overall_words = IntegerField('Overall Total', validators=[Optional()])
    comment = StringField('Comment', validators=[Length(max=200)])
    date = DateField('Date', render_kw={'type': 'date'})
    
class DeleteObjForm(FlaskForm):
    obj_id = HiddenField('Object id', validators=[DataRequired()])
