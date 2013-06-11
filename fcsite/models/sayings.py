# -*- coding: utf-8 -*-

from itertools import groupby
from fcsite import models


def find_all_group_by_publication():
    sayings = models.db().execute("""
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
    models.db().execute("""
        DELETE FROM Saying WHERE id = ?""", (id, ))
    models.db().commit()


def insert(who, body, private):
    models.db().execute("""
        INSERT INTO Saying (who, body, private) VALUES (?, ?, ?)""",
        (who, body, private))
    models.db().commit()


def select_random():
    return models.db().execute("""
        SELECT * FROM Saying ORDER BY RANDOM()""").fetchone()


def select_random_public():
    return models.db().execute("""
        SELECT * FROM Saying WHERE private = 0 ORDER BY RANDOM()""").fetchone()
