#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, g, render_template, session, request, \
    redirect, url_for, flash

app = Flask(__name__)
app.config.from_object('config')

import datetime
import time
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import fcsite.database as database
import fcsite.models.users as users
import fcsite.models.schedules as scheds


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


def do_login(password):
    user = users.find_by_password(password)
    if user:
        session['user_id'] = user['id']
    return True if user else False


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
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('schedule.html',
                           practices=ps, games=gs, events=es)


@app.route('/entry/<int:sid>', methods=["POST"])
def entry(sid):
    action = request.form['action']
    comment = request.form['comment']
    if action == u'参加する':
        scheds.do_entry(sid, comment, entry=True)
    elif action == u'参加しない':
        scheds.do_entry(sid, comment, entry=False)
    return redirect(url_for('schedule'))


@app.route('/member')
@app.route('/member/<int:id>')
def member(id=None):
    males, females = users.find_group_by_sex()
    selected = users.find_by_id(id) if id else None

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
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    return render_template('admin_practice.html', practices=ps)


@app.route('/admin')
def admin():
    return show_admin()


@app.route('/admin/practice')
def admin_practice():
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    return render_template('admin_practice.html', practices=ps)


@app.route('/admin/game')
def admin_game():
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    return render_template('admin_game.html', games=gs)


@app.route('/admin/event')
def admin_event():
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('admin_event.html', events=es)


@app.route('/admin/member')
def admin_member():
    males, females = users.find_group_by_sex()
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

        u = users.make_obj(request.form)
        password = users.generate_uniq_password()
        users.insert(u['name'], str(password), u['sex'])
        return redirect(url_for('admin_member'))


@app.route('/admin/member/delete/<int:id>', methods=['GET', 'POST'])
def delete_member(id):
    if request.method == 'GET':
        user = users.find_by_id(id)
        return render_template('admin_delete_member.html', user=user)
    else:
        action = request.form['action']
        if action == u'はい':
            users.delete_by_id(id)
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

        p = scheds.make_practice_obj(request.form)
        scheds.insert(scheds.TYPE_PRACTICE, p['when'], p['body'])
        return redirect(url_for('admin_practice'))


@app.route('/admin/practice/edit/<int:id>', methods=['GET', 'POST'])
def edit_practice(id):
    if request.method == 'GET':
        p = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template('admin_edit_practice.html', practice=p)
    else:
        try:
            validate_practice()
        except ValueError:
            return redirect(url_for('edit_practice', id=id))

        p = scheds.make_practice_obj(request.form)
        scheds.update(id, p['when'], p['body'])
        return redirect(url_for('admin_practice'))


@app.route('/admin/practice/delete/<int:id>', methods=['GET', 'POST'])
def delete_practice(id):
    if request.method == 'GET':
        p = scheds.from_row(scheds.find_by_id(id))
        return render_template('admin_delete_practice.html', practice=p)
    else:
        action = request.form['action']
        if action == u'はい':
            scheds.delete_by_id(id)
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

        ga = scheds.make_game_obj(request.form)
        scheds.insert(scheds.TYPE_GAME, ga['when'], ga['body'])
        return redirect(url_for('admin_game'))


@app.route('/admin/game/edit/<int:id>', methods=['GET', 'POST'])
def edit_game(id):
    if request.method == 'GET':
        p = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template('admin_edit_game.html', game=p)
    else:
        try:
            validate_game()
        except ValueError:
            return redirect(url_for('edit_game', id=id))

        ga = scheds.make_game_obj(request.form)
        scheds.update(id, ga['when'], ga['body'])
        return redirect(url_for('admin_game'))


@app.route('/admin/game/delete/<int:id>', methods=['GET', 'POST'])
def delete_game(id):
    if request.method == 'GET':
        ga = scheds.from_row(scheds.find_by_id(id))
        return render_template('admin_delete_game.html', game=ga)
    else:
        action = request.form['action']
        if action == u'はい':
            scheds.delete_by_id(id)
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

        e = scheds.make_event_obj(request.form)
        scheds.insert(scheds.TYPE_EVENT, e['when'], e['body'])
        return redirect(url_for('admin_event'))


@app.route('/admin/event/edit/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    if request.method == 'GET':
        e = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template('admin_edit_event.html', event=e)
    else:
        try:
            validate_event()
        except ValueError:
            return redirect(url_for('edit_event', id=id))

        e = scheds.make_event_obj(request.form)
        scheds.update(id, e['when'], e['body'])
        return redirect(url_for('admin_event'))


@app.route('/admin/event/delete/<int:id>', methods=['GET', 'POST'])
def delete_event(id):
    if request.method == 'GET':
        ga = scheds.from_row(scheds.find_by_id(id))
        return render_template('admin_delete_event.html', event=ga)
    else:
        action = request.form['action']
        if action == u'はい':
            scheds.delete_by_id(id)
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
