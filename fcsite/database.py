# -*- coding: utf-8 -*-

from sqlite3 import connect, PARSE_DECLTYPES, Row, IntegrityError
from fcsite import app


def connect_db():
    uri = app.config['DATABASE_URI']
    db = connect(uri, detect_types=PARSE_DECLTYPES)
    db.row_factory = Row
    db.execute('PRAGMA foreign_keys = ON')
    return db


def initialize():
    db = connect_db()
    with db:
        force_insert(db, """
            INSERT INTO User (id, name, password, sex)
                 VALUES (-1, '---', '!@#$%^&*()', 1)""")
    db.close()


def force_insert(db, sql):
    try:
        db.execute(sql)
    except IntegrityError:
        pass
