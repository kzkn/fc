# -*- coding: utf-8 -*-

from nose.tools import ok_, with_setup

from fcsite.models import users
from tests.models import getdb


def setup_module(module):
    users.set_db(getdb())
    getdb().execute("DELETE FROM User")


def setup_testdata():
    users.insert("foo",  "passwd1", 1, 0x0)
    users.insert("bar",  "passwd2", 1, 0x1)
    users.insert("baz",  "passwd3", 2, 0x3)
    users.insert("qux",  "passwd4", 2, 0x7)
    users.insert("quux", "passwd5", 1, 0xf)


def teardown_testdata():
    users.delete_by_id(1)
    users.delete_by_id(2)
    users.delete_by_id(3)
    users.delete_by_id(4)
    users.delete_by_id(5)


@with_setup(setup_testdata, teardown_testdata)
def test_find_by_id():
    u1 = users.find_by_id(1)
    assert u1.name == "foo"
    u2 = users.find_by_id(2)
    assert u2.name == "bar"
    u3 = users.find_by_id(3)
    assert u3.name == "baz"
    u4 = users.find_by_id(4)
    assert u4.name == "qux"
    u5 = users.find_by_id(5)
    assert u5.name == "quux"
    u6 = users.find_by_id(6)
    assert not u6


@with_setup(setup_testdata, teardown_testdata)
def test_sex():
    u1 = users.find_by_id(1)
    assert u1.is_male()
    assert not u1.is_female()

    u3 = users.find_by_id(3)
    assert not u3.is_male()
    assert u3.is_female()


@with_setup(setup_testdata, teardown_testdata)
def test_permission():
    u1 = users.find_by_id(1)
    assert not u1.is_admin()
    assert not u1.is_schedule_admin()
    assert not u1.is_member_admin()
    assert not u1.is_notice_admin()
    assert not u1.is_god()

    u2 = users.find_by_id(2)
    assert u2.is_admin()
    assert not u2.is_schedule_admin()
    assert not u2.is_member_admin()
    assert not u2.is_notice_admin()
    assert not u2.is_god()

    u3 = users.find_by_id(3)
    assert u3.is_admin()
    assert u3.is_schedule_admin()
    assert not u3.is_member_admin()
    assert not u3.is_notice_admin()
    assert not u3.is_god()

    u4 = users.find_by_id(4)
    assert u4.is_admin()
    assert u4.is_schedule_admin()
    assert u4.is_member_admin()
    assert not u4.is_notice_admin()
    assert not u4.is_god()

    u5 = users.find_by_id(5)
    assert u5.is_admin()
    assert u5.is_schedule_admin()
    assert u5.is_member_admin()
    assert u5.is_notice_admin()
    assert u5.is_god()
