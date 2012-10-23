# -*- coding: utf-8 -*-

from flask import g
from itertools import groupby


def find_all_group_by_publication():
    sayings = g.db.execute("""
        SELECT *
          FROM Saying
      ORDER BY private""").fetchall()

    bypublication = {}
    for private, ss in groupby(sayings, lambda s: s['private']):
        bypublication[private] = list(ss)

    public = bypublication.get(0, [])
    private = bypublication.get(1, [])
    return public, private


def delete(id):
    g.db.execute("""
        DELETE FROM Saying WHERE id = ?""", (id, ))
    g.db.commit()


def insert(who, body, private):
    g.db.execute("""
        INSERT INTO Saying (who, body, private) VALUES (?, ?, ?)""",
        (who, body, private))
    g.db.commit()


def select_random():
    return g.db.execute("""
        SELECT * FROM Saying ORDER BY RANDOM()""").fetchone()


def select_random_public():
    return g.db.execute("""
        SELECT * FROM Saying WHERE private = 0 ORDER BY RANDOM()""").fetchone()
