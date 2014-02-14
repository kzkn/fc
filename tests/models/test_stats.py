# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from nose.tools import ok_, with_setup

from fcsite.models import set_user, user, schedules, users, entries, stats
from tests.models import getdb


def setup_module(module):
    getdb().execute("DELETE FROM Entry")
    getdb().execute("DELETE FROM User")
    getdb().execute("DELETE FROM Schedule")


def setup_testdata():
    users.insert("foo",  "passwd1", 1, 0x0)
    u = users.find_by_id(1)
    u.joined = datetime(2011, 1, 1)
    set_user(u)

    d = datetime(2012, 1, 1)
    schedules.insert(schedules.TYPE_PRACTICE, d + timedelta(days=1), "p1")
    schedules.insert(schedules.TYPE_PRACTICE, d + timedelta(days=2), "p2")
    schedules.insert(schedules.TYPE_PRACTICE, d + timedelta(days=3), "p3")
    schedules.insert(schedules.TYPE_PRACTICE, d + timedelta(days=4), "p4")
    schedules.insert(schedules.TYPE_PRACTICE, d + timedelta(days=5), "p5")
    schedules.insert(schedules.TYPE_GAME,     d + timedelta(days=1), "g1")
    schedules.insert(schedules.TYPE_GAME,     d + timedelta(days=2), "g2")
    schedules.insert(schedules.TYPE_GAME,     d + timedelta(days=3), "g3")
    schedules.insert(schedules.TYPE_GAME,     d + timedelta(days=4), "g4")
    schedules.insert(schedules.TYPE_GAME,     d + timedelta(days=5), "g5")
    schedules.insert(schedules.TYPE_EVENT,    d + timedelta(days=1), "e1")
    schedules.insert(schedules.TYPE_EVENT,    d + timedelta(days=2), "e2")
    schedules.insert(schedules.TYPE_EVENT,    d + timedelta(days=3), "e3")
    schedules.insert(schedules.TYPE_EVENT,    d + timedelta(days=4), "e4")
    schedules.insert(schedules.TYPE_EVENT,    d + timedelta(days=5), "e5")


def teardown_testdata():
    getdb().execute("DELETE FROM Entry")
    getdb().execute("DELETE FROM User")
    getdb().execute("DELETE FROM Schedule")


@with_setup(setup_testdata, teardown_testdata)
def test_entry_rate_reflects_only_practice():
    entries.do_entry(1, "comment", True)
    entries.do_entry(2, "comment", True)
    entries.do_entry(3, "comment", True)
    entries.do_entry(4, "comment", True)
    entries.do_entry(5, "comment", True)
    # kokomade practice
    entries.do_entry(6, "comment", False)
    entries.do_entry(7, "comment", False)
    entries.do_entry(8, "comment", False)
    entries.do_entry(9, "comment", False)
    entries.do_entry(10, "comment", False)
    entries.do_entry(11, "comment", False)
    entries.do_entry(12, "comment", False)
    entries.do_entry(13, "comment", False)
    entries.do_entry(14, "comment", False)
    entries.do_entry(15, "comment", False)

    u = user()
    rate = stats.get_practice_entry_rate_of_year(u, 2012)
    assert rate.count == 5
    assert rate.allcount == 5


@with_setup(setup_testdata, teardown_testdata)
def test_entry_rate_reflects_after_joined():
    entries.do_entry(1, "comment", False)
    entries.do_entry(2, "comment", False)
    entries.do_entry(3, "comment", False)  # 2012/1/4
    entries.do_entry(4, "comment", True)
    entries.do_entry(5, "comment", True)
    # kokomade practice
    entries.do_entry(6, "comment", False)
    entries.do_entry(7, "comment", False)
    entries.do_entry(8, "comment", False)
    entries.do_entry(9, "comment", False)
    entries.do_entry(10, "comment", False)
    entries.do_entry(11, "comment", False)
    entries.do_entry(12, "comment", False)
    entries.do_entry(13, "comment", False)
    entries.do_entry(14, "comment", False)
    entries.do_entry(15, "comment", False)

    u = user()
    u.joined = datetime(2012, 1, 4)
    rate = stats.get_practice_entry_rate_of_year(u, 2012)
    assert rate.count == 2
    assert rate.allcount == 3
