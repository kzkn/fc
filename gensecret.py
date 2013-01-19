import os
with open('secret.py', 'w') as f:
    print >>f, "secrets={'SECRET_KEY':" + repr(os.urandom(24)) + "}"
