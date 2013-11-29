# -*- coding: utf-8 -*-

from itertools import groupby
from fcsite import models
from fcsite.models import clauses


def find_by_schedules(sids):
    cur = models.db().execute("""
        SELECT User.name AS user_name, Entry.user_id, Entry.schedule_id,
               Entry.comment, Entry.is_entry
          FROM Entry, User
         WHERE User.id = Entry.user_id
           AND Entry.schedule_id IN %s
      ORDER BY Entry.schedule_id, Entry.when_ DESC""" % clauses(sids), sids)
    es = cur.fetchall()
    es_by_sch = groupby(es, lambda e: e['schedule_id'])

    cur.execute("""
        SELECT GuestEntry.id AS guest_id,
               GuestEntry.name, GuestEntry.schedule_id,
               GuestEntry.inviter_id,
               User.name AS inviter_name,
               GuestEntry.comment
          FROM GuestEntry, User
         WHERE User.id = GuestEntry.inviter_id
           AND GuestEntry.schedule_id IN %s
      ORDER BY GuestEntry.schedule_id, GuestEntry.when_ DESC""" % clauses(sids), sids)
    gs = cur.fetchall()
    gs_by_sch = groupby(gs, lambda g: g['schedule_id'])
    return es_by_sch, gs_by_sch


def find_by_schedule(sid):
    cur = models.db().execute("""
            SELECT User.name AS user_name, Entry.user_id,
                   Entry.comment, Entry.is_entry
              FROM Entry, User
             WHERE User.id = Entry.user_id
               AND Entry.schedule_id = ?
          ORDER BY Entry.when_ DESC""", (sid, ))
    es = cur.fetchall()

    cur.execute("""
        SELECT GuestEntry.id AS guest_id, GuestEntry.name,
               GuestEntry.inviter_id, User.name AS inviter_name,
               GuestEntry.comment
          FROM GuestEntry, User
         WHERE User.id = GuestEntry.inviter_id
           AND GuestEntry.schedule_id = ?
      ORDER BY GuestEntry.when_ DESC""", (sid, ))
    gs = cur.fetchall()
    return es, gs


def do_entry(sid, comment, entry):
    if find_my_entry(sid):
        update_entry(sid, comment, entry)
    else:
        insert_entry(sid, comment, entry)


def find_my_entry(sid):
    cur = models.db().execute("""
        SELECT COUNT(*) FROM Entry
        WHERE user_id = ? AND schedule_id = ?""", (models.user().id, sid))
    return cur.fetchone()[0] > 0


def update_entry(sid, comment, entry):
    models.db().execute("""
        UPDATE Entry
           SET is_entry = ?,
               comment = ?,
               when_ = CURRENT_TIMESTAMP
         WHERE user_id = ?
           AND schedule_id = ?""", (entry, comment, models.user().id, sid))
    models.db().commit()


def insert_entry(sid, comment, entry):
    models.db().execute("""
        INSERT INTO Entry (user_id, schedule_id, is_entry, comment)
        VALUES (?, ?, ?, ?)""", (models.user().id, sid, entry, comment))
    models.db().commit()


def do_guest_entry(sid, name, comment):
    models.db().execute("""
        INSERT INTO GuestEntry (name, inviter_id, schedule_id, comment)
        VALUES (?, ?, ?, ?)""", (name, models.user().id, sid, comment))
    models.db().commit()


def has_permission_to_delete_guest(guest_id):
    u = models.user()
    return u.is_god() or \
         models.db().execute("""
            SELECT COUNT(*) FROM GuestEntry
             WHERE id = ? AND inviter_id = ?""", (guest_id, u.id)).fetchone()[0] > 0


def find_guest_by_id(guest_id):
    return models.db().execute("""
        SELECT GuestEntry.id, GuestEntry.name,
               GuestEntry.schedule_id, GuestEntry.comment,
               GuestEntry.inviter_id, User.name AS inviter_name
          FROM GuestEntry, User
         WHERE GuestEntry.id = ?
           AND inviter_id = User.id""", (guest_id, )).fetchone()


def delete_guest_by_id(guest_id):
    models.db().execute("DELETE FROM GuestEntry WHERE id = ?", (guest_id, ))
    models.db().commit()
