# -*- coding: utf-8 -*-

import re
import time
from datetime import datetime
from flask import request, flash, get_flashed_messages, url_for
from BeautifulSoup import BeautifulSoup, Comment
from markdown import markdown


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
        raise ValueError(u'日付形式ではありません。')
    return s


def check_time(s):
    if not s:
        return s
    try:
        time.strptime(s, '%H:%M')
    except ValueError:
        raise ValueError(u'時刻形式ではありません。')
    return s


def check_number(s):
    if not s:
        return s
    if not s.isdigit():
        raise ValueError(u'数値にしてください。')
    return s


def check_multiple_number(s):
    if not s:
        return s
    for s in s.split(','):
        if not s.strip().isdigit():
            raise ValueError(u'数値、複数の数値であれば' +
                             u'カンマ(半角)区切りで入力してください。')
    return s


def check_required(s):
    if not s:
        raise ValueError(u'入力必須です。')
    return s


def check_in(*options):
    def checker(s):
        if s not in options:
            raise ValueError(u'不正な値です。 (%s)' % ','.join(options))
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


def request_from_featurephone():
    ua = request.user_agent.string
    return re.match(r'(DoCoMo|UP\.Browser|J-PHONE|Vodafone|SoftBank)', ua)


def request_for_mobile_page():
    return re.match(r'^/mobile', request.path)


def pagination(page, pages):
    # pagination は最大 5 つまで
    if page < 3:
        begin = 1
    elif page + 2 > pages:
        begin = pages - 4
    else:
        begin = page - 2
    end = min(pages + 1, begin + 5)
    return (begin, end)


def age_of_fc():
    now = datetime.now()
    # 何年目かを表示するので +1
    return now.year - 2005 + 1


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


def sanitize_markdown(markdown_text):
    return markdown(markdown_text)


#############
# FILTERS
#############

def format_datetime_full(dt):
    return dt.strftime('%Y-%m-%d(%a) %H:%M').decode('utf8')


def format_datetime(dt):
    return dt.strftime('%m-%d(%a) %H:%M').decode('utf8')


def format_date(dt):
    return dt.strftime('%m-%d(%a)').decode('utf8')


def format_time(dt):
    return dt.strftime('%H:%M').decode('utf8')


def format_date_str(s):
    if not s:
        return s
    tm = time.strptime(s, '%Y-%m-%d')
    dt = datetime(tm.tm_year, tm.tm_mon, tm.tm_mday)
    return format_date(dt)


def format_season_action(season, action):
    season = u'%d月' % season
    action = u'→ ○' if action == 1 else u'→ ×'
    return season + ' ' + action


def mobile_url_for(view, **kwargs):
    user_id = kwargs.pop('uid', request.args.get('uid', None))
    session_id = kwargs.pop('sid', request.args.get('sid', None))
    path = url_for(view, **kwargs)
    if user_id is not None and session_id is not None:
        return path + ('?uid=%s&sid=%s' % (user_id, session_id))
    else:
        return path


def nl2br(body):
    return body.replace('\n', '<br>')


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
