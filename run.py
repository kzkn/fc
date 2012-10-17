#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fcsite
import evolutions
from fcsite import database

if __name__ == '__main__':
    app = fcsite.app
    evolutions.apply_script(app.config['DATABASE_URI'], 'schema')
    database.initialize()
    app.run('0.0.0.0')
