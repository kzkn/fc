# -*- coding: utf-8 -*-

from sqlite3 import connect, PARSE_DECLTYPES, Row
from fcsite import app


def connect_db():
    uri = app.config['DATABASE_URI']
    db = connect(uri, detect_types=PARSE_DECLTYPES)
    db.row_factory = Row
    return db
