#! -*- coding: utf-8 -*-

from flask import g


__db = None

def set_db(db):
    global __db
    __db = db


def db():
    global __db
    return __db if __db else g.db
