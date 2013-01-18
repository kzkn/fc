# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from flask import g

MINIMUM_YEAR = 2012


def years():
    return range(MINIMUM_YEAR, datetime.now().year + 1)


def seasons():
    return range(1, 13)


class Payment(object):
    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id
        self.paid_seasons = []

    def pay(self, year, season):
        self.paid_seasons.append((year, season))

    def is_paid(self, year, season):
        return (year, season) in self.paid_seasons

    def season_status(self, year, season):
        last = datetime(year, season, 1)
        for y in years():
            if y != year:
                continue
            for m in seasons():
                if datetime(y, m, 1) > last:
                    break
                if not self.is_paid(y, m):
                    return False
        return True


class PaymentStats(object):
    def __init__(self, year, payments, histories):
        self.year = year
        self.payments = payments
        self.histories = histories

    def rate_of_payments(self):
        total = 0
        paid = 0
        now = datetime.now()
        for m in seasons():
            if now >= datetime(self.year, m, 1):
                total += len(self.payments)
            paid += sum([1 for p in self.payments if p.is_paid(self.year, m)])
        return paid / float(total)

    def __iter__(self):
        return self.Iter(self)

    def is_latest(self):
        return self.year == datetime.now().year

    class Iter(object):
        def __init__(self, stats):
            self.stats = stats
            self.idx = 0
            self.season = datetime.now().month if stats.is_latest() else 12

        def next(self):
            payments = self.stats.payments
            if self.idx == len(payments):
                raise StopIteration()

            p = payments[self.idx]
            self.idx += 1
            return (p.user_id,
                    p.name,
                    p.season_status(self.stats.year, self.season))


def find_all():
    taxes = g.db.execute("""
        SELECT User.name,
               Tax.user_id,
               Tax.year,
               Tax.season
          FROM User
               LEFT OUTER JOIN Tax ON
                 User.id = Tax.user_id
         WHERE User.id <> -1
      ORDER BY User.sex, User.id""").fetchall()

    payments = []
    id_and_name = lambda x: (x['user_id'], x['name'])
    for (user_id, name), paid_seasons in groupby(taxes, id_and_name):
        p = Payment(user_id, name)
        for paid_season in paid_seasons:
            p.pay(paid_season['year'], paid_season['season'])
        payments.append(p)

    stats = []
    for y in reversed(years()):
        histories = g.db.execute("""
            SELECT User.name,
                   Updater.name AS updater,
                   TaxPaymentHistory.year,
                   TaxPaymentHistory.season,
                   TaxPaymentHistory.action,
                   TaxPaymentHistory.when_
              FROM TaxPaymentHistory
                   INNER JOIN User ON
                     User.id = TaxPaymentHistory.user_id
                   INNER JOIN User AS Updater ON
                     Updater.id = TaxPaymentHistory.updater_user_id
             WHERE TaxPaymentHistory.year = ?
          ORDER BY TaxPaymentHistory.when_ DESC
             LIMIT 10""", (y, )).fetchall()
        stats.append(PaymentStats(y, payments, histories))

    return stats


def insert_for_new_year():
    pass


def switch_payment(year, season, user_id):
    # Tax テーブルを更新
    paid = g.db.execute("""
        SELECT COUNT(*)
          FROM Tax
         WHERE year = ?
           AND season = ?
           AND user_id = ?""", (year, season, user_id)).fetchone()[0]
    if paid:
        g.db.execute("""
            DELETE FROM Tax
             WHERE year = ?
               AND season = ?
               AND user_id = ?""", (year, season, user_id))
    else:
        g.db.execute("""
            INSERT INTO Tax (user_id, year, season) VALUES (?, ?, ?)""",
            (user_id, year, season))
    payment = not paid

    # 履歴に保存
    action = 1 if payment else 2
    g.db.execute("""
        INSERT INTO TaxPaymentHistory (
                user_id, year, season, action, updater_user_id)
             VALUES (?, ?, ?, ?, ?)""",
             (user_id, year, season, action, g.user.id))
    new_history = g.db.execute("""
        SELECT TaxPaymentHistory.when_ AS when_,
               User.name AS user_name,
               Updater.name AS updater_name,
               TaxPaymentHistory.season AS season,
               TaxPaymentHistory.action AS action
          FROM TaxPaymentHistory
               INNER JOIN User ON
                 User.id = TaxPaymentHistory.user_id
               INNER JOIN User AS Updater ON
                 Updater.id = TaxPaymentHistory.updater_user_id
         WHERE TaxPaymentHistory.user_id = ?
           AND TaxPaymentHistory.year = ?
           AND TaxPaymentHistory.season = ?
           AND TaxPaymentHistory.action = ?
      ORDER BY TaxPaymentHistory.when_ DESC
         LIMIT 1""", (user_id, year, season, action)).fetchone()

    g.db.commit()

    return payment, new_history


def is_paid_tax_for_current_season(user_id):
    now = datetime.now()
    year = now.year
    season = now.month
    ret = g.db.execute("""
        SELECT COUNT(user_id)
          FROM Tax
         WHERE user_id = ?
           AND year = ?
           AND season = ?""", (user_id, year, season)).fetchone()
    return ret[0] > 0


def find_histories(year, begin, count):
    return g.db.execute("""
        SELECT TaxPaymentHistory.when_ AS when_,
               User.name AS user_name,
               Updater.name AS updater_name,
               TaxPaymentHistory.season AS season,
               TaxPaymentHistory.action AS action
          FROM TaxPaymentHistory
               INNER JOIN User ON
                 User.id = TaxPaymentHistory.user_id
               INNER JOIN User AS Updater ON
                 Updater.id = TaxPaymentHistory.updater_user_id
         WHERE TaxPaymentHistory.year = ?
      ORDER BY TaxPaymentHistory.when_ DESC
         LIMIT ?, ?""", (year, begin, count)).fetchall()
