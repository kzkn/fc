#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, g, render_template, session, request, \
    redirect, url_for, flash

app = Flask(__name__)
app.config.from_object('config')

import datetime
import itertools
import json
import os
import random
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


def connect_db():
    uri = app.config['DATABASE_URI']
    db = sqlite3.connect(uri, detect_types=sqlite3.PARSE_DECLTYPES)
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

USER_SEX_MALE = 1
USER_SEX_FEMALE = 2

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


def find_users_group_by_sex():
    users = g.db.execute('SELECT * FROM User ORDER BY sex, name').fetchall()
    bysex = {}
    for sex, us in itertools.groupby(users, lambda u: u['sex']):
        bysex[sex] = list(us)
    return bysex.get(USER_SEX_MALE, []), bysex.get(USER_SEX_FEMALE, [])


def insert_user(name, password, sex):
    g.db.execute('''
        INSERT INTO User (name, password, sex)
        VALUES (?, ?, ?)''', (name, password, sex))
    g.db.commit()


def delete_user_by_id(id):
    g.db.execute('DELETE FROM User WHERE id = ?', (id, ))
    g.db.commit()


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


def find_schedule_by_id(sid, with_entry=True):
    cur = g.db.execute("""
        SELECT *
          FROM Schedule
         WHERE id = ?""", (sid, ))

    schedule = dict(cur.fetchone())

    if with_entry:
        cur.execute("""
            SELECT User.name AS user_name, Entry.user_id,
                   Entry.comment, Entry.is_entry
              FROM Entry, User
             WHERE User.id = Entry.user_id
               AND Entry.schedule_id = ?
          ORDER BY User.name""", (sid, ))

        entries = cur.fetchall()
        schedule['entries'] = entries

    return schedule


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


def insert_schedule(type, when_, body):
    g.db.execute("""
        INSERT INTO Schedule (type, when_, body)
        VALUES (?, ?, ?)""", (type, when_, body))
    g.db.commit()


def update_schedule(sid, when_, body):
    g.db.execute("""
        UPDATE Schedule
           SET when_ = ?,
               body = ?
         WHERE id = ?""", (when_, body, sid))
    g.db.commit()


def delete_schedule_by_id(sid):
    g.db.execute("""
        DELETE FROM Schedule
         WHERE id = ?""", (sid, ))
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


def make_practice_obj(form):
    date = form['date']
    begintime = form['begintime']
    endtime = form['endtime']
    loc = form['loc']
    court = form['court']
    no = form['no']
    price = form['price']
    note = form['note']

    when = date + ' ' + begintime + ':00'
    body = make_practice_body(endtime, loc, court, no, price, note)
    return {'when': when,
            'body': body}


def make_practice_body(end, loc, court, no, price, note):
    p = {'end': end,
         'loc': loc,
         'court': court,
         'no': no,
         'price': price,
         'note': note}
    return json.dumps(p)


def make_game_obj(form):
    name = form['name']
    date = form['date']
    loc = form['loc']
    genre = form['genre']
    deadline = form['deadline']
    price = form['price']
    begin_acceptance = form['begin_acceptance']
    begin_game = form['begin_game']
    note = form['note']

    when = date + ' 00:00:00'
    body = make_game_body(
        name, loc, genre, deadline, price, begin_acceptance, begin_game, note)
    return {'when': when,
            'body': body}


def make_game_body(
        name, loc, genre, deadline, price, begin_acceptance, begin_game, note):
    ga = {'name': name,
          'loc': loc,
          'genre': genre,
          'deadline': deadline,
          'price': price,
          'begin_acceptance': begin_acceptance,
          'begin_game': begin_game,
          'note': note}
    return json.dumps(ga)


def make_event_obj(form):
    name = form['name']
    date = form['date']
    loc = form['loc']
    deadline = form['deadline']
    price = form['price']
    description = form['description']

    when = date + ' 00:00:00'
    body = make_event_body(name, loc, deadline, price, description)
    return {'when': when,
            'body': body}


