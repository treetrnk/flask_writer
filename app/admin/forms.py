from flask_wtf import FlaskForm
from wtforms import (
        StringField, TextAreaField, SelectField, IntegerField, SubmitField, 
        BooleanField, SubmitField, DateTimeField, SelectMultipleField, 
        PasswordField, HiddenField, DateField, TimeField, FileField,
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo, ValidationError, InputRequired
from app.models import Page, User, Tag, Definition, Link, Product

required = "<span class='text-danger'>*</span>"

class AddUserForm(FlaskForm):
    name = StringField(f'Name', validators=[Length(max=100)])
    username = StringField(f'Username', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[Email(), Optional(), Length(max=120)])
    avatar = StringField('Avatar URL', validators=[Length(max=500), Optional(), Length(max=500)])
    about_me = TextAreaField('About Me', validators=[Length(max=140)])
    timezone = SelectField('Timezone', validators=[Length(max=150)])
    password = PasswordField(f'Password', validators=[DataRequired(), Length(min=6,max=20)])
    confirm_password = PasswordField(f'Confirm Password', validators=[DataRequired(), EqualTo('password')])

class EditUserForm(FlaskForm):
    name = StringField(f'Name', validators=[Length(max=100)])
    username = StringField(f'Username', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[Email(), Optional(), Length(max=120)])
    avatar = StringField('Avatar URL', validators=[Length(max=500), Optional(), Length(max=500)])
    about_me = TextAreaField('About Me', validators=[Length(max=140)])
    timezone = SelectField('Timezone', validators=[Length(max=150)])

    password = PasswordField('Password')
    new_password = PasswordField(f'New Password', validators=[Optional(), Length(min=6, max=20)])
    confirm_password = PasswordField(f'Confirm Password', validators=[EqualTo('new_password')])

def all_tags():
    return Tag.query.order_by('name')
    
class AddPageForm(FlaskForm):
   title = StringField(f'Title', validators=[DataRequired(), Length(max=200)]) 
   slug = StringField(f'Slug', validators=[DataRequired(), Length(max=200)]) 
   template = SelectField(f'Template', choices=Page.TEMPLATE_CHOICES)
   parent_id = SelectField('Parent', coerce=int)
   cover = StringField('Cover Image', validators=[Length(max=500)])
   banner = StringField('Banner Image', validators=[Length(max=500)])
   summary = TextAreaField('Summary', validators=[Length(max=300),Optional()])
   author_note = TextAreaField("Author's Note", validators=[Length(max=5000),Optional()], render_kw={'rows':4})
   author_note_location = SelectField('Note Location', coerce=str, choices=Page.AUTHOR_NOTE_LOCATIONS)
   sidebar = TextAreaField('Sidebar', validators=[Length(max=5000), Optional()])
   body = TextAreaField(f'Body', validators=[DataRequired(), Length(max=10000000)])
   notes = TextAreaField('Notes', validators=[Length(max=5000000)])
   tags = QuerySelectMultipleField('Tags', query_factory=all_tags, allow_blank=True)
   user_id = SelectField(f'Author', coerce=int, validators=[DataRequired()])
   pub_date = DateField('Published Date', validators=[Optional()])
   pub_time = TimeField('Published Date', validators=[Optional()])
   published = BooleanField('Published?')
   notify_subs = BooleanField('Notify Subscribers?')
   notify_group = SelectField('Notify Group')
   timezone = HiddenField('Timezone')
   submit = SubmitField('Submit Post')

class AddTagForm(FlaskForm):
    name = StringField('Tag', validators=[DataRequired(), Length(max=75)])
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
    name = StringField(f'Name', validators=[DataRequired(), Length(max=150)])
    type = SelectField(f'Type', validators=[DataRequired()])
    body = TextAreaField(f'Body', validators=[DataRequired(), Length(max=5000)])
    hidden_body = TextAreaField("Author's Notes", validators=[Length(max=5000)])
    parent_id = SelectField('Parent', coerce=int, render_kw={'data_type': 'select2'})
    tag_id = SelectField(f'Linked Tag', coerce=int, render_kw={'data_type': 'select2'})
    active = BooleanField(f'Active', description="Uncheck to hide from readers")
    #tags = QuerySelectMultipleField('Tags', query_factory=all_tags, allow_blank=True)

    #def validate_name(self, name):
    #    definition = Definition.query.filter_by(name=name, parent_id=self.parent_id, tags=self.tags).first()
    #    if definition is not None:
    #        raise ValidationError('Definition already exists.', 'Error')
    #    return True

class SendProductForm(FlaskForm):
    email = StringField(f'Email', validators=[DataRequired(),Email(), Length(max=200)])

class ProductEditForm(FlaskForm):
    name = StringField(f'Name', validators=[DataRequired(), Length(max=150)], render_kw={'id':'page_title_input'})
    slug = StringField(f'Slug', validators=[DataRequired(), Length(max=150)], render_kw={'id':'page_slug_input'})
    ghost_link = StringField(f'Ghost Link', validators=[Length(max=500)])
    price = StringField(f'Price', validators=[DataRequired(), Length(max=10)])
    sale_price = StringField(f'Sale Price', validators=[Length(max=10)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    image = StringField('Image URL', validators=[Length(max=500)])
    download_path = StringField('Download Path', validators=[Length(max=500)])
    linked_page_id = SelectField('Linked Story', coerce=int, render_kw={'data_type': 'select2'})
    category_id = SelectField(f'Category', coerce=int, validators=[DataRequired()])
    sort = IntegerField('Sort #', render_kw={'placeholder':"500"})
    on_sale = BooleanField('On Sale')
    active = BooleanField('Active')

class CategoryEditForm(FlaskForm):
    name = StringField(f'Name', validators=[DataRequired(),Length(max=150)], render_kw={'id':'page_title_input'})
    icon = StringField('Category', validators=[Length(max=150)])
    default = BooleanField('Default')

class LinkEditForm(FlaskForm):
    text = StringField(f'Link Text', validators=[Length(max=1000)])
    icon = StringField('Icon', validators=[Length(max=200)])
    format = SelectField('Format', validators=[Length(max=200)])
    product_id = SelectField(f'Product', coerce=int, validators=[DataRequired()])
    url = StringField('URL', validators=[Length(max=500)])
    sort = IntegerField('Sort #', render_kw={'placeholder':"500"})

class EmailForm(FlaskForm):
    subject = StringField('Subject', validators=[Length(max=100)])
    recipients = SelectMultipleField('Recipients', coerce=int)
    banner = StringField('Banner URL')
    body = TextAreaField('Body')

class RecordForm(FlaskForm):
    start_words = IntegerField(f'Start', render_kw={'type': 'number'}, validators=[InputRequired()])
    end_words = IntegerField(f'End', render_kw={'type': 'number'}, validators=[DataRequired()])
    overall_words = IntegerField('Story Total', render_kw={'type': 'number'}, validators=[Optional()])
    minutes = IntegerField('Minutes', render_kw={'type': 'number'}, validators=[Optional()])
    comment = StringField('Comment', validators=[Length(max=200)])
    
class RecordEditForm(FlaskForm):
    start_words = IntegerField(f'Start', render_kw={'type': 'number'}, validators=[InputRequired()])
    end_words = IntegerField(f'End', render_kw={'type': 'number'}, validators=[DataRequired()])
    overall_words = IntegerField('Story Total', render_kw={'type': 'number'}, validators=[Optional()])
    minutes = IntegerField('Minutes', render_kw={'type': 'number'}, validators=[Optional()])
    comment = StringField('Comment', validators=[Length(max=200)])
    date = DateField('Date', render_kw={'type': 'date'})
    
class FileUploadForm(FlaskForm):
    file_data = FileField(f'File')
    folder = SelectField(f'Folder')

class CommentEditForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired(), Length(max=100)]) 
    email = StringField('Email', validators=[Optional(), Email(), Length(max=150)]) 
    body = TextAreaField('Comment', validators=[DataRequired(), Length(max=3000)]) 
    created_date = DateField('Created', validators=[DataRequired()], render_kw={'type': 'date'})
    created_time = TimeField('', validators=[DataRequired()], render_kw={'type': 'time'})
    user_id = SelectField('User', coerce=int)
    timezone = HiddenField('Timezone')
    #page_id = HiddenField('page id')
    #product_id = HiddenField('product id')

class DeleteObjForm(FlaskForm):
    obj_id = HiddenField('Object id', validators=[DataRequired()])
