# -*- coding: utf-8 -*-

import sqlite3
from contextlib import closing
from fcsite import app


def connect_db():
    uri = app.config['DATABASE_URI']
    db = sqlite3.connect(uri, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def insert_test_data():
    with closing(connect_db()) as db:
        with app.open_resource('testdata.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()
