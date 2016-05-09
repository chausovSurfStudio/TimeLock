# -*- coding: utf-8 -*-

from flask import jsonify, request, current_app, url_for, g
from . import api
from app.model import User, Post
from .errors import forbidden, bad_request
from app import db


@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    if g.current_user.equal_company(user):
        return jsonify(user.to_json_detailed())
    return jsonify(user.to_json())

@api.route('/users/')
def current_user():
    user = User.query.get_or_404(g.current_user.id)
    return jsonify(user.to_json_detailed())

@api.route('/users/<int:id>', methods = ['PUT'])
def edit_user(id):
	user = User.query.get_or_404(id)
	if g.current_user != user:
		return forbidden(u'У Вас нет доступа для изменения данных этого аккаунта')
	json = request.json
	new_username = json.get('username', user.username)
	if new_username != g.current_user.username and User.query.filter_by(username = new_username).first():
		return bad_request(u'Данное имя пользователя уже используется')
	if len(new_username) == 0:
		return bad_request(u'Имя пользователя не может быть пустой строкой')
	user.username = new_username;
	user.first_name = json.get('first_name', user.first_name)
	user.last_name = json.get('last_name', user.last_name)
	user.middle_name = json.get('middle_name', user.middle_name)
	db.session.add(user)
	return jsonify(user.to_json_detailed())