def make_event_body(name, loc, deadline, price, description):
    e = {'name': name,
         'loc': loc,
         'deadline': deadline,
         'price': price,
         'description': description}
    return json.dumps(e)


def make_user_obj(form):
    return {'name': form['name'],
            'sex': sex_atoi(form['sex'])}


def sex_atoi(sex):
    return USER_SEX_MALE if sex == u'男性' else USER_SEX_FEMALE


def generate_uniq_password():
    p = random.randint(100000, 999999)
    while find_user_by_password(p):
        p = random.randint(100000, 999999)
    return p

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


def check_in(*options):
    def checker(s):
        if s not in options:
            raise ValueError('不正な値です')
        return s
    return checker


def validate_practice():
    validations = OrderedDict()
    validations['date'] = [check_required, check_date]
    validations['begintime'] = [check_required, check_time]
    validations['endtime'] = [check_required, check_time]
    validations['loc'] = [check_required]
    validations['no'] = [check_number]
    validations['price'] = [check_number]
    do_validate(request.form, validations)


def validate_game():
    validations = OrderedDict()
    validations['name'] = [check_required]
    validations['date'] = [check_required, check_date]
    validations['loc'] = [check_required]
    validations['genre'] = [check_required]
    validations['deadline'] = [check_date]
    validations['price'] = [check_number]
    validations['begin_acceptance'] = [check_time]
    validations['begin_game'] = [check_time]
    do_validate(request.form, validations)


def validate_event():
    validations = OrderedDict()
    validations['name'] = [check_required]
    validations['date'] = [check_required, check_date]
    validations['loc'] = [check_required]
    validations['deadline'] = [check_date]
    validations['price'] = [check_number]
    validations['description'] = [check_required]
    do_validate(request.form, validations)


def validate_member():
    validations = OrderedDict()
    validations['name'] = [check_required]
    validations['sex'] = [check_in(u'男性', u'女性')]
    do_validate(request.form, validations)


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
@app.route('/member/<int:id>')
def member(id=None):
    males, females = find_users_group_by_sex()
    selected = find_user_by_id(id) if id else None

    if not selected:
        if males:
            selected = males[0]
        elif females:
            selected = females[0]

    return render_template('member.html', males=males, females=females,
                           selected_user=selected)


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
    ps = [make_schedule(s) for s in find_schedules(SCHEDULE_TYPE_PRACTICE)]
    return render_template('admin_practice.html', practices=ps)


@app.route('/admin/game')
def admin_game():
    gs = [make_schedule(s) for s in find_schedules(SCHEDULE_TYPE_GAME)]
    return render_template('admin_game.html', games=gs)


@app.route('/admin/event')
def admin_event():
    es = [make_schedule(s) for s in find_schedules(SCHEDULE_TYPE_EVENT)]
    return render_template('admin_event.html', events=es)


@app.route('/admin/member')
def admin_member():
    males, females = find_users_group_by_sex()
    return render_template('admin_member.html', users=longzip(males, females))


@app.route('/admin/member/new', methods=['GET', 'POST'])
def new_member():
    if request.method == 'GET':
        return render_template('admin_edit_member.html')
    else:
        try:
            validate_member()
        except ValueError:
            return redirect(url_for('admin_member'))

        u = make_user_obj(request.form)
        password = generate_uniq_password()
        insert_user(u['name'], str(password), u['sex'])
        return redirect(url_for('admin_member'))


@app.route('/admin/member/delete/<int:id>', methods=['GET', 'POST'])
def delete_member(id):
    if request.method == 'GET':
        user = find_user_by_id(id)
        return render_template('admin_delete_member.html', user=user)
    else:
        action = request.form['action']
        if action == u'はい':
            delete_user_by_id(id)
        return redirect(url_for('admin_member'))


