# -*- coding: utf-8 -*-

from flask import g
from itertools import groupby
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


def find_all():
    taxes = g.db.execute("""
        SELECT User.name,
               Tax.year,
               Tax.paid_first,
               Tax.paid_second
          FROM User
               INNER JOIN Tax ON
                 User.id = Tax.user_id
      ORDER BY Tax.year DESC, User.name""").fetchall()

    payments_by_year = OrderedDict()
    for year, payments in groupby(taxes, lambda e: e['year']):
        payments_by_year[year] = list(payments)
    return payments_by_year
