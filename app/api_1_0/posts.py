from flask import jsonify, request, g, abort, url_for, current_app
from app import db
from app.model import Post, Permission
from . import api
from .errors import forbidden


@api.route('/posts/')
def get_posts():
    page = request.args.get('page', 1, type = int)
    pagination = Post.query.paginate(
        page, per_page = current_app.config['TIMELOCK_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'count': pagination.total
    })

@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())