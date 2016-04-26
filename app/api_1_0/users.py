from flask import jsonify, request, current_app, url_for, g
from . import api
from app.model import User, Post


@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    if g.current_user.equal_company(user):
        return jsonify(user.to_json_detailed())
    return jsonify(user.to_json())