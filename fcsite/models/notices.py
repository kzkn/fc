# -*- coding: utf-8 -*-

from datetime import date
from fcsite import models
from fcsite.utils import sanitize_html


def from_row(row):
    notice = {}
    if not row:
        return notice
    notice.update(row)
    notice['is_showing'] = is_showing(row)
    return notice


def is_showing(notice):
    today = date.today()
    begin = notice['begin_show']
    if today < begin:
        return False
    end = notice['end_show']
    if end < today:
        return False
    return True


def find_by_id(id):
    cur = models.db().execute("""
        SELECT *
          FROM NOTICE
         WHERE id = ?""", (id, ))
    return from_row(cur.fetchone())


def find_scheduled():
    cur = models.db().execute("""
        SELECT *
          FROM Notice
         WHERE end_show >= date('now', 'localtime')
      ORDER BY begin_show""")
    return [from_row(r) for r in cur.fetchall()]


def find_showing():
    cur = models.db().execute("""
        SELECT *
          FROM Notice
         WHERE begin_show <= date('now', 'localtime')
           AND end_show >= date('now', 'localtime')
      ORDER BY begin_show""")
    return [from_row(r) for r in cur.fetchall()]


def insert(title, begin_show, end_show, body):
    models.db().execute("""
        INSERT INTO Notice (title, begin_show, end_show, body)
             VALUES (?, ?, ?, ?)""",
             (title, begin_show, end_show, body))
    models.db().commit()


def update(id, title, begin_show, end_show, body):
    models.db().execute("""
        UPDATE Notice
           SET title = ?,
               begin_show = ?,
               end_show = ?,
               body = ?
         WHERE id = ?""", (title, begin_show, end_show, body, id))
    models.db().commit()


def delete_by_id(id):
    models.db().execute("""
        DELETE FROM Notice
              WHERE id = ?""", (id, ))
    models.db().commit()


def make_obj(form):
    title = form['title']
    begin_show = form['begin_show']
    end_show = form['end_show']
    body = sanitize_html(form['body'])
    return {'title': title,
            'begin_show': begin_show,
            'end_show': end_show,
            'body': body}
