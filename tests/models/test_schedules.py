# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from nose.tools import ok_, with_setup

from fcsite.models import set_user, schedules, users
from tests.models import getdb


def setup_module(module):
    getdb().execute("DELETE FROM User")
    getdb().execute("DELETE FROM Schedule")


def _setup_testdata(type):
    def impl():
        users.insert("foo",  "passwd1", 1, 0x0)
        set_user(users.find_by_id(1))
        now = datetime.now()
        schedules.insert(type, now + timedelta(days=1), "hoge")
        schedules.insert(type, now - timedelta(days=1), "fuga")
    return impl


def teardown_testdata():
    users.delete_by_id(1)
    getdb().execute("DELETE FROM Schedule")


@with_setup(_setup_testdata(schedules.TYPE_PRACTICE), teardown_testdata)
def test_find_future_schedules():
    ss = schedules.find(schedules.TYPE_PRACTICE)
    assert len(ss) == 1
    assert ss[0]['id'] == 1


@with_setup(_setup_testdata(schedules.TYPE_PRACTICE), teardown_testdata)
def test_find_past_schedules():
    ss = schedules.find_dones(schedules.TYPE_PRACTICE)
    assert len(ss) == 1
    assert ss[0]['id'] == 2
