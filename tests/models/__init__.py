import sqlite3
import evolutions


def _utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    if isinstance(string, str):
        return unicode(string, 'utf-8').encode('utf-8')
    return _utf8(str(string))


_db = None


def setup_package(pkg):
    global _db
    _db = sqlite3.connect(":memory:")
    _db.row_factory = sqlite3.Row
    _db.text_factory = _utf8
    evolutions.apply_script_for_unittest(_db, 'schema')


def teardown_package(pkg):
    global _db
    _db.close()


def getdb():
    global _db
    return _db
