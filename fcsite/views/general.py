# -*- coding: utf-8 -*-

import re
import json
from datetime import datetime
from flask import render_template, session, redirect, request, \
    url_for, g, abort
from fcsite import check_forced_registration_blueprint, app
from fcsite.models import notices
from fcsite.models import joins
from fcsite.models import users
from fcsite.models import rules
from fcsite.models import taxes
from fcsite.models import reports
from fcsite.utils import error_message, info_message, check_required, \
        check_in, do_validate, format_date, format_season_action
from fcsite.utils import sanitize_html, pagination, sanitize_markdown
from fcsite.auth import do_login, requires_login, requires_permission

ignores = [(['POST'], re.compile('/login')),
           (['GET'], re.compile('/logout'))]
mod = check_forced_registration_blueprint('general', __name__,
        ignore_patterns=ignores)


def validate_join_request():
    validators = {}
    validators['name'] = [check_required]
    validators['home'] = [check_required]
    validators['email'] = [check_required]
    validators['sex'] = [check_required, check_in(u'男性', u'女性')]
    validators['age'] = [check_required, check_in('18-20', '21-23', '24-26',
        '27-29', '30-32', '33-35', '36-38', '39-41', '42-')]
    validators['car'] = [check_required, check_in(u'あり', u'なし')]
    validators['has_racket'] = [check_required, check_in(u'あり', u'なし')]
    validators['holiday'] = [check_required, check_in(u'土日', u'日',
        u'不定期')]
    validators['experience'] = [check_required, check_in(u'初心者',
        u'初級', u'中級', u'上級', u'神、いわゆるゴッド')]
    validators['comment'] = [check_required]
    do_validate(request.form, validators)


def validate_report():
    validators = {}
    validators['title'] = [check_required]
    validators['description'] = [check_required]
    validators['body'] = [check_required]
    do_validate(request.form, validators)


@mod.route('/')
def index():
    info_msgs = []
    if g.user:
        ns = notices.find_showing()
        info_msgs = info_msgs + [notice_to_message(n) for n in ns]
    return render_template('index.html', info_msgs=info_msgs)


def notice_to_message(notice):
    return u'%s:%s' % (notice['title'], notice['body'])


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    btn = request.form['btn']
    if btn == 'login':
        passwd = request.form['password']
        if do_login(passwd):
            return redirect(url_for('general.index'))
        else:
            error_message(u'ログインできません。パスワードが間違っています。')
            return redirect(url_for('general.login'))
    else:
        abort(400)


@mod.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('general.index'))


@mod.route('/introduction')
def introduction():
    return render_template('introduction.html')


@mod.route('/reports')
@mod.route('/reports/<int:page>')
def report_list(page=1):
    modelpage = max(0, page - 1)
    rs = reports.find_reports_on_page(modelpage)
    pages = reports.count_pages()
    if page > pages:
        abort(404)
    begin, end = pagination(page, pages)
    recent_reports = reports.recent()
    return render_template('reports.html', page=page, pages=pages,
            reports=rs, begin=begin, end=end,
            recent_reports=recent_reports)


@mod.route('/report/<int:id>')
def report(id):
    r = reports.find_by_id(id)
    if not r:
        abort(404)
    recent_reports = reports.recent()
    return render_template('report.html', report=r,
            recent_reports=recent_reports)


@mod.route('/report/edit', methods=['GET', 'POST'])
@mod.route('/report/edit/<int:id>', methods=['GET', 'POST'])
@requires_login
def edit_report(id=None):
    r = reports.find_by_id(id) if id is not None else None
    if r and not r.can_edit_by(g.user):
        abort(403)

    if request.method == 'GET':
        return render_template('report_edit.html', report=r)

    # post
    action = request.form['action']
    if action == u'投稿':
        return post_report(r)
    elif action == u'削除':
        return delete_report(r)
    abort(400)


def post_report(r):
    try:
        validate_report()
    except ValueError, e:
        return render_template('report_edit.html', errors=e.errors, report=r)

    title = request.form['title']
    feature_image_url = request.form.get('feature_image_url', '')
    description = request.form['description']
    body = request.form['body']
    if r:
        r.update(title, feature_image_url, description, body)
        newid = r.id
    else:
        newid = reports.insert(title, feature_image_url, description, body)
    return redirect(url_for('general.report', id=newid))


