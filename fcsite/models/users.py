#! -*- coding: utf-8 -*-

from random import randint
from itertools import groupby
from flask import g

SEX_MALE = 1
SEX_FEMALE = 2


def find_by_id(uid):
    cur = g.db.execute('SELECT * FROM User WHERE id = ?', (uid, ))
    return cur.fetchone()


def find_by_password(password):
    cur = g.db.execute('SELECT id, name FROM User WHERE password = ?',
                       (password, ))
    return cur.fetchone()


def find_group_by_sex():
    users = g.db.execute('SELECT * FROM User ORDER BY sex, name').fetchall()
    bysex = {}
    for sex, us in groupby(users, lambda u: u['sex']):
        bysex[sex] = list(us)
    return bysex.get(SEX_MALE, []), bysex.get(SEX_FEMALE, [])


def insert(name, password, sex):
    g.db.execute('''
        INSERT INTO User (name, password, sex)
        VALUES (?, ?, ?)''', (name, password, sex))
    g.db.commit()


def delete_by_id(id):
    g.db.execute('DELETE FROM User WHERE id = ?', (id, ))
    g.db.commit()


def make_obj(form):
    return {'name': form['name'],
            'sex': sex_atoi(form['sex'])}


def sex_atoi(sex):
    return SEX_MALE if sex == u'男性' else SEX_FEMALE


def generate_uniq_password():
    p = randint(100000, 999999)
    while find_by_password(p):
        p = randint(100000, 999999)
    return p
