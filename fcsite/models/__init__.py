#! -*- coding: utf-8 -*-

from flask import g


__db = None

def set_db(db):
    global __db
    __db = db


def db():
    global __db
    return __db if __db else g.db


__user = None

def set_user(user):
    global __user
    __user = user


def user():
    global __user
    return __user if __user else g.user


def clauses(vals):
    return '(' + ','.join('?' * len(vals)) + ')'
