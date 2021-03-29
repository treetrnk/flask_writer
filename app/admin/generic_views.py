from flask import render_template, redirect, current_app, url_for, flash, request
from flask.views import View, MethodView
from flask_login import login_required
from app.admin.functions import log_new, log_change, log_form, flash_form_errors
from app.admin.forms import DeleteObjForm
from app import db
from app.models import Page

class ListView(MethodView):

    template = 'main/index.html'
    context = {}

    def extra(self):
        pass

    def get(self):
        self.extra()
        return self.render_template(self.template, **self.context)

class SaveObjView(MethodView):
    """
    Parameters to include:
    kwargs = {
        'title': the title to be used for the template
        'model': the model that is being added to, updated (without parentheses)
        'obj': the actual object being modified, [include this or the model]
        'form': the form being used to edit the obj
        'action': the action the user is performing [Add, Edit, Delete]
        'log_msg': message to send to the logs
        'success_msg': message to send to the user on successful submit
        'delete_form': form to delete obj [optional (only for Edit action)]
        'template': template to be sent to by default
        'redirect': url for redirect on success
        'context': a dictionary of items to pass to the template
    }
    """
    
    decorators = [login_required]
    title = None
    model = None
    obj_id = None
    obj = None
    form = None
    action = None
    log_msg = None
    success_msg = None
    delete_form = None
    template = 'main/index.html'
    redirect = None
    model_name = None
    delete_endpoint = None
    context = {}

    def __init__(self): #, **kwargs):
        #self.__dict__.update(kwargs)
        self.context.update(**self.__dict__)
        if self.action:
            self.context.update({'action': self.action})
        if self.action == 'Edit':
            self.context.update({'obj': self.obj})
        if self.title:
            self.context.update({'title': self.title})
        if self.model_name:
            self.context.update({'model_name': self.model_name})
        else: 
            self.context.update({'model_name': self.model.__name__})
        if self.redirect:
            self.context.update({'redirect': self.redirect})
        if self.delete_endpoint:
            self.context.update({'delete_endpoint': self.delete_endpoint})


    def set_object(self, obj_id):
        current_app.logger.debug(f'Form: {self.form()}')
        if obj_id and self.model:
            self.obj = self.model.query.filter_by(id=obj_id).first()
        if self.form:
            if self.obj:
                self.form = self.form(obj=self.obj)
            else:
                self.form = self.form()
            if hasattr(self.form, 'obj_id'):
                current_app.logger.info('THERE IS AN OBJ_ID')
                self.form.obj_id.data = obj_id
            self.context.update({'form': self.form})
        if self.model and not self.obj:
            self.obj = self.model()
        self.delete_form = self.delete_form() if self.delete_form else DeleteObjForm()
        if self.obj and self.obj.id:
            self.delete_form.obj_id.data = self.obj.id
        self.context.update({'delete_form': self.delete_form})

    def extra(self): ## For extra case-by-case functionality
        pass

    def pre_get(self): ## For extra case-by-case functionality
        pass

    def pre_post(self): ## For extra case-by-case functionality
        pass

    def post_post(self): ## For extra case-by-case functionality
        pass

    def post_submit(self): ## For extra case-by-case functionality
        pass

    def get(self, obj_id=None):
        self.context.update({'page':Page.query.filter_by(slug='admin').first()})
        self.set_object(obj_id)
        self.extra()
        self.pre_get()
        current_app.logger.debug(self.context)
        return render_template(self.template, **self.context)

    def post(self, obj_id=None):
        self.set_object(obj_id)
        self.extra()
        current_app.logger.info('POSTED========================================')
        if self.form.validate_on_submit():
            current_app.logger.info('VALIDATED========================================')
            if self.action == 'Edit':
                log_orig = log_change(self.obj)
                self.pre_post()
                self.form.populate_obj(self.obj)
                self.post_post()
                log_change(log_orig, self.obj, self.log_msg)
            else:
                self.pre_post()
                self.form.populate_obj(self.obj)
                self.post_post()
                db.session.add(self.obj)
                log_new(self.obj, self.log_msg)
            db.session.commit()
            self.post_submit()
            flash(self.success_msg, 'success')
            if self.redirect:
                return redirect(url_for(**self.redirect))
        log_form(self.form)
        flash_form_errors(self.form)
        return render_template(self.template, **self.context)

class DeleteObjView(MethodView):

    model = None
    redirect = None
    log_msg = ''
    success_msg = ''

    def extra(self):
        pass

    def post(self):
        self.extra()
        self.form = DeleteObjForm()
        if self.form.validate_on_submit():
            self.obj = self.model.query.filter_by(id=self.form.obj_id.data).first()
            log_new(self.obj, self.log_msg)
            db.session.delete(self.obj)
            db.session.commit()
            flash(self.success_msg, 'success')
        else:
            flash('Failed to delete {self.model.__name__}!', 'danger')
        log_form(self.form)
        #flash_form_errors(self.form)
        return redirect(url_for(**self.redirect))
