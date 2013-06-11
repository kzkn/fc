import sqlite3
import evolutions

from fcsite import models


def setup_package(pkg):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row

    def _utf8(string):
        if isinstance(string, unicode):
            return string.encode('utf-8')
        if isinstance(string, str):
            return unicode(string, 'utf-8').encode('utf-8')
        return _utf8(str(string))

    db.text_factory = _utf8
    evolutions.apply_script_for_unittest(db, 'schema')
    models.set_db(db)


def teardown_package(pkg):
    models.db().close()
    models.set_db(None)


def getdb():
    return models.db()
