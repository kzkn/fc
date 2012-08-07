# -*- coding: utf-8 -*-

from flask import Blueprint, request, render_template, redirect, url_for, flash
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


@mod.route('/practice/new', methods=['GET', 'POST'])
def new_practice():
    if request.method == 'GET':
        today = datetime.today()
        return render_template('admin/edit_practice.html', today=today)
    else:
        try:
            validate_practice()
        except ValueError:
            return redirect(url_for('admin.new_practice'))

        p = scheds.make_practice_obj(request.form)
        scheds.insert(scheds.TYPE_PRACTICE, p['when'], p['body'])
        return redirect(url_for('admin.practice'))


@mod.route('/practice/edit/<int:id>', methods=['GET', 'POST'])
def edit_practice(id):
    if request.method == 'GET':
        p = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template('admin/edit_practice.html', practice=p)
    else:
        try:
            validate_practice()
        except ValueError:
            return redirect(url_for('admin.edit_practice', id=id))

        p = scheds.make_practice_obj(request.form)
        scheds.update(id, p['when'], p['body'])
        return redirect(url_for('admin.practice'))


@mod.route('/practice/delete/<int:id>', methods=['GET', 'POST'])
def delete_practice(id):
    if request.method == 'GET':
        p = scheds.from_row(scheds.find_by_id(id))
        return render_template('admin/delete_practice.html', practice=p)
    else:
        action = request.form['action']
        if action == u'はい':
            scheds.delete_by_id(id)
        return redirect(url_for('admin.practice'))


@mod.route('/game/new', methods=['GET', 'POST'])
def new_game():
    if request.method == 'GET':
        today = datetime.today()
        return render_template('admin/edit_game.html', today=today)
    else:
        try:
            validate_game()
        except ValueError:
            return redirect(url_for('admin.new_game'))

        ga = scheds.make_game_obj(request.form)
        scheds.insert(scheds.TYPE_GAME, ga['when'], ga['body'])
        return redirect(url_for('admin.game'))


@mod.route('/game/edit/<int:id>', methods=['GET', 'POST'])
def edit_game(id):
    if request.method == 'GET':
        p = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template('admin/edit_game.html', game=p)
    else:
        try:
            validate_game()
        except ValueError:
            return redirect(url_for('admin.edit_game', id=id))

        ga = scheds.make_game_obj(request.form)
        scheds.update(id, ga['when'], ga['body'])
        return redirect(url_for('admin.game'))


@mod.route('/game/delete/<int:id>', methods=['GET', 'POST'])
def delete_game(id):
    if request.method == 'GET':
        ga = scheds.from_row(scheds.find_by_id(id))
        return render_template('admin/delete_game.html', game=ga)
    else:
        action = request.form['action']
        if action == u'はい':
            scheds.delete_by_id(id)
        return redirect(url_for('admin.game'))


@mod.route('/event/new', methods=['GET', 'POST'])
def new_event():
    if request.method == 'GET':
        today = datetime.today()
        return render_template('admin/edit_event.html', today=today)
    else:
        try:
            validate_event()
        except ValueError, e:
            flash('E:%s' % e.errors)
            return redirect(url_for('admin.new_event'))

        e = scheds.make_event_obj(request.form)
        scheds.insert(scheds.TYPE_EVENT, e['when'], e['body'])
        return redirect(url_for('admin.event'))


@mod.route('/event/edit/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    if request.method == 'GET':
        e = scheds.from_row(scheds.find_by_id(id, with_entry=False))
        return render_template('admin/edit_event.html', event=e)
    else:
        try:
            validate_event()
        except ValueError:
            return redirect(url_for('admin.edit_event', id=id))

        e = scheds.make_event_obj(request.form)
        scheds.update(id, e['when'], e['body'])
        return redirect(url_for('admin.event'))


@mod.route('/event/delete/<int:id>', methods=['GET', 'POST'])
def delete_event(id):
    if request.method == 'GET':
        ga = scheds.from_row(scheds.find_by_id(id))
        return render_template('admin/delete_event.html', event=ga)
    else:
        action = request.form['action']
        if action == u'はい':
            scheds.delete_by_id(id)
        return redirect(url_for('admin.event'))


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
        action = request.form['action']
        if action == u'はい':
            users.delete_by_id(id)
        return redirect(url_for('admin.member'))
