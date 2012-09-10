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
