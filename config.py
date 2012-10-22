# -*- coding: utf-8 -*-

import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

SECRET_FILE = os.path.join(_basedir, 'secret.py')
DATABASE_URI = os.path.join(_basedir, 'fc.db')
UPDATE_SCRIPT = os.path.join(_basedir, 'update.sh')
BBS_PER_PAGE = 20
REPORTS_PER_PAGE = 10

del os
