# -*- coding: utf-8 -*-

from nose.tools import ok_, with_setup

from fcsite.models import set_user, bbs, users
from tests.models import getdb


def setup_module(module):
    getdb().execute("DELETE FROM User")
    getdb().execute("DELETE FROM BBS")


def _setup_testdata(count):
    def impl():
        users.insert("foo",  "passwd1", 1, 0x0)
        set_user(users.find_by_id(1))
        for i in range(count):
            bbs.post(u"あいうえお" + str(i))
    return impl


def teardown_testdata():
    users.delete_by_id(1)
    getdb().execute("DELETE FROM BBS")


@with_setup(_setup_testdata(5), teardown_testdata)
def test_count_posts():
    assert bbs.count_posts() == 5


@with_setup(_setup_testdata(0), teardown_testdata)
def test_count_posts0():
    assert bbs.count_posts() == 0
