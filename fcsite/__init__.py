#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, g, session, redirect, url_for

app = Flask(__name__)
app.config.from_object('config')

from fcsite import database
from fcsite.models import users


#############
# REQUEST HOOKS
#############

@app.before_request
def before_request():
    g.db = database.connect_db()
    if is_logged_in():
        g.user = users.find_by_id(session.get('user_id'))


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


#############
# DOMAIN LAYER LOGIC
#############

def is_logged_in():
    return 'user_id' in session


#############
# VIEWS
#############


@app.route('/bbs')
def bbs():
    return redirect(url_for('general.index'))


@app.route('/message')
def message():
    return redirect(url_for('general.index'))


from fcsite.views import general
from fcsite.views import member
from fcsite.views import schedule
from fcsite.views import admin
app.register_blueprint(general.mod)
app.register_blueprint(member.mod)
app.register_blueprint(schedule.mod)
app.register_blueprint(admin.mod)

from fcsite import utils
app.jinja_env.filters['datetimeformat'] = utils.format_datetime
app.jinja_env.filters['dateformat'] = utils.format_date
app.jinja_env.filters['timeformat'] = utils.format_time

import locale
locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
