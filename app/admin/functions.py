import re
import pytz
from datetime import datetime
from flask import current_app, flash, request
from flask_login import current_user

def convert_to_dict(obj):
    if type(obj) is not dict:
        data = {'repr': repr(obj)}
        for field in obj.__table__.columns:
            data[field.key] = obj.__dict__.get(field.key)
        #for field in obj.__table__.foreign_keys:
        #    data[field.key] = repr(obj.__dict__.get(field.key))
        try:
            data["users"] = obj.users
        except:
            pass
        try:
            data["user"] = obj.user
        except:
            pass
        try:
            data["tags"] = obj.tags
        except:
            pass
        try:
            data["page"] = obj.page
        except:
            pass
        try:
            data["parent"] = obj.parent
        except:
            pass
        return data
    return obj

def log_new(obj, message=''):
    identifier = current_user.username if current_user.is_authenticated else request.remote_addr
    data = convert_to_dict(obj)
    output = f'{identifier} {message}:\n'
    for key, value in data.items():
        char_cap = 1000
        value = value if type(value) is not str or len(value) < char_cap else f"{value[0:100]}...{value[-100:]}"
        output += f"    {key}: {value}\n"
    #print(output)
    current_app.logger.info(output)
    return True

def log_change(original, updated=None, message='changed something'):
    identifier = current_user.username if current_user.is_authenticated else request.remote_addr
    original_data = convert_to_dict(original)
    if updated:
        output = f'{identifier} {message}:\n'
        output += f"Changed object: {original['repr']}\n"
        updated_data = convert_to_dict(updated)
        for key, value in original_data.items():
            if key != 'repr':
                if key not in updated_data or value != updated_data[key]:
                    char_cap = 1000
                    value = value if type(value) is not str or len(value) < char_cap else f"{value[0:100]}...{value[-100:]}"
                    new_value = updated_data[key] 
                    new_value = new_value if type(new_value) is not str or len(new_value) < char_cap else f"{new_value[0:100]}...{new_value[-100:]}"
                    output += f'    {key}: {value}  ===CHANGED TO===>  {new_value}\n'
        #print(output)
        current_app.logger.info(output)
        return True
    return original_data
    
def log_form(form_obj):
    for field in form_obj:
        current_app.logger.debug(f'{field.name}: {field.data}')
        for error in field.errors:
            current_app.logger.warning(f'{field.name}: {error}')

def flash_form_errors(form_obj):
    if form_obj.errors:
        msg = """A problem occured with the following fields. 
                Please correct them and try again. 
                <ul>"""
        for error in form_obj.errors:
            msg += f"<li>{error}</li>"
    
        flash(msg, 'danger')

def to_utc_date(date, tz):
    date = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
    local_tz = pytz.timezone(tz)
    local_date = local_tz.localize(date)
    return local_date.astimezone(pytz.utc)

def to_local_tz_date(date, timezone='America/New_York'):
    current_app.logger.debug(date)
    date = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
    local_tz = pytz.timezone(timezone)
    utc_date = pytz.UTC.localize(date)
    return utc_date.astimezone(tz=local_tz)
