# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from flask import g


def find_all():
    taxes = g.db.execute("""
        SELECT User.name,
               Tax.user_id,
               Tax.year,
               Tax.paid_first,
               Tax.paid_second
          FROM User
               INNER JOIN Tax ON
                 User.id = Tax.user_id
      ORDER BY Tax.year DESC, User.sex, User.id""").fetchall()
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
      ORDER BY TaxPaymentHistory.year DESC,
               TaxPaymentHistory.when_ DESC
         LIMIT 10""").fetchall()

    payments_by_year = OrderedDict()
    for year, payments in groupby(taxes, lambda e: e['year']):
        payments_by_year[year] = [list(payments), []]
    for year, hists in groupby(histories, lambda e: e['year']):
        payments_by_year[year][1] = list(hists)

    return payments_by_year


def insert_for_new_year():
    year = datetime.now().year
    max_stored_year = g.db.execute("""
        SELECT MAX(year) FROM Tax""").fetchone()[0]
    if not max_stored_year or year > max_stored_year:
        do_insert_records_for_year(year)


def do_insert_records_for_year(year):
    # 特殊ユーザ (id=-1) は支払い状況を表示しないよう insert の対象外とする
    g.db.execute("""
        INSERT INTO Tax (user_id, year, paid_first, paid_second)
             SELECT id, ?, 0, 0 FROM User WHERE id <> -1""", (year, ))
    g.db.commit()


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
    season = 'first' if now.month <= 6 else 'second'
    ret = g.db.execute("""
        SELECT COUNT(user_id)
          FROM Tax
         WHERE user_id = ?
           AND year = ?
           AND paid_%s = 1""" % season, (user_id, year)).fetchone()
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
