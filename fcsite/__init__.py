#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from imp import load_source
from flask import Flask, Blueprint, g, session, redirect, url_for, request

app = Flask(__name__)
app.config.from_object('config')
secret = load_source('secret', app.config['SECRET_FILE'])
app.config.update(secret.secrets)
for h in app.logger.handlers:
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

from fcsite import database
from fcsite.models import users
from fcsite.models import joins
from fcsite.models import sayings
from fcsite.models import taxes
from fcsite.models import schedules as scheds
from fcsite.utils import request_from_featurephone, request_for_mobile_page, \
        error_message


#############
# REQUEST HOOKS
#############

@app.errorhandler(401)
def handle_unauthorized(e):
    if request_for_mobile_page():
        return redirect(url_for('mobile.login'))
    else:
        error_message(u'ログインしてください。')
        return redirect(url_for('general.index'))


@app.errorhandler(403)
def handle_forbidden(e):
    if request_for_mobile_page():
        return redirect(url_for('mobile.login'))
    else:
        error_message(u'権限がありません。')
        return redirect(url_for('general.index'))


@app.before_request
def before_request():
    g.db = database.connect_db()
    if 'user_id' in session:
        g.user = users.find_by_id(session.get('user_id'))
    elif 'uid' in request.args:
        g.user = users.find_by_id(request.args.get('uid'))
    else:
        g.user = None

    if request_from_featurephone() and not request_for_mobile_page():
        return redirect(
                url_for('mobile.index') +
                (('?uid=%d' % g.user.id) if g.user else ''))

    if request_for_mobile_page():
        request.charset = 'Shift_JIS'


@app.after_request
def after_request(response):
    if request_for_mobile_page():
        response.headers.add('Content-Type', 'text/html; charset=Shift_JIS')
        response.data = response.data.decode('utf8') \
                                     .encode('sjis', 'xmlcharrefreplace')
    return response


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def check_forced_registration_blueprint(name, import_name, **kwargs):
    ignore_patterns = kwargs.pop('ignore_patterns', [])
    bp = Blueprint(name, import_name, **kwargs)

    def match_any_ignore_pattern():
        for methods, path in ignore_patterns:
            if request.method in methods and path.match(request.path):
                return True
        return False

    def check_impl():
        if not g.user or match_any_ignore_pattern():
            return
        if g.user.has_not_registered_schedule_yet():
            return redirect(url_for('schedule.schedule'))

    bp.before_request(check_impl)
    return bp


#############
# VIEWS
#############

@app.route('/update', methods=['POST'])
def update():
    from subprocess import Popen, PIPE
    proc = Popen(app.config['UPDATE_SCRIPT'], shell=True,
            stdout=PIPE, stderr=PIPE, close_fds=True)
    print ''.join(proc.communicate())
    return 'ok'


@app.route('/message')
def message():
    return redirect(url_for('general.index'))


from fcsite.views import general
from fcsite.views import member
from fcsite.views import schedule
from fcsite.views import bbs
from fcsite.views import admin
from fcsite.views import mobile
app.register_blueprint(general.mod)
app.register_blueprint(member.mod)
app.register_blueprint(schedule.mod)
app.register_blueprint(bbs.mod)
app.register_blueprint(admin.mod)
app.register_blueprint(mobile.mod)

from fcsite import utils
app.jinja_env.filters['datetimeformat_full'] = utils.format_datetime_full
app.jinja_env.filters['datetimeformat'] = utils.format_datetime
app.jinja_env.filters['dateformat'] = utils.format_date
app.jinja_env.filters['timeformat'] = utils.format_time
app.jinja_env.filters['strdateformat'] = utils.format_date_str
app.jinja_env.filters['nl2br'] = utils.nl2br
app.jinja_env.filters['historyactionformat'] = \
    lambda h: utils.format_season_action(h['season'], h['action'])

app.jinja_env.globals['is_admin'] = \
    lambda: g.user and g.user.is_admin()
app.jinja_env.globals['is_schedule_admin'] = \
    lambda: g.user and g.user.is_schedule_admin()
app.jinja_env.globals['is_member_admin'] = \
    lambda: g.user and g.user.is_member_admin()
app.jinja_env.globals['is_notice_admin'] = \
    lambda: g.user and g.user.is_notice_admin()
app.jinja_env.globals['is_god'] = \
    lambda: g.user and g.user.is_god()
app.jinja_env.globals['admin_navigation_list'] = \
    lambda: admin.get_navigation_list(g.user)
app.jinja_env.globals['mobile_url_for'] = \
    utils.mobile_url_for
app.jinja_env.globals['count_joins_has_not_handled'] = \
    lambda: joins.count_has_not_handled()
app.jinja_env.globals['select_random_saying'] = \
    lambda: select_random_saying()
app.jinja_env.globals['is_paid_tax_for_current_season'] = \
    lambda user_id: taxes.is_paid_tax_for_current_season(user_id)
app.jinja_env.globals['is_entried'] = \
    lambda sched, user_id: scheds.is_entried(sched, user_id)
app.jinja_env.globals['age_of_fc'] = \
    utils.age_of_fc


def select_random_saying():
    if g.user:
        return sayings.select_random()
    else:
        return sayings.select_random_public()


try:
    import locale
    locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
except:
    pass
