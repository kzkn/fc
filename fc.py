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
        db.execute(
            """insert into Schedule (type, when_, body) values (
                 2, '2012-07-29 08:15:00', ?
               )""", (json.dumps({'name': u'ぴよぴよ杯',
                                  'loc': u'ふがふが',
                                  'genre': u'男ダブルス A',
                                  'deadline': '2012/07/28',
                                  'price': '2500',
                                  'begin_acceptance': '08:15',
                                  'begin_game': '09:00',
                                  'note': ''}), ))
        db.execute(
            """insert into Schedule (type, when_, body) values (
                 2, '2012-08-15 08:15:00', ?
               )""", (json.dumps({'name': u'ぶよぶよ杯',
                                  'loc': u'どっか',
                                  'genre': u'男ダブルス A',
                                  'deadline': '2012/07/28',
                                  'price': '2500',
                                  'begin_acceptance': '08:15',
                                  'begin_game': '09:00',
                                  'note': '90kg 以上限定'}), ))
        db.execute(
            """insert into Schedule (type, when_, body) values (
                 3, '2012-07-30 19:00:00', ?
               )""", (json.dumps({'name': u'はなきん',
                                  'loc': u'飲み屋',
                                  'description': u'飲むぜぇー',
                                  'deadline': '2012/07/28',
                                  'price': '2500'}), ))
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
        SELECT *
          FROM Schedule
         WHERE type = ? AND when_ >= datetime('now', 'localtime')
      ORDER BY when_""", (type, ))

    # Row -> dict for `entries'
    schedules = []
    for row in cur.fetchall():
        s = {}
        s.update(row)
        s.setdefault('entries', [])
        schedules.append(s)

    sids = '(%s)' % ','.join([str(s['id']) for s in schedules])
    cur.execute("""
        SELECT User.name AS user_name, Entry.user_id, Entry.schedule_id,
               Entry.comment, Entry.is_entry
          FROM Entry, User
         WHERE User.id = Entry.user_id
           AND Entry.schedule_id IN %s
      ORDER BY User.name""" % sids)

    entries = cur.fetchall()

    if entries:
        # make schedule-entry tree
        sid2sc = {}
        for s in schedules:
            sid2sc[s['id']] = s

        for e in entries:
            sid = e['schedule_id']
            schedule = sid2sc.get(sid, None)
            if schedule:
                schedule['entries'].append(e)

    return schedules


def find_my_entry(sid):
    cur = g.db.execute("""
        SELECT COUNT(*) FROM Entry
        WHERE user_id = ? AND schedule_id = ?""", (g.user['id'], sid))
    return cur.fetchone()[0] > 0


def update_entry(sid, comment, entry):
    g.db.execute("""
        UPDATE Entry
        SET is_entry = ?, comment = ?
        WHERE user_id = ? AND schedule_id = ?
        """, (entry, comment, g.user['id'], sid))
    g.db.commit()


def insert_entry(sid, comment, entry):
    g.db.execute("""
        INSERT INTO Entry (user_id, schedule_id, is_entry, comment)
        VALUES (?, ?, ?, ?)""", (g.user['id'], sid, entry, comment))
    g.db.commit()


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


def make_schedule(raw_schedule):
    schedule = {}
    schedule.update(raw_schedule)
    body = json.loads(raw_schedule['body'])
    schedule.update(body)
    return schedule


def do_entry(sid, comment, entry):
    if find_my_entry(sid):
        update_entry(sid, comment, entry)
    else:
        insert_entry(sid, comment, entry)


#############
# VIEWS
#############

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/schedule')
def schedule():
    ps = [make_schedule(s) for s in find_schedules(SCHEDULE_TYPE_PRACTICE)]
    gs = [make_schedule(s) for s in find_schedules(SCHEDULE_TYPE_GAME)]
    es = [make_schedule(s) for s in find_schedules(SCHEDULE_TYPE_EVENT)]
    return render_template('schedule.html',
                           practices=ps, games=gs, events=es)


@app.route('/entry/<int:sid>', methods=["POST"])
def entry(sid):
    action = request.form['action']
    comment = request.form['comment']
    if action == u'参加する':
        do_entry(sid, comment, entry=True)
    elif action == u'参加しない':
        do_entry(sid, comment, entry=False)
    return redirect(url_for('schedule'))


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
