#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from flask import Flask, g, render_template

app = Flask(__name__)

import sqlite3
from contextlib import closing


DATABASE_URI = ':memory:'


def connect_db():
    db = sqlite3.connect(DATABASE_URI)
    db.row_factory = sqlite3.Row
    return db


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run('192.168.1.100', debug=True)
