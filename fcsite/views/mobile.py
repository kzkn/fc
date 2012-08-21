# -*- coding: utf-8 -*-

from flask import Blueprint, request, render_template, abort, redirect, url_for
from fcsite.models import users
from fcsite.models import schedules as scheds
from functools import wraps

mod = Blueprint('mobile', __name__, url_prefix='/mobile')


def get_userid():
    return request.args.get('uid', '')


def requires_userid(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = get_userid()
        if not uid:
            print 'abort 1'
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def append_userid(url):
    return '%s?uid=%s' % (url, get_userid())


def find_user_and_schedule(sid):
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    s = scheds.find_by_id(sid)
    if not s:
        abort(404)
    return (user, scheds.from_row(s))


@mod.route('/')
@requires_userid
def index():
    user = users.find_by_id(get_userid())
    if not user:
        print 'abort 2'
        abort(401)
    practice_count = scheds.count_schedules(scheds.TYPE_PRACTICE)
    game_count = scheds.count_schedules(scheds.TYPE_GAME)
    event_count = scheds.count_schedules(scheds.TYPE_EVENT)
    return render_template('mobile/index.html',
                           user=user,
                           practice_count=practice_count,
                           game_count=game_count,
                           event_count=event_count)


@mod.route('/practice')
@requires_userid
def practices():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    return render_template('mobile/practices.html', user=user, practices=ps)


@mod.route('/practice/<int:sid>')
@requires_userid
def practice(sid):
    (user, p) = find_user_and_schedule(sid)
    return render_template('mobile/practice.html', user=user, practice=p)


@mod.route('/game')
@requires_userid
def games():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    return render_template('mobile/games.html', user=user, games=gs)


@mod.route('/game/<int:sid>')
@requires_userid
def game(sid):
    (user, ga) = find_user_and_schedule(sid)
    return render_template('mobile/game.html', user=user, game=ga)


@mod.route('/event')
@requires_userid
def events():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('mobile/events.html', user=user, events=es)


@mod.route('/event/<int:sid>')
@requires_userid
def event(sid):
    (user, e) = find_user_and_schedule(sid)
    return render_template('mobile/event.html', user=user, event=e)


@mod.route('/entry/<int:sid>', methods=['POST'])
@requires_userid
def entry(sid):
    return redirect(append_userid(url_for('mobile.index')))
