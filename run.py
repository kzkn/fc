#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fcsite


if __name__ == '__main__':
    fcsite.init_db()
    fcsite.insert_test_data()
    fcsite.app.run('0.0.0.0', debug=True)
