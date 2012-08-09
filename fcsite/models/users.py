#! -*- coding: utf-8 -*-

from random import randint
from itertools import groupby
from flask import g

SEX_MALE = 1
SEX_FEMALE = 2

PERM_ADMIN = 1
PERM_ADMIN_SCHEDULE = (1 << 1) | PERM_ADMIN
PERM_ADMIN_MEMBER = (1 << 2) | PERM_ADMIN
PERM_ADMIN_GOD = PERM_ADMIN_SCHEDULE | PERM_ADMIN_MEMBER


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


def insert(name, password, sex, permission):
    g.db.execute('''
        INSERT INTO User (name, password, sex, permission)
        VALUES (?, ?, ?, ?)''', (name, password, sex, permission))
    g.db.commit()


def delete_by_id(id):
    g.db.execute('DELETE FROM User WHERE id = ?', (id, ))
    g.db.commit()


def make_obj(form):
    return {'name': form['name'],
            'sex': sex_atoi(form['sex']),
            'permission': permission_atoi(form)}


def sex_atoi(sex):
    return SEX_MALE if sex == u'男性' else SEX_FEMALE


def permission_atoi(form):
    permission = 0
    checks = form.getlist('permissions')
    if 'schedule' in checks:
        permission |= PERM_ADMIN_SCHEDULE
    if 'member' in checks:
        permission |= PERM_ADMIN_MEMBER
    return permission


def generate_uniq_password():
    p = randint(100000, 999999)
    while find_by_password(p):
        p = randint(100000, 999999)
    return p


def has_permission(user, permission):
    p = user['permission']
    return (user['permission'] & permission) == permission


def is_admin(user):
    return has_permission(user, PERM_ADMIN)


def is_schedule_admin(user):
    return has_permission(user, PERM_ADMIN_SCHEDULE)


def is_member_admin(user):
    return has_permission(user, PERM_ADMIN_MEMBER)
