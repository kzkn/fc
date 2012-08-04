#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fcsite

if __name__ == '__main__':
    app = fcsite.app
    if app.config['DEBUG']:
        fcsite.init_db()
        fcsite.insert_test_data()
    app.run('0.0.0.0')
