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
    avatar = StringField('Avatar URL', validators=[Length(max=500), Optional()])
    about_me = TextAreaField('About Me')
    timezone = SelectField('Timezone')
    password = PasswordField(f'Password{required}', validators=[DataRequired()])
    confirm_password = PasswordField(f'Confirm Password{required}', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Add User")

class EditUserForm(FlaskForm):
    username = StringField(f'Username{required}', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), Optional()])
    avatar = StringField('Avatar URL', validators=[Length(max=500), Optional()])
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
   summary = TextAreaField('Summary', validators=[Length(max=300),Optional()])
   author_note = TextAreaField("Author's Note", validators=[Length(max=5000),Optional()], render_kw={'rows':4})
   author_note_location = SelectField('Note Location', coerce=str, choices=Page.AUTHOR_NOTE_LOCATIONS)
   sidebar = TextAreaField('Sidebar', validators=[Length(max=5000), Optional()])
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

class DefinitionEditForm(FlaskForm):
    name = StringField(f'Name{required}', validators=[DataRequired()])
    type = SelectField(f'Type{required}', validators=[DataRequired()])
    body = TextAreaField(f'Body{required}', validators=[DataRequired()])
    hidden_body = TextAreaField("Author's Notes")
    parent_id = SelectField('Parent', coerce=int, render_kw={'data_type': 'select2'})
    tag_id = SelectField(f'Linked Tag', coerce=int, render_kw={'data_type': 'select2'})
    active = BooleanField(f'Active', description="Uncheck to hide from readers")
    #tags = QuerySelectMultipleField('Tags', query_factory=all_tags, allow_blank=True)

    #def validate_name(self, name):
    #    definition = Definition.query.filter_by(name=name, parent_id=self.parent_id, tags=self.tags).first()
    #    if definition is not None:
    #        raise ValidationError('Definition already exists.', 'Error')
    #    return True

class ProductEditForm(FlaskForm):
    name = StringField(f'Name{required}', validators=[DataRequired()], render_kw={'id':'page_title_input'})
    slug = StringField(f'Slug{required}', validators=[DataRequired()], render_kw={'id':'page_slug_input'})
    price = StringField(f'Price{required}', validators=[DataRequired()])
    sale_price = StringField(f'Sale Price')
    description = TextAreaField('Description', validators=[Length(max=1000)])
    image = StringField('Image URL', validators=[Length(max=500)])
    download_path = StringField('Download Path', validators=[Length(max=500)])
    linked_page_id = SelectField('Linked Story', coerce=int, render_kw={'data_type': 'select2'})
    sort = IntegerField('Sort #', render_kw={'placeholder':"500"})
    on_sale = BooleanField('On Sale')
    active = BooleanField('Active')

class LinkEditForm(FlaskForm):
    text = StringField(f'Link Text{required}', validators=[Length(max=1000)])
    icon = StringField('Icon', validators=[Length(max=200)])
    format = SelectField('Format', validators=[Length(max=200)])
    product_id = SelectField(f'Product{required}', coerce=int, validators=[DataRequired()])
    url = StringField('URL', validators=[Length(max=500)])
    sort = IntegerField('Sort #', render_kw={'placeholder':"500"})

class EmailForm(FlaskForm):
    subject = StringField('Subject')
    recipients = SelectMultipleField('Recipients', coerce=int)
    banner = StringField('Banner URL')
    body = TextAreaField('Body')

class RecordForm(FlaskForm):
    start_words = IntegerField(f'Start{required}', render_kw={'type': 'number'}, validators=[InputRequired()])
    end_words = IntegerField(f'End{required}', render_kw={'type': 'number'}, validators=[DataRequired()])
    overall_words = IntegerField('Story Total', render_kw={'type': 'number'}, validators=[Optional()])
    minutes = IntegerField('Minutes', render_kw={'type': 'number'}, validators=[Optional()])
    comment = StringField('Comment', validators=[Length(max=200)])
    
class RecordEditForm(FlaskForm):
    start_words = IntegerField(f'Start{required}', render_kw={'type': 'number'}, validators=[InputRequired()])
    end_words = IntegerField(f'End{required}', render_kw={'type': 'number'}, validators=[DataRequired()])
    overall_words = IntegerField('Story Total', render_kw={'type': 'number'}, validators=[Optional()])
    minutes = IntegerField('Minutes', render_kw={'type': 'number'}, validators=[Optional()])
    comment = StringField('Comment', validators=[Length(max=200)])
    date = DateField('Date', render_kw={'type': 'date'})
    
class DeleteObjForm(FlaskForm):
    obj_id = HiddenField('Object id', validators=[DataRequired()])
