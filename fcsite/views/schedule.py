# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, request
from fcsite.models import schedules as scheds
from fcsite.utils import requires_login

mod = Blueprint('schedule', __name__, url_prefix='/schedule')


@mod.route('/')
@requires_login
def schedule():
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('schedule.html',
                           practices=ps, games=gs, events=es)


@mod.route('/<int:sid>/entry', methods=["POST"])
@requires_login
def entry(sid):
    action = request.form['action']
    comment = request.form['comment']
    if action == u'参加する':
        scheds.do_entry(sid, comment, entry=True)
    elif action == u'参加しない':
        scheds.do_entry(sid, comment, entry=False)
    return redirect(url_for('schedule.schedule'))
