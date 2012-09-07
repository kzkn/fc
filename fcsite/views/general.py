# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, session, redirect, request, \
    url_for, g
from fcsite.models import schedules as scheds
from fcsite.utils import error_message
from fcsite.auth import do_login

mod = Blueprint('general', __name__)


@mod.route('/')
def index():
    info_msgs = []
    if g.user and scheds.has_non_registered_practice(g.user['id']):
        info_msgs.append(u'通知:未登録の練習があります。登録は' +
                u'<a href="%s">コチラから</a>。' % url_for('schedule.schedule'))
    return render_template('index.html', info_msgs=info_msgs)


@mod.route('/login', methods=['POST'])
def login():
    passwd = request.form['password']
    if not do_login(passwd):
        error_message(u'ログインできません。パスワードが間違っています。')
    return redirect(url_for('general.index'))


@mod.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('general.index'))


@mod.route('/report')
def report():
    return redirect(url_for('general.index'))


@mod.route('/gallery')
def gallery():
    return redirect(url_for('general.index'))


@mod.route('/join')
def join():
    return redirect(url_for('general.index'))
