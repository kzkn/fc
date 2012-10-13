# -*- coding: utf-8 -*-

from flask import g


def find_all():
    return g.db.execute("""
        SELECT *
          FROM Rule
      ORDER BY id""").fetchall()


def delete(id):
    g.db.execute("""
        DELETE FROM Rule WHERE id = ?""", (id, ))
    g.db.commit()


def insert(body):
    g.db.execute("""
        INSERT INTO Rule (body) VALUES (?)""", (body, ))
    g.db.commit()
