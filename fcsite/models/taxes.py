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
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.paid_seasons = []

    def pay(self, year, season):
        self.paid_seasons.append((year, season))

    def is_paid(self, year, season):
        return (year, season) in self.paid_seasons

    def status_summary(self, year):
        now = datetime.now()
        month = now.month if now.year == year else 12
        last = datetime(year, month, 1)
        for m in seasons():
            if datetime(year, m, 1) > last:
                break
            if not self.is_paid(year, m):
                return False
        return True

    def statuses_of_year(self, year):
        return [(m, self.is_paid(year, m)) for m in seasons()]


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


def find_by_year(year):
    taxes = g.db.execute("""
        SELECT User.name,
               User.id AS user_id,
               Tax.year,
               Tax.season
          FROM User
               LEFT OUTER JOIN (SELECT * FROM Tax WHERE year = ?) AS Tax ON
                 User.id = Tax.user_id
         WHERE User.id <> -1
      ORDER BY User.sex, User.id""", (year, )).fetchall()

    payments = []
    id_and_name = lambda x: (x['user_id'], x['name'])
    for (user_id, name), paid_seasons in groupby(taxes, id_and_name):
        p = Payment(user_id, name)
        for paid_season in paid_seasons:
            p.pay(year, paid_season['season'])
        payments.append(p)

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
         LIMIT 10""", (year, )).fetchall()
    return PaymentStats(year, payments, histories)


def update_payments(year, user_id, new_paid):
    records = g.db.execute("""
        SELECT Tax.season
          FROM Tax
         WHERE Tax.year = ?
           AND Tax.user_id = ?""", (year, user_id)).fetchall()
    curr_paid = [r['season'] for r in records]

    insertions = [s for s in new_paid if s not in curr_paid]
    deletions = [s for s in curr_paid if s not in new_paid]

    # Tax テーブルの更新
    g.db.executemany("""
        INSERT INTO Tax (year, user_id, season) VALUES (?, ?, ?)""",
        [(year, user_id, s) for s in insertions])
    g.db.executemany("""
        DELETE FROM Tax
         WHERE year = ?
           AND user_id = ?
           AND season = ?""", [(year, user_id, s) for s in deletions])

    # TaxPaymentHistory テーブルの更新
    def insert_payment_histories(action, seasons):
        updater = g.user.id
        g.db.executemany("""
            INSERT INTO TaxPaymentHistory (
                    year, user_id, season, action, updater_user_id)
                 VALUES (?, ?, ?, ?, ?)""",
            [(year, user_id, s, action, updater) for s in seasons])

    insert_payment_histories(1, insertions)
    insert_payment_histories(2, deletions)
    g.db.commit()


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
