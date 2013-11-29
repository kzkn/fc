# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from nose.tools import with_setup

from fcsite.models import set_user, schedules, users, entries
from tests.models import getdb


def setup_module(module):
    getdb().execute("DELETE FROM User")
    getdb().execute("DELETE FROM Schedule")
    getdb().execute("DELETE FROM GuestEntry")


def _setup_testdata(type):
    def impl():
        users.insert("god",  "root", 1, 0xf)
        users.insert("normal1",  "passwd1", 1, 0x0)
        users.insert("normal2",  "passwd2", 1, 0x0)
        users.insert("normal3",  "passwd3", 1, 0x3)
        now = datetime.now()
        schedules.insert(type, now + timedelta(days=1), "hoge")
        schedules.insert(type, now - timedelta(days=1), "fuga")
    return impl


def teardown_testdata():
    getdb().execute("DELETE FROM User")
    getdb().execute("DELETE FROM Schedule")
    getdb().execute("DELETE FROM GuestEntry")


@with_setup(_setup_testdata(schedules.TYPE_PRACTICE), teardown_testdata)
def test_has_permission_to_delete_guest():
    set_user(users.find_by_id(2))  # invited by normal1
    entries.do_guest_entry(1, "name", "comment")
    # check...
    set_user(users.find_by_id(1))  # god
    assert entries.has_permission_to_delete_guest(1)
    set_user(users.find_by_id(2))  # normal1
    assert entries.has_permission_to_delete_guest(1)
    set_user(users.find_by_id(3))  # normal2
    assert not entries.has_permission_to_delete_guest(1)
    set_user(users.find_by_id(4))  # normal3
    assert not entries.has_permission_to_delete_guest(1)
