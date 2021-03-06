# -*- coding: utf-8 -*-

import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

SECRET_FILE = os.path.join(_basedir, 'secret.py')
DATABASE_URI = os.path.join(_basedir, 'fc.db')
BBS_PER_PAGE = 20
REPORTS_PER_PAGE = 10
SEND_FILE_MAX_AGE_DEFAULT = 0

del os
