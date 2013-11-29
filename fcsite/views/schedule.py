# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, request, g, abort
from fcsite.models import schedules as scheds
from fcsite.models import entries
from fcsite.auth import requires_login
from fcsite.utils import logi, info_message

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
    is_guest = request.form.get('is-guest', False)
    if is_guest and is_entering_action(action):
        guest_name = request.form['guest-name']
        logi('guest entry to sid=%d, name=%s', sid, guest_name)
        entries.do_guest_entry(sid, guest_name, comment)
    else:
        if is_entering_action(action):
            logi('entry to sid=%d, uid=%d', sid, g.user.id)
            entries.do_entry(sid, comment, entry=True)
        elif is_leaving_action(action):
            logi('exit from sid=%d, uid=%d', sid, g.user.id)
            entries.do_entry(sid, comment, entry=False)
    return redirect(url_for('schedule.schedule'))


def is_entering_action(action):
    return action == u'参加する'


def is_leaving_action(action):
    return action == u'参加しない'


@mod.route('/remove_guest/<int:guest_id>')
@requires_login
def remove_guest(guest_id):
    gu = entries.find_guest_by_id(guest_id)
    if not gu:
        logi('not found guest id: %d', guest_id)
        return abort(404)

    if not entries.has_permission_to_delete_guest(guest_id):
        logi('no permission to delete guest: %d', guest_id)
        return abort(403)

    logi('delete guest: %d', guest_id)
    entries.delete_guest_by_id(guest_id)
    info_message(message=u'%s の参加表明を取り消しました。' % gu['name'],
                 title=u'更新ありがとうございます！')
    return redirect(url_for('schedule.schedule'))
