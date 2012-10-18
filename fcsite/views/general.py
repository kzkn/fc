# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, session, redirect, request, \
    url_for, g
from fcsite.models import schedules as scheds
from fcsite.models import notices
from fcsite.models import joins
from fcsite.models import users
from fcsite.models import rules
from fcsite.models import taxes
from fcsite.utils import error_message, info_message, check_required, \
        check_in, do_validate
from fcsite.utils import sanitize_html
from fcsite.auth import do_login, requires_login, requires_permission

mod = Blueprint('general', __name__)


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


@mod.route('/')
def index():
    info_msgs = []

    if g.user:
        ns = notices.find_showing()
        info_msgs = info_msgs + [notice_to_message(n) for n in ns]

    if g.user and scheds.has_non_registered_practice(g.user.id):
        info_msgs.append(u'通知:未登録の練習があります。登録は' +
                u'<a href="%s">コチラから</a>。' % url_for('schedule.schedule'))
    return render_template('index.html', info_msgs=info_msgs)


def notice_to_message(notice):
    return u'%s:%s' % (notice['title'], notice['body'])


@mod.route('/login', methods=['POST'])
def login():
    passwd = request.form['password']
    if not do_login(passwd):
        error_message(u'ログインできません。パスワードが間違っています。')
    return redirect(url_for('general.index'))


@mod.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('general.index'))


@mod.route('/introduction')
def introduction():
    return render_template('introduction.html')


@mod.route('/report')
def report():
    return redirect(url_for('general.index'))


@mod.route('/gallery')
def gallery():
    return redirect(url_for('general.index'))


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
@requires_login
def tax_list():
    ts = taxes.find_all()
    return render_template('tax.html', taxes=ts)


@mod.route('/tax_for_new_year')
def tax_for_new_year():
    taxes.insert_for_new_year()
    return 'thanks'


@mod.route('/switch_payment/<int:year>/<string:season>/<int:user_id>')
@requires_permission(users.PERM_ADMIN_GOD)
def switch_payment(year, season, user_id):
    newpayments = taxes.switch_payment(year, season == 'first', user_id)
    return str(newpayments)
