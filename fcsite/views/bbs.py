# -*- coding: utf-8 -*-

from flask import render_template, request, redirect, url_for, abort
from fcsite import check_forced_registration_blueprint
from fcsite.models import bbs
from fcsite.auth import requires_login
from fcsite.utils import pagination, logi

mod = check_forced_registration_blueprint('bbs', __name__, url_prefix='/bbs')


@mod.route('/')
@mod.route('/<int:page>')
@requires_login
def index(page=1):
    modelpage = max(0, page - 1)
    posts = bbs.find_posts_on_page(modelpage)
    pages = bbs.count_pages()
    if page > pages:
        abort(404)
    begin, end = pagination(page, pages)
    return render_template('bbs.html', page=page, pages=pages, posts=posts,
            begin=begin, end=end)


@mod.route('/post', methods=['POST'])
@requires_login
def post():
    logi('bbs post')
    body = request.form['body']
    bbs.post(body)
    return redirect(url_for('bbs.index'))
