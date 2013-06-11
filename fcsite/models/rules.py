# -*- coding: utf-8 -*-

from fcsite import models


def find_all():
    return models.db().execute("""
        SELECT *
          FROM Rule
      ORDER BY id""").fetchall()


def delete(id):
    models.db().execute("""
        DELETE FROM Rule WHERE id = ?""", (id, ))
    models.db().commit()


def insert(body):
    models.db().execute("""
        INSERT INTO Rule (body) VALUES (?)""", (body, ))
    models.db().commit()
