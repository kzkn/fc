#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, g, render_template, session, request, \
    redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'foo_bar-baz'

import sqlite3
from contextlib import closing


DATABASE_URI = 'fc.db'


def connect_db():
    db = sqlite3.connect(DATABASE_URI)
    db.row_factory = sqlite3.Row
    return db


def find_user_by_id(uid):
    cur = g.db.execute('SELECT * FROM User WHERE id = ?', (uid, ))
    return cur.fetchone()


@app.before_request
def before_request():
    g.db = connect_db()
    if is_logged_in():
        g.user = find_user_by_id(session.get('user_id'))


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def is_logged_in():
    return 'user_id' in session


def do_login(passwd):
    cur = g.db.execute('SELECT id, name FROM User WHERE password = ?',
                       (passwd, ))
    res = cur.fetchone()
    if res:
        session['user_id'] = res['id']
    return True if res else False


@app.route('/')
def index():
    if is_logged_in():
        return render_template('index.html', user=g.user['name'])
    else:
        return render_template('index.html')


@app.route('/schedule')
def schedule():
    return redirect(url_for('index'))


@app.route('/member')
def member():
    return redirect(url_for('index'))


@app.route('/bbs')
def bbs():
    return redirect(url_for('index'))


@app.route('/message')
def message():
    return redirect(url_for('index'))


@app.route('/admin')
def admin():
    return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    passwd = request.form['password']
    if not do_login(passwd):
        flash(u'E:ログインできません。パスワードが間違っています。')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('index'))


@app.route('/report')
def report():
    return redirect(url_for('index'))


@app.route('/gallery')
def gallery():
    return redirect(url_for('index'))


@app.route('/join')
def join():
    return redirect(url_for('index'))


def insert_test_data():
    with closing(connect_db()) as db:
        db.execute(
            "insert into User (name, password) values ('foo', '123456')")
        db.commit()


if __name__ == '__main__':
    init_db()
    insert_test_data()
    app.run('0.0.0.0', debug=True)
