# -*- coding: utf-8 -*-

from flask import render_template, request, g, redirect, url_for
from fcsite import check_forced_registration_blueprint
from fcsite.models import users
from fcsite.auth import requires_login
from fcsite.utils import do_validate, check_date

mod = check_forced_registration_blueprint('member', __name__,
        url_prefix='/member')


def validate_profile():
    validators = {}
    validators['birthday'] = [check_date]
    do_validate(request.form, validators)


@mod.route('/list')
def list():
    males, females = users.find_group_by_sex()
    return render_template('member_list.html', males=males, females=females)


@mod.route('/stats')
@requires_login
def stats():
    return render_template('member_stats.html', members=users.find_all())


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
