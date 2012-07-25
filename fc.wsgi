activate_this = '/var/www/env/flask'
execfile(activate_this, dir(__file__=activate_this))

import sys
sys.path.insert(0, '/var/www/html/newfc')

from fc import app
app.run(debug=True)
