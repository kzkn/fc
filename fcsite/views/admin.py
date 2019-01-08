# -*- coding: utf-8 -*-

from datetime import datetime
from itertools import groupby
from collections import OrderedDict

from flask import Blueprint, request, render_template, redirect, url_for, g, \
    abort, jsonify
from fcsite.models import users
from fcsite.models import schedules as scheds
from fcsite.models import court as crt
from fcsite.models import notices
from fcsite.models import sayings
from fcsite.utils import do_validate, check_date, check_time, check_number, \
    check_required, check_in, check_multiple_number, logi
from fcsite.auth import requires_permission, requires_admin

mod = Blueprint('admin', __name__, url_prefix='/admin')


#############
# VALIDATIONS
#############

def validate_practice():
    validations = OrderedDict()
    validations['date'] = [check_required, check_date]
    validations['begintime'] = [check_required, check_time]
    validations['endtime'] = [check_required, check_time]
    validations['loc'] = [check_required]
    validations['no'] = [check_multiple_number]
    do_validate(request.form, validations)


def validate_game():
    validations = OrderedDict()
    validations['name'] = [check_required]
    validations['date'] = [check_required, check_date]
    validations['loc'] = [check_required]
    validations['genre'] = [check_required]
    validations['deadline'] = [check_date]
    validations['begin_acceptance'] = [check_time]
    validations['begin_game'] = [check_time]
    do_validate(request.form, validations)


def validate_event():
    validations = OrderedDict()
    validations['name'] = [check_required]
    validations['date'] = [check_required, check_date]
    validations['loc'] = [check_required]
    validations['deadline'] = [check_date]
    validations['description'] = [check_required]
    do_validate(request.form, validations)


def validate_member():
    validations = OrderedDict()
    validations['name'] = [check_required]
    validations['password'] = [check_number]
    validations['sex'] = [check_in(u'男性', u'女性')]
    do_validate(request.form, validations)


def validate_notice():
    validations = OrderedDict()
    validations['title'] = [check_required]
    validations['begin_show'] = [check_required, check_date]
    validations['end_show'] = [check_required, check_date]
    validations['body'] = [check_required]
    do_validate(request.form, validations)


def validate_saying():
    validations = OrderedDict()
    validations['who'] = [check_required]
    validations['body'] = [check_required]
    do_validate(request.form, validations)


def not_unique_password_error():
    return dict(password=u'被ってるっぽいので別のにしてください')


@mod.route('/')
@requires_admin
def index():
    if g.user.is_schedule_admin():
        return practice()
    if g.user.is_member_admin():
        return member()
    if g.user.is_notice_admin():
        return notice()
    if g.user.is_admin():
        return saying()
    abort(403)


@mod.route('/practice')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def practice():
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    return render_template('admin/practice.html', practices=ps)


@mod.route('/game')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def game():
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    return render_template('admin/game.html', games=gs)


@mod.route('/event')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def event():
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('admin/event.html', events=es)


@mod.route('/member')
@requires_permission(users.PERM_ADMIN_MEMBER)
def member():
    males, females = users.find_group_by_sex()
    return render_template('admin/member.html',
                           males=males, females=females)


@mod.route('/practice_history')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def practice_history():
    ps = [scheds.from_row(s) for s in scheds.find_dones(scheds.TYPE_PRACTICE)]
    ys, ps = schedules_group_by_year(ps)
    return render_template('admin/practice_history.html', years=ys, practices=ps)


@mod.route('/game_history')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def game_history():
    gs = [scheds.from_row(s) for s in scheds.find_dones(scheds.TYPE_GAME)]
    ys, gs = schedules_group_by_year(gs)
    return render_template('admin/game_history.html', years=ys, games=gs)


@mod.route('/event_history')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def event_history():
    es = [scheds.from_row(s) for s in scheds.find_dones(scheds.TYPE_EVENT)]
    ys, es = schedules_group_by_year(es)
    return render_template('admin/event_history.html', years=ys, events=es)


@mod.route('/court')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def court():
    return render_template('admin/court.html', blds=crt.get_blds())


@mod.route('/search_court', methods=['GET', 'POST'])
def search_court():
    return jsonify(crt.search(request.json))


def schedules_group_by_year(schedules):
    years = []
    scheds_by_years = {}
    for y, ss in groupby(schedules, lambda s: s['when_'].year):
        years.append(y)
        scheds_by_years[y] = list(ss)
    return reversed(sorted(years)), scheds_by_years


@mod.route('/practice/<int:id>')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def show_practice(id):
    s = scheds.from_row(scheds.find_by_id(id))
    return render_template("admin/show_practice.html", schedule=s)


@mod.route('/game/<int:id>')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def show_game(id):
    s = scheds.from_row(scheds.find_by_id(id))
    return render_template("admin/show_game.html", schedule=s)


@mod.route('/event/<int:id>')
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def show_event(id):
    s = scheds.from_row(scheds.find_by_id(id))
    return render_template("admin/show_event.html", schedule=s)


