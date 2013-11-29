# -*- coding: utf-8 -*-

from json import loads, dumps
from itertools import groupby
from time import strptime
from datetime import datetime, timedelta
from flask import g
from fcsite import models
from fcsite.models import entries
from fcsite.utils import sanitize_html


TYPE_PRACTICE = 1
TYPE_GAME = 2
TYPE_EVENT = 3


def find(type):
    return find_future_or_past(type,
                               "when_ >= date('now', 'localtime')",
                               "when_")


def find_dones(type):
    return find_future_or_past(type,
                               "when_ < date('now', 'localtime')",
                               "when_ DESC")


def find_future_or_past(type, condition, order):
    cur = models.db().execute("""
        SELECT Schedule.id,
               Schedule.type,
               Schedule.when_,
               Schedule.body,
               ((SELECT COUNT(*) FROM Entry WHERE schedule_id = Schedule.id AND is_entry)
                +
                (SELECT COUNT(*) FROM GuestEntry WHERE schedule_id = Schedule.id)) AS entry_count,
               (SELECT COUNT(*) FROM Entry WHERE schedule_id = Schedule.id AND NOT is_entry) AS not_entry_count
          FROM Schedule
         WHERE type = ?
           AND %s
      ORDER BY %s""" % (condition, order), (type, ))

    # Row -> dict for `entries'
    schedules = [dict(r) for r in cur.fetchall()]
    sids = [s['id'] for s in schedules]

    es_by_sch, gs_by_sch = entries.find_by_schedules(sids)

    if es_by_sch or gs_by_sch:
        # make schedule-entry tree
        sid2sc = {}
        for s in schedules:
            sid2sc[s['id']] = s

        for sid, es in es_by_sch:
            schedule = sid2sc.get(sid, None)
            if schedule:
                schedule['entries'] = list(es)

        for sid, gs in gs_by_sch:
            schedule = sid2sc.get(sid, None)
            if schedule:
                schedule['guests'] = list(gs)

    return schedules


def find_by_id(sid, with_entry=True):
    cur = models.db().execute("""
        SELECT *
          FROM Schedule
         WHERE id = ?""", (sid, ))

    schedule = dict(cur.fetchone())

    if with_entry:
        es, gs = entries.find_by_schedule(sid)
        schedule['entries'] = es
        schedule['guests'] = gs

    return schedule


def find_non_registered(uid, type):
    cur = models.db().execute("""
        SELECT Schedule.id AS id,
               Schedule.type AS type,
               Schedule.when_ AS when_,
               Schedule.body AS body,
               ((SELECT COUNT(*) FROM Entry WHERE schedule_id = Schedule.id AND is_entry)
                +
                (SELECT COUNT(*) FROM GuestEntry WHERE schedule_id = Schedule.id)) AS entry_count,
          FROM Schedule
               LEFT OUTER JOIN (SELECT *
                                  FROM Entry
                                 WHERE user_id = ?) AS Entry ON
                 Schedule.id = Entry.schedule_id
         WHERE Schedule.when_ >= datetime('now', 'localtime')
           AND Schedule.type = ?
      GROUP BY Schedule.id
        HAVING COUNT(Entry.user_id) = 0
      ORDER BY Schedule.when_""", (uid, type))
    return cur.fetchall()


def insert(type, when_, body):
    models.db().execute("""
        INSERT INTO Schedule (type, when_, body)
        VALUES (?, ?, ?)""", (type, when_, body))
    models.db().commit()


def update(sid, when_, body):
    models.db().execute("""
        UPDATE Schedule
           SET when_ = ?,
               body = ?
         WHERE id = ?""", (when_, body, sid))
    models.db().commit()


def delete_by_id(sid):
    models.db().execute("""
        DELETE FROM Schedule
         WHERE id = ?""", (sid, ))
    models.db().commit()


def find_practice_locations():
    cur = models.db().execute(
        "SELECT body FROM Schedule WHERE type = ?", (TYPE_PRACTICE, ))
    bodies = cur.fetchall()
    return list(set([loads(body[0])['loc'] for body in bodies]))


def is_deadline_overred(schedule_body):
    if not schedule_body.get('deadline', None):  # 締め切りなし
        return False
    tm = strptime(schedule_body['deadline'], '%Y-%m-%d')
    # 「その日のうちに」ということで、次の日の 0 時を過ぎたかどうかチェック
    deadline = datetime(tm.tm_year, tm.tm_mon, tm.tm_mday) + timedelta(1)
    return deadline < datetime.now()


def count_schedules(type):
    cur = models.db().execute("""
        SELECT COUNT(*)
          FROM Schedule
         WHERE type = ?
           AND when_ >= datetime('now', 'localtime')""", (type, ))
    return cur.fetchone()[0]


def from_row(row):
    schedule = {}
    if not row:
        return schedule
    schedule.update(row)
    body = loads(row['body'])
    schedule.update(body)
    schedule['deadline_overred'] = is_deadline_overred(body)
    return schedule


def make_practice_obj(form):
    date = form['date']
    begintime = form['begintime']
    endtime = form['endtime']
    loc = form['loc']
    court = form['court']
    no = form['no']
    price = form['price']
    note = sanitize_html(form['note'])

    when = date + ' ' + begintime + ':00'
    body = make_practice_body(endtime, loc, court, no, price, note)
    return {'when': when,
            'body': body}


def make_practice_body(end, loc, court, no, price, note):
    p = {'end': end,
         'loc': loc,
         'court': court,
         'no': no,
         'price': price,
         'note': note}
    return dumps(p)


def make_game_obj(form):
    name = form['name']
    date = form['date']
    loc = form['loc']
    genre = form['genre']
    deadline = form['deadline']
    price = form['price']
    begin_acceptance = form['begin_acceptance']
    begin_game = form['begin_game']
    note = sanitize_html(form['note'])

    when = date + ' 00:00:00'
    body = make_game_body(
        name, loc, genre, deadline, price, begin_acceptance, begin_game, note)
    return {'when': when,
            'body': body}


def make_game_body(
        name, loc, genre, deadline, price, begin_acceptance, begin_game, note):
    ga = {'name': name,
          'loc': loc,
          'genre': genre,
          'deadline': deadline,
          'price': price,
          'begin_acceptance': begin_acceptance,
          'begin_game': begin_game,
          'note': note}
    return dumps(ga)


def make_event_obj(form):
    name = form['name']
    date = form['date']
    loc = form['loc']
    deadline = form['deadline']
    price = form['price']
    description = sanitize_html(form['description'])

    when = date + ' 00:00:00'
    body = make_event_body(name, loc, deadline, price, description)
    return {'when': when,
            'body': body}


def make_event_body(name, loc, deadline, price, description):
    e = {'name': name,
         'loc': loc,
         'deadline': deadline,
         'price': price,
         'description': description}
    return dumps(e)


def is_entried(sched, user_id):
    for e in sched.get('entries', []):
        if e['user_id'] == user_id:
            return e['is_entry']
    return False
