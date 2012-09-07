# -*- coding: utf-8 -*-

from flask import g, abort, session
from functools import wraps
from fcsite.models import users


#############
# DECORATORS
#############

def requires_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not users.is_admin(g.user):
            abort(403)
        return f(*args, **kwargs)
    return requires_login(decorated_function)


def requires_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not users.has_permission(g.user, permission):
                abort(403)
            return f(*args, **kwargs)
        return requires_login(decorated_function)
    return decorator


#############
# UTILITIES
#############


def do_login(password):
    user = users.find_by_password(password)
    if user:
        session['user_id'] = user['id']
    return True if user else False


def do_mobile_login(password):
    user = users.find_by_password(password)
    if user:
        sid = users.issue_new_session_id(user['id'])
    return (user['id'], sid) if user else (None, None)