def is_yes(name='action'):
    return request.form[name] == u'はい'


modify_practice = dict(
    edit_template='admin/edit_practice.html',
    delete_template='admin/delete_practice.html',
    new='admin.new_practice',
    edit='admin.edit_practice',
    delete='admin.delete_practice',
    index='admin.practice',
    validate=validate_practice,
    make_obj=scheds.make_practice_obj,
    type=scheds.TYPE_PRACTICE)

modify_game = dict(
    edit_template='admin/edit_game.html',
    delete_template='admin/delete_game.html',
    new='admin.new_game',
    edit='admin.edit_game',
    delete='admin.delete_game',
    index='admin.game',
    validate=validate_game,
    make_obj=scheds.make_game_obj,
    type=scheds.TYPE_GAME)

modify_event = dict(
    edit_template='admin/edit_event.html',
    delete_template='admin/delete_event.html',
    new='admin.new_event',
    edit='admin.edit_event',
    delete='admin.delete_event',
    index='admin.event',
    validate=validate_event,
    make_obj=scheds.make_event_obj,
    type=scheds.TYPE_EVENT)


def new_schedule(module):
    if request.method == 'GET':
        today = datetime.today()
        return render_template(module['edit_template'], today=today)
    else:
        moduletype = module['type']
        logi('new schedule: type=%d', moduletype)
        try:
            module['validate']()
        except ValueError, e:
            logi('new schedule: validation error type=%d, errors=%s', moduletype, e.errors.keys())
            today = datetime.today()
            return render_template(module['edit_template'], today=today,
                    errors=e.errors)

        obj = module['make_obj'](request.form)
        logi('new schedule: insert type=%d, when=%s, body=%s', moduletype, obj['when'], obj['body'])
        scheds.insert(moduletype, obj['when'], obj['body'])
        return redirect(url_for(module['index']))


def edit_schedule(id, module):
    if request.method == 'GET':
        s = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template(module['edit_template'], schedule=s)
    else:
        moduletype = module['type']
        logi('edit schedule: type=%d, sid=%d', moduletype, id)
        try:
            module['validate']()
        except ValueError, e:
            logi('edit schedule: validation error type=%d, sid=%d, errors=%s', moduletype, id, e.errors.keys())
            s = scheds.from_row(scheds.find_by_id(id, with_entry=False))
            return render_template(module['edit_template'], schedule=s,
                    errors=e.errors)

        obj = module['make_obj'](request.form)
        logi('edit schedule: update type=%d, sid=%d, when=%s, body=%s', moduletype, id, obj['when'], obj['body'])
        scheds.update(id, obj['when'], obj['body'])
        return redirect(url_for(module['index']))


def delete_schedule(id, module):
    if request.method == 'GET':
        s = scheds.from_row(scheds.find_by_id(id))
        return render_template(module['delete_template'], schedule=s)
    else:
        if is_yes():
            logi('delete schedule: type=%d, sid=%d', module['type'], id)
            scheds.delete_by_id(id)
        else:
            logi('not delete schedule: type=%d, sid=%d', module['type'], id)
        return redirect(url_for(module['index']))


