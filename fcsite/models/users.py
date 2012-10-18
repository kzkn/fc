#! -*- coding: utf-8 -*-

from json import dumps, loads
from random import randint
from itertools import groupby
from sqlite3 import IntegrityError
from hashlib import sha1
from datetime import datetime
from flask import g
from fcsite.utils import sanitize_html

SEX_MALE = 1
SEX_FEMALE = 2

PERM_ADMIN = 1
PERM_ADMIN_SCHEDULE = (1 << 1) | PERM_ADMIN
PERM_ADMIN_MEMBER = (1 << 2) | PERM_ADMIN
PERM_ADMIN_NOTICE = (1 << 3) | PERM_ADMIN
PERM_ADMIN_GOD = PERM_ADMIN_SCHEDULE | PERM_ADMIN_MEMBER | PERM_ADMIN_NOTICE

PROFILE_FIELDS = ['email', 'home', 'car', 'comment', 'birthday']


class User(object):
    def __init__(self, row):
        self.id = row['id']
        self.name = row['name']
        self.password = row['password']
        self.sex = row['sex']
        self.permission = row['permission']
        profile = loads(row['profile'])
        self.email = profile.get('email', '')
        self.home = profile.get('home', '')
        self.car = profile.get('car', '')
        self.comment = profile.get('comment', '')
        self.birthday = profile.get('birthday', '')

    def has_permission(self, permission):
        return (self.permission & permission) == permission

    def is_admin(self):
        return self.has_permission(PERM_ADMIN)

    def is_schedule_admin(self):
        return self.has_permission(PERM_ADMIN_SCHEDULE)

    def is_member_admin(self):
        return self.has_permission(PERM_ADMIN_MEMBER)

    def is_notice_admin(self):
        return self.has_permission(PERM_ADMIN_NOTICE)

    def is_god(self):
        return self.has_permission(PERM_ADMIN_GOD)

    def is_male(self):
        return self.sex == SEX_MALE

    def is_female(self):
        return self.sex == SEX_FEMALE


def from_row(row):
    return User(row) if row else {}


def find_by_id(uid):
    cur = g.db.execute('SELECT * FROM User WHERE id = ?', (uid, ))
    return from_row(cur.fetchone())


def find_by_password(password):
    # 特殊ユーザ (id=-1) はログインさせないように無視する
    cur = g.db.execute('SELECT * FROM User WHERE password = ? AND id <> -1',
                       (password, ))
    return from_row(cur.fetchone())


def find_group_by_sex():
    # 特殊ユーザ (id=-1) は一覧上に表示させないように無視する
    users = g.db.execute('''
        SELECT *
          FROM User
         WHERE id <> -1
      ORDER BY sex, id''').fetchall()
    bysex = {}
    for sex, us in groupby(users, lambda u: u['sex']):
        bysex[sex] = [from_row(u) for u in us]
    return bysex.get(SEX_MALE, []), bysex.get(SEX_FEMALE, [])


def is_valid_session_id(uid, sid):
    cur = g.db.execute("""
        SELECT user_id
          FROM MobileSession
         WHERE user_id = ?
           AND session_id = ?
           AND expire > CURRENT_TIMESTAMP""", (uid, sid))
    return cur.fetchone() is not None


def issue_new_session_id(uid):
    for sid in generate_session_id(6):
        try:
            with g.db:
                do_issue_new_session_id(uid, sid)
                return sid
        except IntegrityError:
            pass  # not unique


def generate_session_id(length):
    while True:
        random_value = str(randint(100000, 999999))
        hashcode = sha1(random_value).hexdigest()
        for i in xrange(0, len(hashcode) - length):
            yield hashcode[i:i + length]


def do_issue_new_session_id(uid, sid):
    g.db.execute("""
        DELETE FROM MobileSession
              WHERE user_id = ?""", (uid, ))
    g.db.execute("""
        INSERT INTO MobileSession (user_id, session_id, expire)
             VALUES (?, ?, datetime('now', '+1 month'))""", (uid, sid))


def insert(name, password, sex, permission):
    g.db.execute('''
        INSERT INTO User (name, password, sex, permission)
        VALUES (?, ?, ?, ?)''', (name, password, sex, permission))

    newid = g.db.execute('''
        SELECT id FROM User WHERE name = ?''', (name, )).fetchone()[0]
    g.db.execute('''
        INSERT INTO Tax (user_id, year, paid_first, paid_second)
             VALUES (?, ?, ?, ?)''', (newid, datetime.now().year, 0, 0))

    g.db.commit()


def update(id, password, sex, permission):
    g.db.execute('''
        UPDATE User
           SET password = ?,
               sex = ?,
               permission = ?
         WHERE id = ?''', (password, sex, permission, id))
    g.db.commit()


def update_profile(id, form):
    password = get_or_gen_password(form)
    sex = sex_atoi(form['sex'])
    birthday = form['birthday']
    email = form['email']
    home = form['home']
    car = form['car']
    comment = sanitize_html(form['comment'])
    profile = dumps({
        'birthday': birthday,
        'email': email,
        'home': home,
        'car': car,
        'comment': comment
        })
    g.db.execute('''
        UPDATE User
           SET password = ?,
               sex = ?,
               profile = ?
         WHERE id = ?''', (password, sex, profile, id))
    g.db.commit()


def delete_by_id(id):
    g.db.execute('DELETE FROM User WHERE id = ?', (id, ))
    g.db.commit()


def make_obj(form, id=-9999):
    dummy_row = {'id': id,
            'name': form['name'],
            'password': get_or_gen_password(form),
            'sex': sex_atoi(form['sex']),
            'permission': permission_atoi(form),
            'profile': '{}'}
    return User(dummy_row)


def get_or_gen_password(form):
    p = form['password']
    return p if p else generate_uniq_password()


def sex_atoi(sex):
    return SEX_MALE if sex == u'男性' else SEX_FEMALE


def permission_atoi(form):
    permission = 0
    checks = form.getlist('permissions')
    if 'schedule' in checks:
        permission |= PERM_ADMIN_SCHEDULE
    if 'member' in checks:
        permission |= PERM_ADMIN_MEMBER
    if 'notice' in checks:
        permission |= PERM_ADMIN_NOTICE
    return permission


def generate_uniq_password():
    p = randint(100000, 999999)
    while find_by_password(p):
        p = randint(100000, 999999)
    return p
