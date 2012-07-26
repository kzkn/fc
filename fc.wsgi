activate_this = '/var/www/env/flask/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/var/www/html/newfc')

from fc import app as application