@mod.route('/practice/new', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def new_practice():
    return new_schedule(modify_practice)


@mod.route('/practice/edit/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def edit_practice(id):
    return edit_schedule(id, modify_practice)


@mod.route('/practice/delete/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def delete_practice(id):
    return delete_schedule(id, modify_practice)


@mod.route('/game/new', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def new_game():
    return new_schedule(modify_game)


@mod.route('/game/edit/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def edit_game(id):
    return edit_schedule(id, modify_game)


@mod.route('/game/delete/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def delete_game(id):
    return delete_schedule(id, modify_game)


@mod.route('/event/new', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def new_event():
    return new_schedule(modify_event)


@mod.route('/event/edit/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def edit_event(id):
    return edit_schedule(id, modify_event)


@mod.route('/event/delete/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_SCHEDULE)
def delete_event(id):
    return delete_schedule(id, modify_event)


@mod.route('/member/new', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_MEMBER)
def new_member():
    if request.method == 'GET':
        return render_template('admin/edit_member.html')
    else:
        logi('new member')
        try:
            validate_member()
        except ValueError, e:
            logi('new member: validation error errors=%s', e.errors.keys())
            return render_template('admin/edit_member.html', errors=e.errors)

        u = users.make_obj(request.form)
        logi('new member: insert name=%s', u.name)
        try:
            users.insert(u.name, u.password, u.sex, u.permission)
            return redirect(url_for('admin.member'))
        except users.NotUniquePassword:
            logi('not unique password')
            return render_template('admin/edit_member.html',
                    errors=not_unique_password_error())


@mod.route('/member/edit/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_MEMBER)
def edit_member(id):
    if request.method == 'GET':
        user = users.find_by_id(id)
        return render_template('admin/edit_member.html', user=user)
    else:
        logi('edit member')
        try:
            validate_member()
        except ValueError, e:
            user = users.find_by_id(id)
            logi('edit member: validation error uid=%d', id)
            return render_template('admin/edit_member.html', user=user,
                    errors=e.errors)

        u = users.make_obj(request.form, id)
        logi('edit member: update uid=%d', id)
        try:
            users.update(id, u.password, u.sex, u.permission)
        except users.NotUniquePassword:
            user = users.find_by_id(id)
            logi('not unique password')
            return render_template('admin/edit_member.html', user=user,
                    errors=not_unique_password_error())

        if id != g.user.id:
            return redirect(url_for('admin.member'))
        elif u.is_member_admin():
            return redirect(url_for('admin.member'))
        elif u.is_admin():
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('general.index'))



@mod.route('/member/delete/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_MEMBER)
def delete_member(id):
    if request.method == 'GET':
        user = users.find_by_id(id)
        return render_template('admin/delete_member.html', user=user)
    else:
        if is_yes():
            logi('delete member: uid=%d', id)
            users.delete_by_id(id)
        else:
            logi('not delete member: uid=%d', id)
        return redirect(url_for('admin.member'))


@mod.route('/notice')
@requires_permission(users.PERM_ADMIN_NOTICE)
def notice():
    ns = notices.find_scheduled()
    return render_template('admin/notice.html', notices=ns)


@mod.route('/notice/new', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_NOTICE)
def new_notice():
    if request.method == 'GET':
        return render_template('admin/edit_notice.html')
    else:
        logi('new notice')
        try:
            validate_notice()
        except ValueError, e:
            logi('new notice: validation error')
            return render_template('admin/edit_notice.html', errors=e.errors)

        n = notices.make_obj(request.form)
        notices.insert(n['title'], n['begin_show'], n['end_show'], n['body'])
        return redirect(url_for('admin.notice'))


@mod.route('/notice/edit/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_NOTICE)
def edit_notice(id):
    if request.method == 'GET':
        notice = notices.find_by_id(id)
        return render_template('admin/edit_notice.html', notice=notice)
    else:
        logi('edit notice')
        try:
            validate_notice()
        except ValueError, e:
            logi('edit notice: validation error errors=%s', e.errors.keys())
            notice = notices.find_by_id(id)
            return render_template('admin/edit_notice.html', notice=notice,
                    errors=e.errors)

        n = notices.make_obj(request.form)
        logi('edit notice: update id=%d, begin_show=%s, end_show=%s', id, n['begin_show'], n['end_show'])
        notices.update(id, n['title'], n['begin_show'], n['end_show'],
                n['body'])
        return redirect(url_for('admin.notice'))


@mod.route('/notice/delete/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_NOTICE)
def delete_notice(id):
    if request.method == 'GET':
        notice = notices.find_by_id(id)
        return render_template('admin/delete_notice.html', notice=notice)
    else:
        if is_yes():
            logi('delete notice: id=%d', id)
            notices.delete_by_id(id)
        else:
            logi('not delete notice: id=%d', id)
        return redirect(url_for('admin.notice'))


@mod.route('/saying')
@requires_permission(users.PERM_ADMIN)
def saying():
    (public, private) = sayings.find_all_group_by_publication()
    return render_template('admin/saying.html', public_saying=public,
            private_saying=private)


@mod.route('/saying/new', methods=['POST'])
@requires_permission(users.PERM_ADMIN)
def new_saying():
    logi('new saying')
    try:
        validate_saying()
    except ValueError, e:
        logi('new saying: validation error errors=%s', e.errors.keys())
        (public, private) = sayings.find_all_group_by_publication()
        return render_template('admin/saying.html', public_saying=public,
                private_saying=private, errors=e.errors)

    who = request.form['who']
    body = request.form['body']
    private = 'private' in request.form.getlist('private')
    logi('new saying: insert who=%s, body=%s, private=%s', who, body, private)
    sayings.insert(who, body, private)
    return redirect(url_for('admin.saying'))


@mod.route('/saying/delete/<int:id>')
@requires_permission(users.PERM_ADMIN)
def delete_saying(id):
    sayings.delete(id)
    logi('delete saying: id=%d', id)
    return redirect(url_for('admin.saying'))


#############
# UTILITIES
#############

def get_navigation_list(user):
    navs = []
    if user.is_schedule_admin():
        navs.append(('admin.practice', 'practice', 'glyphicon-calendar', u'活動予定'))
        navs.append(('admin.practice_history', 'practice_history', 'glyphicon-time', u'過去の活動実績'))
        navs.append(('admin.court', 'court', 'glyphicon-search', u'コート検索'))
    if user.is_member_admin():
        navs.append(('admin.member', 'member', 'glyphicon-user', u'メンバー'))
    if user.is_notice_admin():
        navs.append(('admin.notice', 'notice', 'glyphicon-info-sign', u'告知'))
    if user.is_admin():
        navs.append(('admin.saying', 'saying', 'glyphicon-comment', u'名言'))
    return navs
