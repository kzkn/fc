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

    payments_by_year = OrderedDict()
    for year, payments in groupby(taxes, lambda e: e['year']):
        payments_by_year[year] = list(payments)
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


def switch_payment(year, is_first_season, user_id):
    column = 'paid_first' if is_first_season else 'paid_second'
    g.db.execute("""
        UPDATE Tax
           SET %s = CASE WHEN %s = 1 THEN 0
                         ELSE 1
                    END
         WHERE year = ?
           AND user_id = ?""" % (column, column), (year, user_id))
    g.db.commit()

    return g.db.execute("""
        SELECT %s
          FROM Tax
         WHERE year = ?
           AND user_id = ?""" % column, (year, user_id)).fetchone()[0]
