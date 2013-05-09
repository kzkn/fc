# -*- coding: utf-8 -*-

from nose.tools import ok_, raises
from fcsite import utils


def _(check, arg):
    try:
        return check(arg)
    except ValueError:
        return None


def test_check_date():
    ok_(_(utils.check_date, "2000-1-1"))
    ok_(_(utils.check_date, "2000-01-1"))
    ok_(_(utils.check_date, "2000-1-01"))
    ok_(_(utils.check_date, "2000-01-01"))
    ok_(_(utils.check_date, "2000-12-31"))
    ok_(not _(utils.check_date, "2000-12-32"))
    ok_(not _(utils.check_date, "2000-1-0"))
    ok_(not _(utils.check_date, "2000-0-1"))
    ok_(not _(utils.check_date, "2000-1-"))
    ok_(not _(utils.check_date, "2000--0"))
    ok_(not _(utils.check_date, ""))


def test_check_time():
    ok_(_(utils.check_time, "0:0"))
    ok_(_(utils.check_time, "00:00"))
    ok_(_(utils.check_time, "23:59"))
    ok_(not _(utils.check_time, "24:00"))
    ok_(not _(utils.check_time, "0:60"))
    ok_(not _(utils.check_time, ""))
    ok_(not _(utils.check_time, "0:"))
    ok_(not _(utils.check_time, ":0"))
    ok_(not _(utils.check_time, "0:0:0"))
