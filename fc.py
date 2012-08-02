#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, g, render_template, session, request, \
    redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'foo_bar-baz'

import datetime
import itertools
import json
import os
import sqlite3
import time
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from contextlib import closing


#############
# DATABASE ACCESS
#############

DATABASE_URI = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'fc.db')


def connect_db():
    db = sqlite3.connect(DATABASE_URI, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def insert_test_data():
    with closing(connect_db()) as db:
        with app.open_resource('testdata.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


#############
# DOMAIN LEVEL DATABASE ACCESS
#############

SCHEDULE_TYPE_PRACTICE = 1
SCHEDULE_TYPE_GAME = 2
SCHEDULE_TYPE_EVENT = 3


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
    schedules = [dict(r) for r in cur.fetchall()]

    sids = '(%s)' % ','.join([str(s['id']) for s in schedules])
    cur.execute("""
        SELECT User.name AS user_name, Entry.user_id, Entry.schedule_id,
               Entry.comment, Entry.is_entry
          FROM Entry, User
         WHERE User.id = Entry.user_id
           AND Entry.schedule_id IN %s
      ORDER BY Entry.schedule_id, User.name""" % sids)

    entries = cur.fetchall()

    if entries:
        # make schedule-entry tree
        sid2sc = {}
        for s in schedules:
            sid2sc[s['id']] = s

        for sid, es in itertools.groupby(entries, lambda e: e['schedule_id']):
            schedule = sid2sc.get(sid, None)
            if schedule:
                schedule['entries'] = list(es)

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


def insert_practice(when_, body):
    g.db.execute("""
        INSERT INTO Schedule (type, when_, body)
        VALUES (?, ?, ?)""", (SCHEDULE_TYPE_PRACTICE, when_, body))
    g.db.commit()


def find_practice_locations():
    cur = g.db.execute(
        "SELECT body FROM Schedule WHERE type = ?", (SCHEDULE_TYPE_PRACTICE, ))
    bodies = cur.fetchall()
    return list(set([json.loads(body[0])['loc'] for body in bodies]))


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


def make_practice_body(end, loc, court, no, price, note):
    p = {'end': end,
         'loc': loc,
         'court': court,
         'no': no,
         'price': price,
         'note': note}
    return json.dumps(p)


def make_new_practice(form):
    date = form['date']
    begintime = form['begintime']
    endtime = form['endtime']
    loc = form['loc']
    court = form['court'] or '-'
    no = form['no'] or '-'
    price = form['price'] or '-'
    note = form['note']
    when = date + ' ' + begintime + ':00'
    body = make_practice_body(endtime, loc, court, no, price, note)
    insert_practice(when, body)


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
    try:
        time.strptime(s, '%Y-%m-%d')
    except ValueError:
        raise ValueError('日付形式ではありません')
    return s


def check_time(s):
    try:
        time.strptime(s, '%H:%M')
    except ValueError:
        raise ValueError('時刻形式ではありません')
    return s


def check_number(s):
    if len(s) == 0:
        return s
    if not s.isdigit():
        raise ValueError('数値にしてください')
    return s


def check_required(s):
    if not s:
        raise ValueError('入力してください')
    return s


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


def show_admin(errors=[]):
    ps = [make_schedule(s) for s in find_schedules(SCHEDULE_TYPE_PRACTICE)]
    return render_template('admin_practice.html', practices=ps)


@app.route('/admin')
def admin():
    return show_admin()


@app.route('/admin/practice')
def admin_practice():
    return show_admin()


@app.route('/admin/game')
def admin_game():
    return show_admin()


@app.route('/admin/event')
def admin_event():
    return show_admin()


@app.route('/admin/member')
def admin_member():
    return show_admin()


@app.route('/admin/practice/new', methods=['GET', 'POST'])
def new_practice():
    if request.method == 'GET':
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        return render_template('admin_edit_practice.html', today=today)
    else:
        try:
            validations = OrderedDict()
            validations['date'] = [check_required, check_date]
            validations['begintime'] = [check_required, check_time]
            validations['endtime'] = [check_required, check_time]
            validations['loc'] = [check_required]
            validations['no'] = [check_number]
            validations['price'] = [check_number]
            do_validate(request.form, validations)
        except ValueError:
            return redirect(url_for('new_practice'))

        make_new_practice(request.form)
        return redirect(url_for('admin_practice'))


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
