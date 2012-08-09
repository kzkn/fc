# -*- coding: utf-8 -*-

import sqlite3
from fcsite import app


def connect_db():
    uri = app.config['DATABASE_URI']
    db = sqlite3.connect(uri, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db
