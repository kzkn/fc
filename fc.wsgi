activate_this = '/var/www/env/flask/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/var/www/html/newfc')

from fcsite import app as application
from fcsite import database

import os
import evolutions
evolutions.apply_script(
        application.config['DATABASE_URI'],
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'schema'))
database.initialize()
