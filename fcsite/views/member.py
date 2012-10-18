# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, g, redirect, url_for
from fcsite.models import users
from fcsite.auth import requires_login
from fcsite.utils import do_validate, check_date

mod = Blueprint('member', __name__, url_prefix='/member')


def validate_profile():
    validators = {}
    validators['birthday'] = [check_date]
    do_validate(request.form, validators)


@mod.route('/')
@mod.route('/<int:id>')
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


@mod.route('/profile', methods=['GET', 'POST'])
@requires_login
def profile():
    if request.method == 'GET':
        return render_template('profile.html')
    try:
        validate_profile()
    except ValueError, e:
        return render_template('profile.html', errors=e.errors)

    users.update_profile(g.user.id, request.form)
    return redirect(url_for('member.profile'))
