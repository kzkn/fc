# -*- coding: utf-8 -*-

from flask import g, abort, request, session, flash, get_flashed_messages
from fcsite.models import users
from functools import wraps
from BeautifulSoup import BeautifulSoup, Comment
import re
import time


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
# VALIDATIONS
#############

def do_validate(form, validations):
    errors = {}

    for name in validations:
        input_value = form[name]
        try:
            [check(input_value) for check in validations[name]]
        except ValueError, e:
            errors[name] = e.message

    if errors:
        e = ValueError()
        e.errors = errors
        raise e


def check_date(s):
    if not s:
        return s
    try:
        time.strptime(s, '%Y-%m-%d')
    except ValueError:
        raise ValueError('日付形式ではありません')
    return s


def check_time(s):
    if not s:
        return s
    try:
        time.strptime(s, '%H:%M')
    except ValueError:
        raise ValueError('時刻形式ではありません')
    return s


def check_number(s):
    if not s:
        return s
    if not s.isdigit():
        raise ValueError('数値にしてください')
    return s


def check_required(s):
    if not s:
        raise ValueError('入力してください')
    return s


def check_in(*options):
    def checker(s):
        if s not in options:
            raise ValueError('不正な値です')
        return s
    return checker


#############
# UTILITIES
#############

def longzip(l1, l2):
    ret = []
    len1 = len(l1)
    len2 = len(l2)
    length = max(len1, len2)
    for i in xrange(length):
        pair = (l1[i] if i < len1 else None,
                l2[i] if i < len2 else None)
        ret.append(pair)
    return ret


def do_login(password):
    user = users.find_by_password(password)
    if user:
        session['user_id'] = user['id']
    return True if user else False


def request_from_featurephone():
    ua = request.user_agent.string
    return re.match(r'(DoCoMo|UP\.Browser|J-PHONE|Vodafone|SoftBank)', ua)


def request_for_mobile_page():
    return re.match(r'^/mobile', request.path)


def htmlize_textarea_body(body):
    return body.replace('\n', '<br>')


#############
# HTML SANITIZER
#############

# http://stackoverflow.com/posts/5246109/revisions

VALID_TAGS = {'strong': [],
              'em': [],
              'p': [],
              'ol': [],
              'ul': [],
              'li': [],
              'br': [],
              'a': ['href', 'title']}


def sanitize_html(value, valid_tags=VALID_TAGS):
    soup = BeautifulSoup(value)
    comments = soup.findAll(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]
    # Some markup can be crafted to slip through BeautifulSoup's parser, so
    # we run this repeatedly until it generates the same output twice.
    newoutput = soup.renderContents()
    while 1:
        oldoutput = newoutput
        soup = BeautifulSoup(newoutput)
        for tag in soup.findAll(True):
            if tag.name not in valid_tags:
                tag.hidden = True
            else:
                tag.attrs = [(attr, value) for attr, value in tag.attrs
                        if attr in valid_tags[tag.name]]
        newoutput = soup.renderContents()
        if oldoutput == newoutput:
            break
    newoutput = newoutput.replace('<br />', '<br>')
    return newoutput.decode('utf8')


#############
# FILTERS
#############

def format_datetime(dt):
    return dt.strftime('%m-%d(%a) %H:%M').decode('utf8')


def format_date(dt):
    return dt.strftime('%m-%d(%a)').decode('utf8')


def format_time(dt):
    return dt.strftime('%H:%M').decode('utf8')


#############
# MESSAGES
#############

def error_message(message, title=u'エラー!'):
    flash_message('error', title, message)


def info_message(message, title=u'通知'):
    flash_message('info', title, message)


def flash_message(category, title, message):
    msg = title + ':' + message
    msgs = get_flashed_messages(category_filter=[category])
    if msg not in msgs:
        flash(msg, category)