@app.route('/admin/practice/new', methods=['GET', 'POST'])
def new_practice():
    if request.method == 'GET':
        today = datetime.datetime.today()
        return render_template('admin_edit_practice.html', today=today)
    else:
        try:
            validate_practice()
        except ValueError:
            return redirect(url_for('new_practice'))

        p = make_practice_obj(request.form)
        insert_schedule(SCHEDULE_TYPE_PRACTICE, p['when'], p['body'])
        return redirect(url_for('admin_practice'))


@app.route('/admin/practice/edit/<int:id>', methods=['GET', 'POST'])
def edit_practice(id):
    if request.method == 'GET':
        p = make_schedule(find_schedule_by_id(id, with_entry=False))
        return render_template('admin_edit_practice.html', practice=p)
    else:
        try:
            validate_practice()
        except ValueError:
            return redirect(url_for('edit_practice', id=id))

        p = make_practice_obj(request.form)
        update_schedule(id, p['when'], p['body'])
        return redirect(url_for('admin_practice'))


@app.route('/admin/practice/delete/<int:id>', methods=['GET', 'POST'])
def delete_practice(id):
    if request.method == 'GET':
        p = make_schedule(find_schedule_by_id(id))
        return render_template('admin_delete_practice.html', practice=p)
    else:
        action = request.form['action']
        if action == u'はい':
            delete_schedule_by_id(id)
        return redirect(url_for('admin_practice'))


@app.route('/admin/game/new', methods=['GET', 'POST'])
def new_game():
    if request.method == 'GET':
        today = datetime.datetime.today()
        return render_template('admin_edit_game.html', today=today)
    else:
        try:
            validate_game()
        except ValueError:
            return redirect(url_for('new_game'))

        ga = make_game_obj(request.form)
        insert_schedule(SCHEDULE_TYPE_GAME, ga['when'], ga['body'])
        return redirect(url_for('admin_game'))


@app.route('/admin/game/edit/<int:id>', methods=['GET', 'POST'])
def edit_game(id):
    if request.method == 'GET':
        p = make_schedule(find_schedule_by_id(id, with_entry=False))
        return render_template('admin_edit_game.html', game=p)
    else:
        try:
            validate_game()
        except ValueError:
            return redirect(url_for('edit_game', id=id))

        ga = make_game_obj(request.form)
        update_schedule(id, ga['when'], ga['body'])
        return redirect(url_for('admin_game'))


@app.route('/admin/game/delete/<int:id>', methods=['GET', 'POST'])
def delete_game(id):
    if request.method == 'GET':
        ga = make_schedule(find_schedule_by_id(id))
        return render_template('admin_delete_game.html', game=ga)
    else:
        action = request.form['action']
        if action == u'はい':
            delete_schedule_by_id(id)
        return redirect(url_for('admin_game'))


@app.route('/admin/event/new', methods=['GET', 'POST'])
def new_event():
    if request.method == 'GET':
        today = datetime.datetime.today()
        return render_template('admin_edit_event.html', today=today)
    else:
        try:
            validate_event()
        except ValueError:
            return redirect(url_for('new_event'))

        e = make_event_obj(request.form)
        insert_schedule(SCHEDULE_TYPE_EVENT, e['when'], e['body'])
        return redirect(url_for('admin_event'))


@app.route('/admin/event/edit/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    if request.method == 'GET':
        e = make_schedule(find_schedule_by_id(id, with_entry=False))
        return render_template('admin_edit_event.html', event=e)
    else:
        try:
            validate_event()
        except ValueError:
            return redirect(url_for('edit_event', id=id))

        e = make_event_obj(request.form)
        update_schedule(id, e['when'], e['body'])
        return redirect(url_for('admin_event'))


@app.route('/admin/event/delete/<int:id>', methods=['GET', 'POST'])
def delete_event(id):
    if request.method == 'GET':
        ga = make_schedule(find_schedule_by_id(id))
        return render_template('admin_delete_event.html', event=ga)
    else:
        action = request.form['action']
        if action == u'はい':
            delete_schedule_by_id(id)
        return redirect(url_for('admin_event'))


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
