# -*- coding: utf-8 -*-

import json
from itertools import groupby
from flask import g


TYPE_PRACTICE = 1
TYPE_GAME = 2
TYPE_EVENT = 3


def find(type):
    cur = g.db.execute("""
        SELECT *
          FROM Schedule
         WHERE type = ? AND when_ >= datetime('now', 'localtime')
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
      ORDER BY Entry.schedule_id, User.name""" % sids)

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
          ORDER BY User.name""", (sid, ))

        entries = cur.fetchall()
        schedule['entries'] = entries

    return schedule


def find_my_entry(sid):
    cur = g.db.execute("""
        SELECT COUNT(*) FROM Entry
        WHERE user_id = ? AND schedule_id = ?""", (g.user['id'], sid))
    return cur.fetchone()[0] > 0


def update_entry(sid, comment, entry):
    g.db.execute("""
        UPDATE Entry
        SET is_entry = ?, comment = ?
        WHERE user_id = ? AND schedule_id = ?
        """, (entry, comment, g.user['id'], sid))
    g.db.commit()


def insert_entry(sid, comment, entry):
    g.db.execute("""
        INSERT INTO Entry (user_id, schedule_id, is_entry, comment)
        VALUES (?, ?, ?, ?)""", (g.user['id'], sid, entry, comment))
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
    return list(set([json.loads(body[0])['loc'] for body in bodies]))


def from_row(row):
    schedule = {}
    schedule.update(row)
    body = json.loads(row['body'])
    schedule.update(body)
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
    note = form['note']

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
    return json.dumps(p)


def make_game_obj(form):
    name = form['name']
    date = form['date']
    loc = form['loc']
    genre = form['genre']
    deadline = form['deadline']
    price = form['price']
    begin_acceptance = form['begin_acceptance']
    begin_game = form['begin_game']
    note = form['note']

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
    return json.dumps(ga)


def make_event_obj(form):
    name = form['name']
    date = form['date']
    loc = form['loc']
    deadline = form['deadline']
    price = form['price']
    description = form['description']

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
    return json.dumps(e)
