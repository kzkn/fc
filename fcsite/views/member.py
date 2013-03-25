# -*- coding: utf-8 -*-

from flask import render_template, request, g, redirect, url_for
from flask.ext.wtf import Form
from flask.ext.wtf.html5 import DateField
from wtforms import TextField, TextAreaField, SelectField
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


@mod.route('/')
@mod.route('/<int:id>')
def member(id=None):
    males, females = users.find_group_by_sex()
    selected = users.find_by_id(id) if id is not None else None

    if not selected:
        if males:
            selected = males[0]
        elif females:
            selected = females[0]

    return render_template('member.html', males=males, females=females,
                           selected_user=selected)


class ProfileForm(Form):
    name = TextField(u'名前')
    password = TextField(u'パスワード')
    sex = SelectField(u'性別', choices=[('male', u'男性'), ('female', u'女性')])
    email = TextField(u'メールアドレス')
    birthday = DateField(u'生年月日')
    home = TextField(u'住まい')
    car = TextField(u'車')
    comment = TextAreaField(u'一言')

    @classmethod
    def new(cls):
        form = cls()
        form.sex.data = 'male' if g.user.is_male() else form.sex.data
        form.sex.data = 'female' if g.user.is_female() else form.sex.data
        form.comment.data = g.user.comment
        return form


@mod.route('/profile', methods=['GET', 'POST'])
@requires_login
def profile():
    form = ProfileForm.new()
    if form.validate_on_submit():
        users.update_profile(g.user.id, request.form)  # TODO request.form やめたい
        return redirect(url_for('member.profile'))

    return render_template('profile.html', form=form)
