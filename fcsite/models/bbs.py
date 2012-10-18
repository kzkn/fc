# -*- coding: utf-8 -*-

from datetime import datetime
from flask import g
from fcsite import app
from fcsite.utils import sanitize_html


def find_posts(begin):
    records = app.config['BBS_PER_PAGE']
    return g.db.execute("""
        SELECT User.name AS user_name,
               BBS.when_,
               BBS.body
          FROM User, BBS
         WHERE BBS.user_id = User.id
      ORDER BY BBS.when_ DESC
         LIMIT ?, ?""", (begin, records))


def count_posts():
    return g.db.execute("SELECT COUNT(*) FROM BBS").fetchone()[0]


def post(body):
    g.db.execute("""
        INSERT INTO BBS (user_id, when_, body) VALUES (?, ?, ?)""", (
            g.user.id,
            datetime.now(),
            sanitize_html(body)))
    g.db.commit()


def find_posts_on_page(page):
    perpage = app.config['BBS_PER_PAGE']
    return find_posts(page * perpage)


def count_pages():
    perpage = app.config['BBS_PER_PAGE']
    count = count_posts()
    pages = max(1, count / perpage)
    if pages * perpage < count:
        pages += 1
    return pages
