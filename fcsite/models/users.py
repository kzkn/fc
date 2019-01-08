#! -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from json import dumps, loads
from random import randint
from itertools import groupby
from sqlite3 import IntegrityError
from hashlib import sha1
from fcsite import models
from fcsite.models import schedules as scheds
from fcsite.models import stats
from fcsite.utils import sanitize_html

SPECIAL_USER = -1

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
        self.joined = row['joined']
        self.logged_in = row['logged_in']
        profile = loads(row['profile'])
        self.email = profile.get('email', '')
        self.home = profile.get('home', '')
        self.car = profile.get('car', '')
        self.comment = profile.get('comment', '')
        self.birthday = profile.get('birthday', '')

        self.entry_rate_cache = dict()

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

    def is_registered(self, schedule):
        cur = models.db().execute("""
            SELECT Schedule.id,
                   Schedule.type,
                   Schedule.body,
                   Entry.user_id
              FROM Schedule
                   LEFT OUTER JOIN (SELECT schedule_id,
                                           user_id
                                      FROM Entry
                                     WHERE user_id = ?) Entry ON
                     Schedule.id = Entry.schedule_id
             WHERE Schedule.id = ?""", (self.id, schedule['id']))
        s = cur.fetchone()
        if not s:  # スケジュールが存在しない
            return False
        if s['user_id'] is not None:  # 登録済み
            return True
        if s['type'] == scheds.TYPE_PRACTICE:  # 練習 未登録
            return False

        # 試合、イベント 未登録 締め切り確認
        body = loads(s['body'])
        return scheds.is_deadline_overred(body)

    def is_entered(self, schedule):
        cur = models.db().execute("""
            SELECT user_id
              FROM Entry
             WHERE user_id = ?
               AND schedule_id = ?
               AND is_entry = 1""", (self.id, schedule['id']))
        return cur.fetchone() is not None

    def has_not_registered_schedule_yet(self):
        cur = models.db().execute("""
            SELECT Schedule.id
              FROM Schedule
                   LEFT OUTER JOIN (SELECT *
                                      FROM Entry
                                     WHERE user_id = ?) AS Entry ON
                     Schedule.id = Entry.schedule_id
             WHERE Schedule.when_ >= datetime('now', 'localtime')
               AND Schedule.type = ?
          GROUP BY Schedule.id
            HAVING COUNT(Entry.user_id) = 0""",
            (self.id, scheds.TYPE_PRACTICE))
        return cur.fetchone() is not None

    def is_joined_at(self, year):
        dt = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        return self.joined < dt

    def get_entry_rate(self, year):
        r = self.entry_rate_cache.get(year, None)
        if not r:
            r = stats.get_practice_entry_rate_of_year(self, year)
            self.entry_rate_cache[year] = r
        return r

    def update_logged_in(self):
        db = models.db()
        db.execute("""
            UPDATE User
               SET logged_in = datetime('now', 'localtime')
             WHERE id = ?""", (self.id, ))
        db.commit()

class NotUniquePassword(Exception):
    def __init__(self):
        pass


def from_row(row):
    return User(row) if row else {}


def find_all():
    # 特殊ユーザ以外
    cur = models.db().execute("SELECT * FROM User WHERE id <> ?", (SPECIAL_USER, ))
    return [from_row(r) for r in cur.fetchall()]

def find_by_id(uid):
    cur = models.db().execute('SELECT * FROM User WHERE id = ?', (uid, ))
    return from_row(cur.fetchone())


def find_by_password(password):
    # 特殊ユーザはログインさせないように無視する
    cur = models.db().execute('SELECT * FROM User WHERE password = ? AND id <> ?',
                       (password, SPECIAL_USER))
    return from_row(cur.fetchone())


def find_group_by_sex():
    # 特殊ユーザは一覧上に表示させないように無視する
    users = models.db().execute('''
        SELECT *
          FROM User
         WHERE id <> ?
      ORDER BY sex, id''', (SPECIAL_USER, )).fetchall()
    bysex = {}
    for sex, us in groupby(users, lambda u: u['sex']):
        bysex[sex] = [from_row(u) for u in us]
    return bysex.get(SEX_MALE, []), bysex.get(SEX_FEMALE, [])


def is_valid_session_id(uid, sid):
    cur = models.db().execute("""
        SELECT user_id
          FROM MobileSession
         WHERE user_id = ?
           AND session_id = ?
           AND expire > CURRENT_TIMESTAMP""", (uid, sid))
    return cur.fetchone() is not None


def issue_new_session_id(uid):
    for sid in generate_session_id(6):
        try:
            with models.db():
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
    models.db().execute("""
        DELETE FROM MobileSession
              WHERE user_id = ?""", (uid, ))
    models.db().execute("""
        INSERT INTO MobileSession (user_id, session_id, expire)
             VALUES (?, ?, datetime('now', '+1 month'))""", (uid, sid))


def check_unique_password(password, id=None):
    db = models.db()
    if id is not None:
        cnt = db.execute("""
            SELECT COUNT(*)
              FROM User
             WHERE password = ?
               AND id <> ?""", (password, id)).fetchone()
    else:
        cnt = db.execute("""
            SELECT COUNT(*)
              FROM User
             WHERE password = ?""", (password, )).fetchone()

    if cnt[0] > 0:
        raise NotUniquePassword()


def insert(name, password, sex, permission):
    check_unique_password(password)
    try:
        db = models.db()
        c = db.cursor()
        c.execute("""
            INSERT INTO User (name, password, sex, permission)
            VALUES (?, ?, ?, ?)""", (name, password, sex, permission))
        db.commit()
        return c.lastrowid
    except IntegrityError, e:
        raise NotUniquePassword()  # そうとは限らないけど。。。


def update(id, password, sex, permission):
    check_unique_password(password, id)
    try:
        db = models.db()
        db.execute("""
            UPDATE User
               SET password = ?,
                   sex = ?,
                   permission = ?
             WHERE id = ?""", (password, sex, permission, id))
        db.commit()
    except IntegrityError, e:
        raise NotUniquePassword()  # そうとは限らないけど。。。


def update_profile(id, form):
    password = get_or_gen_password(form)
    check_unique_password(password, id)

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
    models.db().execute('''
        UPDATE User
           SET password = ?,
               sex = ?,
               profile = ?
         WHERE id = ?''', (password, sex, profile, id))
    models.db().commit()


def delete_by_id(id):
    db = models.db()
    db.execute('UPDATE TaxPaymentHistory SET user_id = ? WHERE user_id = ?', (SPECIAL_USER, id))
    db.execute('UPDATE TaxPaymentHistory SET updater_user_id = ? WHERE updater_user_id = ?', (SPECIAL_USER, id))
    db.execute('DELETE FROM User WHERE id = ?', (id, ))
    db.commit()


def make_obj(form, id=-9999):
    dummy_row = {'id': id,
            'name': form['name'],
            'password': get_or_gen_password(form),
            'sex': sex_atoi(form['sex']),
            'permission': permission_atoi(form),
            'joined': datetime.now(),
            'logged_in': None,
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
