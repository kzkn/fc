# -*- coding: utf-8 -*-

from json import loads, dumps
from itertools import groupby
from time import strptime
from datetime import datetime
from flask import g
from fcsite.utils import sanitize_html


TYPE_PRACTICE = 1
TYPE_GAME = 2
TYPE_EVENT = 3


def find(type):
    cur = g.db.execute("""
        SELECT Schedule.id,
               Schedule.type,
               Schedule.when_,
               Schedule.body,
               (SELECT COUNT(*)
                  FROM Entry
                 WHERE schedule_id = Schedule.id
                   AND is_entry) AS entry_count
          FROM Schedule
         WHERE type = ?
           AND when_ >= date('now', 'localtime')
      ORDER BY when_""", (type, ))

    # Row -> dict for `entries'
    schedules = [dict(r) for r in cur.fetchall()]

    sids = '(%s)' % ','.join([str(s['id']) for s in schedules])
    cur.execute("""
        SELECT User.name AS user_name, Entry.user_id, Entry.schedule_id,
               Entry.comment, Entry.is_entry
          FROM Entry, User
         WHERE User.id = Entry.user_id
           AND Entry.schedule_id IN %s
      ORDER BY Entry.schedule_id, Entry.when_ DESC""" % sids)

    entries = cur.fetchall()

    if entries:
        # make schedule-entry tree
        sid2sc = {}
        for s in schedules:
            sid2sc[s['id']] = s

        for sid, es in groupby(entries, lambda e: e['schedule_id']):
            schedule = sid2sc.get(sid, None)
            if schedule:
                schedule['entries'] = list(es)

    return schedules


def find_by_id(sid, with_entry=True):
    cur = g.db.execute("""
        SELECT *
          FROM Schedule
         WHERE id = ?""", (sid, ))

    schedule = dict(cur.fetchone())

    if with_entry:
        cur.execute("""
            SELECT User.name AS user_name, Entry.user_id,
                   Entry.comment, Entry.is_entry
              FROM Entry, User
             WHERE User.id = Entry.user_id
               AND Entry.schedule_id = ?
          ORDER BY Entry.when_ DESC""", (sid, ))

        entries = cur.fetchall()
        schedule['entries'] = entries

    return schedule


def find_my_entry(sid):
    cur = g.db.execute("""
        SELECT COUNT(*) FROM Entry
        WHERE user_id = ? AND schedule_id = ?""", (g.user.id, sid))
    return cur.fetchone()[0] > 0


def find_non_registered(uid, type):
    cur = g.db.execute("""
        SELECT Schedule.id AS id,
               Schedule.type AS type,
               Schedule.when_ AS when_,
               Schedule.body AS body,
               (SELECT COUNT(*)
                  FROM Entry
                 WHERE schedule_id = Schedule.id
                   AND is_entry) AS entry_count
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


def has_non_registered_practice(uid):
    cur = g.db.execute("""
        SELECT Schedule.id
          FROM Schedule
               LEFT OUTER JOIN (SELECT *
                                  FROM Entry
                                 WHERE user_id = ?) AS Entry ON
                 Schedule.id = Entry.schedule_id
         WHERE Schedule.when_ >= datetime('now', 'localtime')
           AND Schedule.type = ?
      GROUP BY Schedule.id
        HAVING COUNT(Entry.user_id) = 0""", (uid, TYPE_PRACTICE))
    return cur.fetchone() is not None


def update_entry(sid, comment, entry):
    g.db.execute("""
        UPDATE Entry
           SET is_entry = ?,
               comment = ?,
               when_ = CURRENT_TIMESTAMP
         WHERE user_id = ?
           AND schedule_id = ?""", (entry, comment, g.user.id, sid))
    g.db.commit()


def insert_entry(sid, comment, entry):
    g.db.execute("""
        INSERT INTO Entry (user_id, schedule_id, is_entry, comment)
        VALUES (?, ?, ?, ?)""", (g.user.id, sid, entry, comment))
    g.db.commit()


def insert(type, when_, body):
    g.db.execute("""
        INSERT INTO Schedule (type, when_, body)
        VALUES (?, ?, ?)""", (type, when_, body))
    g.db.commit()


def update(sid, when_, body):
    g.db.execute("""
        UPDATE Schedule
           SET when_ = ?,
               body = ?
         WHERE id = ?""", (when_, body, sid))
    g.db.commit()


def delete_by_id(sid):
    g.db.execute("""
        DELETE FROM Schedule
         WHERE id = ?""", (sid, ))
    g.db.commit()


def find_practice_locations():
    cur = g.db.execute(
        "SELECT body FROM Schedule WHERE type = ?", (TYPE_PRACTICE, ))
    bodies = cur.fetchall()
    return list(set([loads(body[0])['loc'] for body in bodies]))


def is_registered(uid, sid):
    cur = g.db.execute("""
        SELECT Schedule.id,
               Schedule.type,
               Schedule.body,
               Entry.user_id
          FROM Schedule
               LEFT OUTER JOIN (SELECT schedule_id,
                                       user_id
                                  FROM Entry
                                 WHERE user_id = ?) Entry ON
                 Schedule.id = Entry.schedule_id
         WHERE Schedule.id = ?""", (uid, sid))
    s = cur.fetchone()
    if not s:  # スケジュールが存在しない
        return False
    if s['user_id'] is not None:  # 登録済み
        return True
    if s['type'] == TYPE_PRACTICE:  # 練習 未登録
        return False

    # 試合、イベント 未登録 締め切り確認
    body = loads(s['body'])
    return is_deadline_overred(body)


def is_deadline_overred(schedule_body):
    if not schedule_body.get('deadline', None):  # 締め切りなし
        return False
    tm = strptime(schedule_body['deadline'], '%Y-%m-%d')
    deadline = datetime(tm.tm_year, tm.tm_mon, tm.tm_mday)
    return deadline < datetime.now()


def is_entered(uid, sid):
    cur = g.db.execute("""
        SELECT user_id
          FROM Entry
         WHERE user_id = ?
           AND schedule_id = ?
           AND is_entry = 1""", (uid, sid))
    return cur.fetchone() is not None


def count_schedules(type):
    cur = g.db.execute("""
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


def do_entry(sid, comment, entry):
    if find_my_entry(sid):
        update_entry(sid, comment, entry)
    else:
        insert_entry(sid, comment, entry)


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
