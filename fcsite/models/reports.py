# -*- coding: utf-8 -*-

from flask import g
from fcsite import app


class Report(object):
    def __init__(self, record):
        self.id = record['id']
        self.when = record['when_']
        self.author_name = record['author_name']
        self.title = record['title']
        self.description = record['description']
        self.body = record['body']

    _older_id_gotten = False
    _newer_id_gotten = False

    @property
    def older_id(self):
        if self._older_id_gotten:
            return self._older_id

        older = g.db.execute("""
            SELECT id
              FROM Report
             WHERE when_ < ?
          ORDER BY when_ DESC""", (self.when, )).fetchone()
        self._older_id = older['id'] if older else None
        self._older_id_gotten = True
        return self._older_id

    @property
    def newer_id(self):
        if self._newer_id_gotten:
            return self._newer_id

        newer = g.db.execute("""
            SELECT id
              FROM Report
             WHERE when_ > ?
          ORDER BY when_""", (self.when, )).fetchone()
        self._newer_id = newer['id'] if newer else None
        self._newer_id_gotten = True
        return self._newer_id


def find_reports(begin, records=None):
    records = records if records else app.config['REPORTS_PER_PAGE']
    recs = g.db.execute("""
        SELECT Report.id,
               Report.when_,
               User.name as author_name,
               Report.title,
               Report.description,
               Report.body
          FROM Report
               INNER JOIN User ON
                 Report.author_id = User.id
      ORDER BY Report.when_ DESC
         LIMIT ?, ?""", (begin, records)).fetchall()
    return [Report(r) for r in recs]


def count_reports():
    return g.db.execute("SELECT COUNT(*) FROM Report").fetchone()[0]


def find_reports_on_page(page):
    perpage = app.config['REPORTS_PER_PAGE']
    return find_reports(page * perpage)


def count_pages():
    perpage = app.config['REPORTS_PER_PAGE']
    count = count_reports()
    pages = max(1, count / perpage)
    if pages * perpage < count:
        pages += 1
    return pages


def recent():
    return find_reports(0, 10)


def find_by_id(id):
    rec = g.db.execute("""
        SELECT Report.id,
               Report.when_,
               User.name as author_name,
               Report.title,
               Report.description,
               Report.body
          FROM Report
               INNER JOIN User ON
                 Report.author_id = User.id
         WHERE Report.id = ?""", (id, )).fetchone()
    return Report(rec) if rec else None
