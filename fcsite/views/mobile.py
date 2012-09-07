# -*- coding: utf-8 -*-

from flask import Blueprint, request, render_template, abort, redirect
from fcsite.models import users
from fcsite.models import schedules as scheds
from fcsite.models import bbs as bbsmodel
from fcsite.utils import mobile_url_for
from fcsite.auth import do_mobile_login
from functools import wraps

mod = Blueprint('mobile', __name__, url_prefix='/mobile')


def get_userid():
    return request.args.get('uid', None)


def get_sessionid():
    return request.args.get('sid', None)


def requires_userid(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = get_userid()
        if not uid or not users.find_by_id(uid):
            abort(401)
        sid = get_sessionid()
        if not sid or not users.is_valid_session_id(uid, sid):
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def find_user_and_schedule(sid):
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    s = scheds.find_by_id(sid)
    if not s:
        abort(404)
    return (user, scheds.from_row(s))


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        (uid, sid) = do_mobile_login(password)
        if uid:
            return redirect(mobile_url_for('mobile.index', uid=uid, sid=sid))
    return render_template('mobile/login.html')


@mod.route('/')
@requires_userid
def index():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    if scheds.has_non_registered_practice(user['id']):
        return redirect(mobile_url_for('mobile.non_registered_practices'))
    practice_count = scheds.count_schedules(scheds.TYPE_PRACTICE)
    game_count = scheds.count_schedules(scheds.TYPE_GAME)
    event_count = scheds.count_schedules(scheds.TYPE_EVENT)
    return render_template('mobile/index.html',
                           user=user,
                           practice_count=practice_count,
                           game_count=game_count,
                           event_count=event_count)


@mod.route('/non_registered_practices')
@requires_userid
def non_registered_practices():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    ps = [scheds.from_row(s) for s in scheds.find_non_registered(user['id'],
        scheds.TYPE_PRACTICE)]
    return render_template('mobile/practices.html', user=user, practices=ps,
            info_msg=u'未登録の練習があります。')


@mod.route('/practice')
@requires_userid
def practices():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    return render_template('mobile/practices.html', user=user, practices=ps)


@mod.route('/practice/<int:schid>')
@requires_userid
def practice(schid):
    (user, p) = find_user_and_schedule(schid)
    return render_template('mobile/practice.html', user=user, schedule=p)


@mod.route('/game')
@requires_userid
def games():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    return render_template('mobile/games.html', user=user, games=gs)


@mod.route('/game/<int:schid>')
@requires_userid
def game(schid):
    (user, ga) = find_user_and_schedule(schid)
    return render_template('mobile/game.html', user=user, schedule=ga)


@mod.route('/event')
@requires_userid
def events():
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('mobile/events.html', user=user, events=es)


@mod.route('/event/<int:schid>')
@requires_userid
def event(schid):
    (user, e) = find_user_and_schedule(schid)
    return render_template('mobile/event.html', user=user, schedule=e)


@mod.route('/entry/<int:schid>', methods=['POST'])
@requires_userid
def entry(schid):
    action = request.form['action']
    comment = request.form['comment']
    if action == u'参加':
        scheds.do_entry(schid, comment, entry=True)
    elif action == u'不参加':
        scheds.do_entry(schid, comment, entry=False)
    return redirect(request.form['come_from'])


@mod.route('/bbs')
@mod.route('/bbs/<int:page>')
@requires_userid
def bbs(page=1):
    user = users.find_by_id(get_userid())
    if not user:
        abort(401)
    modelpage = max(0, page - 1)
    posts = bbsmodel.find_posts_on_page(modelpage)
    pages = bbsmodel.count_pages()
    return render_template('mobile/bbs.html',
            user=user, page=page, pages=pages, posts=posts)


@mod.route('/bbs/post', methods=['POST'])
@requires_userid
def bbs_post():
    body = request.form['body']
    bbsmodel.post(body)
    return redirect(mobile_url_for('mobile.bbs'))


@mod.route('/member')
@mod.route('/member/<int:id>')
@requires_userid
def member(id=None):
    if not id:
        males, females = users.find_group_by_sex()
        return render_template('mobile/members.html', males=males,
                females=females)
    else:
        user = users.find_by_id(id)
        if not user:
            abort(404)
        return render_template('mobile/member.html', user=user)


@mod.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        return render_template('mobile/profile.html')
    id = get_userid()
    users.update_profile(id, request.form)
    return redirect(mobile_url_for('mobile.profile'))
