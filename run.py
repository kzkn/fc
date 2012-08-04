#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fcsite
import fcsite.database as database

if __name__ == '__main__':
    app = fcsite.app
    if app.config['DEBUG']:
        database.init_db()
        database.insert_test_data()
    app.run('0.0.0.0')
