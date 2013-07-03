# -*- coding: utf-8 -*-

from nose.tools import ok_, with_setup

from fcsite.models import users
from tests.models import getdb


def setup_module(module):
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


@with_setup(setup_testdata, teardown_testdata)
def test_find_group_by_sex():
    males, females = users.find_group_by_sex()

    assert len(males) == 3
    assert males[0].name == "foo"
    assert males[1].name == "bar"
    assert males[2].name == "quux"

    assert len(females) == 2
    assert females[0].name == "baz"
    assert females[1].name == "qux"


def test_get_or_gen_password():
    f1 = {"password": "1234"}
    p1 = users.get_or_gen_password(f1)
    assert p1 == "1234"

    f2 = {"password": ""}
    p2 = users.get_or_gen_password(f2)
    assert not users.find_by_password(p2)


def test_sex_atoi():
    s1 = users.sex_atoi(u"男性")
    assert s1 == users.SEX_MALE

    s2 = users.sex_atoi(u"女性")
    assert s2 == users.SEX_FEMALE

    s3 = users.sex_atoi(None)
    assert s3 == users.SEX_FEMALE

    s4 = users.sex_atoi("hoge")
    assert s4 == users.SEX_FEMALE


def test_permission_atoi():
    class DummyForm(object):
        def __init__(self, items):
            self.items = items

        def getlist(self, key):
            return self.items

    f1 = DummyForm(["schedule"])
    p1 = users.permission_atoi(f1) & ~users.PERM_ADMIN
    assert p1 & users.PERM_ADMIN_SCHEDULE
    assert not (p1 & users.PERM_ADMIN_MEMBER)
    assert not (p1 & users.PERM_ADMIN_NOTICE)

    f2 = DummyForm(["member"])
    p2 = users.permission_atoi(f2) & ~users.PERM_ADMIN
    assert not (p2 & users.PERM_ADMIN_SCHEDULE)
    assert p2 & users.PERM_ADMIN_MEMBER
    assert not (p2 & users.PERM_ADMIN_NOTICE)

    f3 = DummyForm(["notice"])
    p3 = users.permission_atoi(f3) & ~users.PERM_ADMIN
    assert not (p3 & users.PERM_ADMIN_SCHEDULE)
    assert not (p3 & users.PERM_ADMIN_MEMBER)
    assert p3 & users.PERM_ADMIN_NOTICE

    f4 = DummyForm(["schedule", "member"])
    p4 = users.permission_atoi(f4) & ~users.PERM_ADMIN
    assert p4 & users.PERM_ADMIN_SCHEDULE
    assert p4 & users.PERM_ADMIN_MEMBER
    assert not (p4 & users.PERM_ADMIN_NOTICE)

    f5 = DummyForm(["notice", "member"])
    p5 = users.permission_atoi(f5) & ~users.PERM_ADMIN
    assert not (p5 & users.PERM_ADMIN_SCHEDULE)
    assert p5 & users.PERM_ADMIN_MEMBER
    assert p5 & users.PERM_ADMIN_NOTICE

    f6 = DummyForm(["notice", "schedule", "member"])
    p6 = users.permission_atoi(f6) & ~users.PERM_ADMIN
    assert p6 & users.PERM_ADMIN_SCHEDULE
    assert p6 & users.PERM_ADMIN_MEMBER
    assert p6 & users.PERM_ADMIN_NOTICE

    f7 = DummyForm([])
    p7 = users.permission_atoi(f7) & ~users.PERM_ADMIN
    assert not (p7 & users.PERM_ADMIN_SCHEDULE)
    assert not (p7 & users.PERM_ADMIN_MEMBER)
    assert not (p7 & users.PERM_ADMIN_NOTICE)
