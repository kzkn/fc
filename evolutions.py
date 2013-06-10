# -*- coding: utf-8 -*-

import os
import re
import sqlite3
import codecs
from datetime import datetime
from hashlib import sha1
from contextlib import closing

EVOLUTIONS_DIR = './evolutions'
CREATE_EVOLUTIONS_TABLE = """
   create table evolutions (
      id int primary key,
      hash varchar(255) not null,
      applied_at timestamp not null,
      apply_script clob,
      revert_script clob,
      state varchar(255),
      last_problem clob
)"""



def utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    if isinstance(string, str):
        return unicode(string, 'utf-8').encode('utf-8')
    return utf8(str(string))


def new_connection(db_uri):
    conn = sqlite3.connect(db_uri)
    conn.row_factory = sqlite3.Row
    conn.text_factory = utf8
    return conn


def exists_directory(path):
    return os.path.isdir(path) and os.path.exists(path)


def read_file_content(path):
    with closing(codecs.open(path, encoding='utf-8')) as f:
        return utf8(f.read())


class Evolution(object):
    def __init__(self, revision, sql_up, sql_down, apply_up):
        self.revision = revision
        self.sql_up = sql_up
        self.sql_down = sql_down
        self.apply_up = apply_up
        self.hash = sha1('%s%s' % (sql_up, sql_down)).hexdigest()

    def __eq__(self, other):
        return self.revision == other.revision

    def __lt__(self, other):
        return self.revision < other.revision

    def __hash__(self):
        return self.revision

    def sql_seqs(self):
        sql = self.sql_up if self.apply_up else self.sql_down
        return sql.split(';')


def apply_script(db_uri, evolutions_dir=EVOLUTIONS_DIR):
    with closing(new_connection(db_uri)) as conn:
        applying = -1
        try:
            for evolution in get_evolution_script(db_uri, evolutions_dir):
                applying = evolution.revision

                # insert into logs
                if (evolution.apply_up):
                    conn.execute(
                        "insert into evolutions values (?, ?, ?, ?, ?, ?, ?)",
                        (evolution.revision,
                         evolution.hash,
                         datetime.now(),
                         evolution.sql_up,
                         evolution.sql_down,
                         'applying_up',
                         ''))
                else:
                    conn.execute("""
                          update evolutions
                            set state = 'applying_down'
                          where id = ?""", (evolution.revision, ))
                conn.commit()

                # execute script
                for sql in evolution.sql_seqs():
                    if sql:
                        conn.execute(sql)

                # insert into logs (result)
                if evolution.apply_up:
                    conn.execute("""
                        update evolutions
                           set state = 'applied'
                         where id = ?""", (evolution.revision, ))
                else:
                    conn.execute(
                        "delete from evolutions where id = ?",
                        (evolution.revision, ))
                conn.commit()
        except sqlite3.Error, e:
            conn.execute(
                "update evolutions set last_problem = ? where id = ?",
                (e.message, applying))
            conn.commit()
            raise e
    return True


def dryrun_script(db_uri, evolutions_dir=EVOLUTIONS_DIR):
    for evolution in get_evolution_script(db_uri, evolutions_dir):
        # print scripts
        for sql in evolution.sql_seqs():
            if sql:
                print sql


def get_evolution_script(db_uri, evolutions_dir):
    app = list_app_evolutions(evolutions_dir)
    db = list_db_evolutions(db_uri)
    ups = []
    downs = []

    # apply non conflicting evolutions (ups and downs)
    while db[-1].revision != app[-1].revision:
        if db[-1].revision > app[-1].revision:
            downs.append(db.pop())
        else:
            ups.append(app.pop())

    # revert conflicting to fork node
    while db[-1].revision == app[-1].revision and db[-1].hash != app[-1].hash:
        downs.append(db.pop())
        ups.append(app.pop())

    # Ups need to be applied earlier first
    ups.sort()

    return downs + ups


def list_app_evolutions(evolutions_dir):
    evolutions = []
    evolutions.append(Evolution(0, '', '', True))
    if not exists_directory(evolutions_dir):
        return evolutions
    for fname in os.listdir(evolutions_dir):
        m = re.match(r'^([0-9]+)[.]sql$', fname)
        if not m:
            continue
        revision = int(m.group(1))
        sql = read_file_content(os.path.join(evolutions_dir, fname))
        sql_up = []
        sql_down = []
        current = []
        for line in [s.strip() for s in sql.split('\n')]:
            if re.match(r'#.*[!]Ups', line):
                current = sql_up
            elif re.match(r'#.*[!]Downs', line):
                current = sql_down
            elif line.startswith('#'):
                pass  # skip
            else:
                current.append(line)
        e = Evolution(revision, '\n'.join(sql_up), '\n'.join(sql_down), True)
        evolutions.append(e)
    evolutions.sort()
    return evolutions


def list_db_evolutions(db_uri):
    evolutions = []
    evolutions.append(Evolution(0, '', '', False))
    with closing(new_connection(db_uri)) as conn:
        table_exists = conn.execute("""
            select count(*) from sqlite_master
             where type = 'table' and name = 'evolutions'""")
        if table_exists.fetchone()[0]:
            cur = conn.execute(
                "select id, apply_script, revert_script from evolutions")
            for r in cur.fetchall():
                e = Evolution(r['id'],
                              utf8(r['apply_script']),
                              utf8(r['revert_script']),
                              False)
                evolutions.append(e)
        else:
            conn.execute(CREATE_EVOLUTIONS_TABLE)
    evolutions.sort()
    return evolutions


def apply_script_for_unittest(db, evolutions_dir=EVOLUTIONS_DIR):
    # create evolutions table
    db.execute(CREATE_EVOLUTIONS_TABLE)
    # apply all evolution scripts
    for evolution in list_app_evolutions(evolutions_dir):
        db.execute(
            "insert into evolutions values (?, ?, ?, ?, ?, ?, ?)",
            (evolution.revision,
             evolution.hash,
             datetime.now(),
             evolution.sql_up,
             evolution.sql_down,
             'applying_up',
             ''))

        # execute script
        for sql in evolution.sql_seqs():
            if sql:
                db.execute(sql)

        # insert into logs (result)
        db.execute("""
            update evolutions
               set state = 'applied'
             where id = ?""", (evolution.revision, ))
        db.commit()