def delete_report(r):
    r.delete()
    info_message(message=u'活動記録を削除しました。')
    return redirect(url_for('general.report_list'))


@mod.route('/report/preview', methods=['POST'])
@mod.route('/report/preview/<int:id>', methods=['POST'])
@requires_login
def preview_report(id=None):
    title = request.form.get('title', '')
    feature_image_url = request.form.get('feature_image_url', '')
    description = request.form.get('description', '')
    body = request.form.get('body', '')

    inputs = dict(id=id, title=title, feature_image_url=feature_image_url,
            description=description, body=body)
    preview_report = dict(
            title=title,
            feature_image_url=feature_image_url,
            description=sanitize_markdown(description),
            body=sanitize_markdown(body))
    return render_template('general.edit_report', report=inputs,
            preview=preview_report)


@mod.route('/gallery')
def gallery():
    return render_template('gallery.html')


@mod.route('/gallery/<int:albumId>')
def album(albumId):
    return render_template('album.html', albumId=albumId)


@mod.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')

    try:
        validate_join_request()
    except ValueError, e:
        return render_template('join.html', errors=e.errors)

    name = request.form['name']
    home = request.form['home']
    email = request.form['email']
    sex = request.form['sex']
    age = request.form['age']
    car = request.form['car']
    has_racket = request.form['has_racket']
    holiday = request.form['holiday']
    experience = request.form['experience']
    comment = request.form['comment']
    joins.insert(name, home, email, sex, age, car, has_racket, holiday,
            experience, comment)

    info_message(message=u'後日、サークルのものから折り返し連絡します。',
            title=u'応募ありがとうございます！')
    return redirect(url_for('general.index'))


@mod.route('/new_join_requests')
@requires_login
def show_join_reqs():
    joinreqs = joins.find_not_handled()
    return render_template('joinreqs_new.html', joinreqs=joinreqs)


@mod.route('/handle_joinreq/<int:id>')
@requires_permission(users.PERM_ADMIN_MEMBER)
def handle_joinreq(id):
    joins.handle_join_request(id)
    info_message(message=u'応募者対応、ありがとう！', title=u'応募者に対応しました')
    return redirect(url_for('general.show_join_reqs'))


@mod.route('/rule')
@requires_login
def rule():
    rs = rules.find_all()
    return render_template('rule.html', rules=rs)


@mod.route('/delete_rule/<int:id>')
@requires_permission(users.PERM_ADMIN_GOD)
def delete_rule(id):
    rules.delete(id)
    info_message(message=u'規約を削除しましたね。通知とかしたほうがいいんじゃないすか？',
            title=u'規約を削除しました')
    return redirect(url_for('general.rule'))


@mod.route('/add_rule', methods=['POST'])
@requires_permission(users.PERM_ADMIN_GOD)
def add_rule():
    body = sanitize_html(request.form['body'])
    rules.insert(body)
    info_message(message=u'規約を追加しましたね。通知とかしたほうがいいんじゃないすか？',
            title=u'規約を追加しました')
    return redirect(url_for('general.rule'))


@mod.route('/tax_list')
@mod.route('/tax_list/<int:year>')
@requires_login
def tax_list(year=None):
    now = datetime.now()
    if not year:
        year = now.year
    if year < taxes.MINIMUM_YEAR or year > now.year:
        abort(404)
    stat = taxes.find_by_year(year)
    return render_template('tax.html',
            stat=stat, current_year=year, years=reversed(taxes.years()))


@mod.route('/update_payments/<int:year>/<int:user_id>', methods=['POST'])
@requires_permission(users.PERM_ADMIN_GOD)
def update_payments(year, user_id):
    new_paid_seasons = [int(x) for x in request.form.getlist('seasons')]
    taxes.update_payments(year, user_id, new_paid_seasons)
    return redirect(url_for('general.tax_list'))


def history_to_dict(history):
    when = format_date(history['when_'])
    name = history['user_name']
    updater = history['updater_name']
    action = format_season_action(history['season'], history['action'])
    return {'when': when,
            'name': name,
            'updater': updater,
            'action': action}


TAX_HISTORIES_STEP = 5


@mod.route('/tax_histories/<int:year>/<int:page>')
@requires_login
def tax_histories(year, page):
    begin = (page - 1) * TAX_HISTORIES_STEP
    hists = taxes.find_histories(year, begin, TAX_HISTORIES_STEP)
    return json.dumps([history_to_dict(h) for h in hists])
