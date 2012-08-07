# -*- coding: utf-8 -*-

from flask import Blueprint, request, render_template, redirect, url_for
from fcsite.models import users
from fcsite.models import schedules as scheds
from fcsite.utils import do_validate, check_date, check_time, check_number, \
    check_required, check_in, longzip

from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

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


@mod.route('/')
@mod.route('/practice')
def practice():
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    return render_template('admin/practice.html', practices=ps)


@mod.route('/game')
def game():
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    return render_template('admin/game.html', games=gs)


@mod.route('/event')
def event():
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('admin/event.html', events=es)


@mod.route('/member')
def member():
    males, females = users.find_group_by_sex()
    return render_template('admin/member.html',
                           users=longzip(males, females))


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
        except ValueError:
            return redirect(url_for(module['new']))

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
        except ValueError:
            return redirect(url_for(module['edit'], id=id))

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
def new_practice():
    return new_schedule(modify_practice)


@mod.route('/practice/edit/<int:id>', methods=['GET', 'POST'])
def edit_practice(id):
    return edit_schedule(id, modify_practice)


@mod.route('/practice/delete/<int:id>', methods=['GET', 'POST'])
def delete_practice(id):
    return delete_schedule(id, modify_practice)


@mod.route('/game/new', methods=['GET', 'POST'])
def new_game():
    return new_schedule(modify_game)


@mod.route('/game/edit/<int:id>', methods=['GET', 'POST'])
def edit_game(id):
    return edit_schedule(id, modify_game)


@mod.route('/game/delete/<int:id>', methods=['GET', 'POST'])
def delete_game(id):
    return delete_schedule(id, modify_game)


@mod.route('/event/new', methods=['GET', 'POST'])
def new_event():
    return new_schedule(modify_event)


@mod.route('/event/edit/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    return edit_schedule(id, modify_event)


@mod.route('/event/delete/<int:id>', methods=['GET', 'POST'])
def delete_event(id):
    return delete_schedule(id, modify_event)


@mod.route('/member/new', methods=['GET', 'POST'])
def new_member():
    if request.method == 'GET':
        return render_template('admin/edit_member.html')
    else:
        try:
            validate_member()
        except ValueError:
            return redirect(url_for('admin.member'))

        u = users.make_obj(request.form)
        password = users.generate_uniq_password()
        users.insert(u['name'], str(password), u['sex'])
        return redirect(url_for('admin.member'))


@mod.route('/member/delete/<int:id>', methods=['GET', 'POST'])
def delete_member(id):
    if request.method == 'GET':
        user = users.find_by_id(id)
        return render_template('admin/delete_member.html', user=user)
    else:
        if is_yes():
            users.delete_by_id(id)
        return redirect(url_for('admin.member'))
