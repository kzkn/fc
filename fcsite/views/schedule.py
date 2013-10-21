# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, request, g
from fcsite.models import schedules as scheds
from fcsite.auth import requires_login
from fcsite.utils import logi

mod = Blueprint('schedule', __name__, url_prefix='/schedule')


@mod.route('/')
@requires_login
def schedule():
    info_msgs = []
    if g.user.has_not_registered_schedule_yet():
        info_msgs.append(u'未登録の練習があります:' +
                u'参加/不参加の登録をお願いします。<br>' +
                u'予定が未定な方は、とりあえず参加/不参加どちらかで登録' +
                u'して、あとで更新してもらっても構いません。')
    ps = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_PRACTICE)]
    gs = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_GAME)]
    es = [scheds.from_row(s) for s in scheds.find(scheds.TYPE_EVENT)]
    return render_template('schedule.html',
                           practices=ps, games=gs, events=es,
                           info_msgs=info_msgs)


@mod.route('/<int:sid>/entry', methods=["POST"])
@requires_login
def entry(sid):
    action = request.form['action']
    comment = request.form['comment']
    if action == u'参加する':
        logi('entry to sid=%d, uid=%d', sid, g.user.id)
        scheds.do_entry(sid, comment, entry=True)
    elif action == u'参加しない':
        logi('exit from sid=%d, uid=%d', sid, g.user.id)
        scheds.do_entry(sid, comment, entry=False)
    return redirect(url_for('schedule.schedule'))
