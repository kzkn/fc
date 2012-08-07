# -*- coding: utf-8 -*-

from flask import Blueprint, render_template
from fcsite import users

mod = Blueprint('member', __name__)


@mod.route('/member')
@mod.route('/member/<int:id>')
def member(id=None):
    males, females = users.find_group_by_sex()
    selected = users.find_by_id(id) if id else None

    if not selected:
        if males:
            selected = males[0]
        elif females:
            selected = females[0]

    return render_template('member.html', males=males, females=females,
                           selected_user=selected)
