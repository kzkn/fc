# -*- coding: utf-8 -*-

from flask import g
from datetime import date
from fcsite.utils import htmlize_textarea_body, sanitize_html


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
    cur = g.db.execute("""
        SELECT *
          FROM NOTICE
         WHERE id = ?""", (id, ))
    return from_row(cur.fetchone())


def find_scheduled():
    cur = g.db.execute("""
        SELECT *
          FROM Notice
         WHERE end_show >= date('now', 'localtime')
      ORDER BY begin_show""")
    return [from_row(r) for r in cur.fetchall()]


def find_showing():
    cur = g.db.execute("""
        SELECT *
          FROM Notice
         WHERE begin_show <= date('now', 'localtime')
           AND end_show >= date('now', 'localtime')
      ORDER BY begin_show""")
    return [from_row(r) for r in cur.fetchall()]


def insert(title, begin_show, end_show, body):
    g.db.execute("""
        INSERT INTO Notice (title, begin_show, end_show, body)
             VALUES (?, ?, ?, ?)""",
             (title, begin_show, end_show, body))
    g.db.commit()


def update(id, title, begin_show, end_show, body):
    g.db.execute("""
        UPDATE Notice
           SET title = ?,
               begin_show = ?,
               end_show = ?,
               body = ?
         WHERE id = ?""", (title, begin_show, end_show, body, id))
    g.db.commit()


def delete_by_id(id):
    g.db.execute("""
        DELETE FROM Notice
              WHERE id = ?""", (id, ))
    g.db.commit()


def make_obj(form):
    title = form['title']
    begin_show = form['begin_show']
    end_show = form['end_show']
    body = sanitize_html(htmlize_textarea_body(form['body']))
    return {'title': title,
            'begin_show': begin_show,
            'end_show': end_show,
            'body': body}
