# -*- coding: utf-8 -*-

from flask import g


def insert(name, home, email, sex, age, car, has_racket, holiday, experience,
        comment):
    g.db.execute("""
        INSERT INTO JoinRequest (when_, name, home, email, sex, age,
                                 car, has_racket, holiday, experience, comment)
             VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?)""",
                     (name, home, email, sex, age, car, has_racket, holiday,
                         experience, comment))
    g.db.commit()


def count_has_not_handled():
    ret = g.db.execute("""
        SELECT COUNT(*)
          FROM JoinRequest
         WHERE handled = 0""").fetchone()
    return ret[0]


def find_not_handled():
    cur = g.db.execute("""
        SELECT *
          FROM JoinRequest
         WHERE handled = 0
      ORDER BY when_ DESC""")
    return cur.fetchall()


def handle_join_request(id):
    g.db.execute("""
        UPDATE JoinRequest
           SET handled = 1
         WHERE id = ?""", (id, ))
    g.db.commit()
