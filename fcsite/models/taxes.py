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
               Tax.year,
               Tax.paid_first,
               Tax.paid_second
          FROM User
               INNER JOIN Tax ON
                 User.id = Tax.user_id
      ORDER BY Tax.year DESC, User.sex, User.name""").fetchall()

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
    g.db.execute("""
        INSERT INTO Tax (user_id, year, paid_first, paid_second)
             SELECT id, ?, 0, 0 FROM User""", (year, ))
    g.db.commit()
