#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, g, render_template, session, request, \
    redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'foo_bar-baz'

import sqlite3
import json
from contextlib import closing


#############
# DATABASE ACCESS
#############

DATABASE_URI = 'fc.db'


def connect_db():
    db = sqlite3.connect(DATABASE_URI, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


#############
# DOMAIN LEVEL DATABASE ACCESS
#############

SCHEDULE_TYPE_PRACTICE = 1
SCHEDULE_TYPE_GAME = 2
SCHEDULE_TYPE_EVENT = 3


def insert_test_data():
    with closing(connect_db()) as db:
        db.execute(
            "insert into User (name, password) values ('foo', '123456')")
        db.execute(
            """insert into Schedule (type, when_, body) values (
                 1, '2012-07-29 01:00:00', ?
               )""", (json.dumps({'loc': u'ほげほげ',
                                  'court': '5',
                                  'end': '03:00',
                                  'no': '123456789',
                                  'price': '2400',
                                  'note': ''}), ))
        db.commit()


def find_user_by_id(uid):
    cur = g.db.execute('SELECT * FROM User WHERE id = ?', (uid, ))
    return cur.fetchone()


def find_user_by_password(password):
    cur = g.db.execute('SELECT id, name FROM User WHERE password = ?',
                       (password, ))
    return cur.fetchone()


def find_schedules(type):
    cur = g.db.execute("""
        SELECT * from Schedule
        WHERE type = ? AND when_ >= datetime('now', 'localtime')""", (type, ))
    return cur.fetchall()


#############
# REQUEST HOOKS
#############

@app.before_request
def before_request():
    g.db = connect_db()
    if is_logged_in():
        g.user = find_user_by_id(session.get('user_id'))


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


#############
# DOMAIN LAYER LOGIC
#############

def is_logged_in():
    return 'user_id' in session


def do_login(password):
    user = find_user_by_password(password)
    if user:
        session['user_id'] = user['id']
    return True if user else False


def make_practice(raw_practice):
    practice = {}
    practice.update(raw_practice)
    body = json.loads(raw_practice['body'])
    practice.update(body)
    return practice


def make_game(raw_game):
    game = {}
    game.update(raw_game)
    body = json.loads(raw_game['body'])
    game.update(body)
    return game


def make_event(raw_event):
    event = {}
    event.update(raw_event)
    body = json.loads(raw_event['body'])
    event.update(body)
    return event


#############
# VIEWS
#############

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/schedule')
def schedule():
    ps = [make_practice(s) for s in find_schedules(SCHEDULE_TYPE_PRACTICE)]
    gs = [make_game(s) for s in find_schedules(SCHEDULE_TYPE_GAME)]
    es = [make_event(s) for s in find_schedules(SCHEDULE_TYPE_EVENT)]
    return render_template('schedule.html',
                           practices=ps, games=gs, events=es)


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


#############
# DEVELOPMENT MAIN
#############

if __name__ == '__main__':
    init_db()
    insert_test_data()
    app.run('0.0.0.0', debug=True)
