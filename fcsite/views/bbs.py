# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for
from fcsite.models import bbs
from fcsite.utils import requires_login

mod = Blueprint('bbs', __name__, url_prefix='/bbs')


@mod.route('/')
@mod.route('/<int:page>')
@requires_login
def index(page=1):
    modelpage = max(0, page - 1)
    posts = bbs.find_posts_on_page(modelpage)
    pages = bbs.count_pages()
    return render_template('bbs.html', page=page, pages=pages, posts=posts)


@mod.route('/post', methods=['POST'])
@requires_login
def post():
    body = request.form['body']
    bbs.post(body)
    return redirect(url_for('bbs.index'))