# -*- coding: utf-8 -*-

from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from flask import Blueprint, request, render_template, redirect, url_for, g, \
    abort
from fcsite.models import users
from fcsite.models import schedules as scheds
from fcsite.models import notices
from fcsite.utils import do_validate, check_date, check_time, check_number, \
    check_required, check_in
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


def validate_notice():
    validations = OrderedDict()
    validations['title'] = [check_required]
    validations['begin_show'] = [check_required, check_date]
    validations['end_show'] = [check_required, check_date]
    validations['body'] = [check_required]
    do_validate(request.form, validations)


@mod.route('/')
@requires_admin
def index():
    if users.is_schedule_admin(g.user):
        return practice()
    if users.is_member_admin(g.user):
        return member()
    if users.is_notice_admin(g.user):
        return notice()
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
        try:
            module['validate']()
        except ValueError, e:
            today = datetime.today()
            return render_template(module['edit_template'], today=today,
                    errors=e.errors)

        obj = module['make_obj'](request.form)
        scheds.insert(module['type'], obj['when'], obj['body'])
        return redirect(url_for(module['index']))


def edit_schedule(id, module):
    if request.method == 'GET':
        s = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template(module['edit_template'], schedule=s)
    else:
        try:
            module['validate']()
        except ValueError, e:
            s = scheds.from_row(scheds.find_by_id(id, with_entry=False))
            return render_template(module['edit_template'], schedule=s,
                    errors=e.errors)

        obj = module['make_obj'](request.form)
        scheds.update(id, obj['when'], obj['body'])
        return redirect(url_for(module['index']))


def delete_schedule(id, module):
    if request.method == 'GET':
        s = scheds.from_row(scheds.find_by_id(id))
        return render_template(module['delete_template'], schedule=s)
    else:
        if is_yes():
            scheds.delete_by_id(id)
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
        try:
            validate_member()
        except ValueError, e:
            return render_template('admin/edit_member.html', errors=e.errors)

        u = users.make_obj(request.form)
        users.insert(u['name'], u['password'], u['sex'], u['permission'])
        return redirect(url_for('admin.member'))


@mod.route('/member/edit/<int:id>', methods=['GET', 'POST'])
@requires_permission(users.PERM_ADMIN_MEMBER)
def edit_member(id):
    if request.method == 'GET':
        user = users.find_by_id(id)
        return render_template('admin/edit_member.html', user=user)
    else:
        try:
            validate_member()
        except ValueError, e:
            user = users.find_by_id(id)
            return render_template('admin/edit_member.html', user=user,
                    errors=e.errors)

        u = users.make_obj(request.form)
        users.update(id, u['password'], u['sex'], u['permission'])

        if id != g.user['id']:
            return redirect(url_for('admin.member'))
        else:
            if users.is_member_admin(u):
                return redirect(url_for('admin.member'))
            elif users.is_admin(u):
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
            users.delete_by_id(id)
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
        try:
            validate_notice()
        except ValueError, e:
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
        try:
            validate_notice()
        except ValueError, e:
            notice = notices.find_by_id(id)
            return render_template('admin/edit_notice.html', notice=notice,
                    errors=e.errors)

        n = notices.make_obj(request.form)
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
            notices.delete_by_id(id)
        return redirect(url_for('admin.notice'))


#############
# UTILITIES
#############

def get_navigation_list(user):
    navs = []
    if users.is_schedule_admin(user):
        navs.append(('admin.practice', 'practice', 'icon-calendar', u'活動予定'))
    if users.is_member_admin(user):
        navs.append(('admin.member', 'member', 'icon-user', u'メンバー'))
    if users.is_notice_admin(user):
        navs.append(('admin.notice', 'notice', 'icon-info-sign', u'告知'))
    return navs
