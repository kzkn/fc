import os
with open('secret.py', 'w') as f:
    print >>f, "secrets={"
    print >>f, "  'SECRET_KEY':" + repr(os.urandom(24)) + ","
    print >>f, "  'ADMIN_EMAIL':'foo@example.com'"
    print >>f, "}"
