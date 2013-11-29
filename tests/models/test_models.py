# -*- coding: utf-8 -*-

from nose.tools import ok_, with_setup

from fcsite import models


def test_clauses():
    assert models.clauses([1,2,3]) == '(?,?,?)'
    assert models.clauses([]) == '()'
    assert models.clauses([1]) == '(?)'
