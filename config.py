# -*- coding: utf-8 -*-

import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

SECRET_KEY = 'foo_bar-baz'
DATABASE_URI = os.path.join(_basedir, 'fc.db')
BBS_PER_PAGE = 20

del os
