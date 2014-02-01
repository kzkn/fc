# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from fcsite import models
from fcsite.models import schedules as scheds


class Rate(object):
    def __init__(self, count, allcount):
        self.count = count
        self.allcount = allcount

    def __cmp__(self, other):
        return cmp(float(self), float(other))

    def __float__(self):
        if self.allcount == 0:
            return 0.0
        else:
            return self.count / float(self.allcount)

    def percentage(self):
        return "%.2f %%" % (100 * float(self))

    def counts(self):
        return "%d / %d" % (self.count, self.allcount)


def get_practice_entry_rate_of_year(user, year):
    dtmin = max(user.joined, datetime(year, 1, 1)) - timedelta(seconds=1)
    dtmax = datetime(year + 1, 1, 1)
    cur = models.db().execute("""
        SELECT (SELECT COUNT(*)
                  FROM Schedule
                 WHERE when_ > ?
                   AND when_ < ?
                   AND type = ?) AS _all,
               (SELECT COUNT(*)
                  FROM Schedule
                       INNER JOIN Entry ON
                         Schedule.id = Entry.schedule_id
                 WHERE Schedule.when_ > ?
                   AND Schedule.when_ < ?
                   AND Schedule.type = ?
                   AND Entry.user_id = ?
                   AND Entry.is_entry) AS entried""",
        (dtmin, dtmax, scheds.TYPE_PRACTICE,
         dtmin, dtmax, scheds.TYPE_PRACTICE, user.id))

    r = cur.fetchone()
    return Rate(r['entried'], r['_all'])
