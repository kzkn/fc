# -*- coding: utf-8 -*-

from flask import g
from fcsite import app, models
from fcsite.utils import sanitize_markdown


class Report(object):
    def __init__(self, record):
        self.id = record['id']
        self.when = record['when_']
        self.author_id = record['author_id']
        self.author_name = record['author_name']
        self.title = record['title']
        self.feature_image_url = record['feature_image_url']
        self.description = record['description']
        self.description_html = record['description_html']
        self.body = record['body']
        self.body_html = record['body_html']

    _older_id_gotten = False
    _newer_id_gotten = False

    @property
    def older_id(self):
        if self._older_id_gotten:
            return self._older_id

        older = models.db().execute("""
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

        newer = models.db().execute("""
            SELECT id
              FROM Report
             WHERE when_ > ?
          ORDER BY when_""", (self.when, )).fetchone()
        self._newer_id = newer['id'] if newer else None
        self._newer_id_gotten = True
        return self._newer_id

    def update(self, title, feature_image_url, description, body):
        desc_html = sanitize_markdown(description)
        body_html = sanitize_markdown(body)
        models.db().execute("""
            UPDATE Report
               SET when_ = datetime('now', 'localtime'),
                   title = ?,
                   feature_image_url = ?,
                   description = ?,
                   description_html = ?,
                   body = ?,
                   body_html = ?
             WHERE id = ?""", (title, feature_image_url,
                 description, desc_html, body, body_html, self.id))
        models.db().commit()

        self.title = title
        self.description = description
        self.description_html = desc_html
        self.body = body
        self.body_html = body_html

    def can_edit_by(self, user):
        return user and (user.is_god() or user.id == self.author_id)

    def delete(self):
        models.db().execute("""
            DELETE FROM Report WHERE id = ?""", (self.id, ))
        models.db().commit()


def find_reports(begin, records=None):
    records = records if records else app.config['REPORTS_PER_PAGE']
    recs = models.db().execute("""
        SELECT Report.id,
               Report.when_,
               Report.author_id,
               User.name as author_name,
               Report.title,
               Report.feature_image_url,
               Report.description,
               Report.description_html,
               Report.body,
               Report.body_html
          FROM Report
               INNER JOIN User ON
                 Report.author_id = User.id
      ORDER BY Report.when_ DESC
         LIMIT ?, ?""", (begin, records)).fetchall()
    return [Report(r) for r in recs]


def count_reports():
    return models.db().execute("SELECT COUNT(*) FROM Report").fetchone()[0]


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
    rec = models.db().execute("""
        SELECT Report.id,
               Report.when_,
               Report.author_id,
               User.name as author_name,
               Report.title,
               Report.feature_image_url,
               Report.description,
               Report.description_html,
               Report.body,
               Report.body_html
          FROM Report
               INNER JOIN User ON
                 Report.author_id = User.id
         WHERE Report.id = ?""", (id, )).fetchone()
    return Report(rec) if rec else None


def insert(title, feature_image_url, description, body):
    with models.db():
        models.db().execute("""
            INSERT INTO Report (when_, author_id, title, feature_image_url,
                                description, description_html, body, body_html)
                 VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?)""",
                 (models.user().id, title, feature_image_url,
                     description, sanitize_markdown(description),
                     body, sanitize_markdown(body)))
        return models.db().execute("""
            SELECT id
              FROM Report
             WHERE when_ = (SELECT MAX(when_) FROM Report)""").fetchone()[0]
