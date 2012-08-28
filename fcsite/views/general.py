# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, session, redirect, request, \
    flash, url_for
from fcsite.utils import do_login

mod = Blueprint('general', __name__)


@mod.route('/')
def index():
    return render_template('index.html')


@mod.route('/login', methods=['POST'])
def login():
    passwd = request.form['password']
    if not do_login(passwd):
        flash(u'E:ログインできません。パスワードが間違っています。')
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
