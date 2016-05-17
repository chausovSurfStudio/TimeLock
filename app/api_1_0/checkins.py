# -*- coding: utf-8 -*-

from flask import jsonify, request, g, abort, url_for, current_app
from app import db
from app.model import Checkin, User, TimeCache
from . import api
from .errors import forbidden, bad_request
from datetime import datetime
import re

@api.route('/checkins/')
def get_checkins_page():
	page = request.args.get('page', 1, type = int)
	(dict, cache) = Checkin.get_checkins_page_api(page, g.current_user.id)
	keys = dict.keys()
	keys.sort()

	result_json = {}
	result_json["checkins"] = []
	result_json["notes"] = []
	result_json["times"] = []
	for date in keys:
		date_string = date.strftime('%d.%m.%Y %H:%M:%S')
		for checkin in dict[date][0]:
			result_json["checkins"].append(checkin.to_json(date_string))
		for note in dict[date][2]:
			result_json["notes"].append(note.to_json(date_string))
		result_json["times"].append(dict[date][1])
	result_json["times"].append(cache)
	result_json["monday"] = keys[0].strftime('%d.%m.%Y %H:%M:%S')
	return jsonify(result_json)

@api.route('/checkins/<int:checkin_id>', methods = ['DELETE'])
def delete_checkin(checkin_id):
	checkin = Checkin.query.filter_by(id = checkin_id).first()
	if not checkin:
		return bad_request(u'Запрошенный к удалению чекин не найден')
	if checkin.user_id != g.current_user.id:
		return bad_request(u'Вы не можете изменять чекины других пользователей')
	db.session.delete(checkin)
	TimeCache.update_cache(g.current_user.id, checkin.time)
	return jsonify({'success': True})

@api.route('/checkins/', methods = ['POST'])
def create_checkin():
	json = request.json
	date_string = json.get('date_string', "")
	if date_string == '':
		return bad_request(u'Неверные параметры запроса')
	regular_expression = re.compile("\d{1,2}\.\d{1,2}\.\d{4} \d{1,2}:\d{2}:\d{2}")
	if not regular_expression.match(date_string):
		return bad_request(u'Неверные параметры запроса')
	date = datetime.strptime(date_string, "%d.%m.%Y %H:%M:%S")
	if date > datetime.now():
		return bad_request(u'Вы не можете создать чекин заранее, выберите более раннюю дату')
	checkin = Checkin(user_id = g.current_user.id, time = date, trustLevel = False)
	db.session.add(checkin)
	db.session.commit()
	TimeCache.update_cache(g.current_user.id, checkin.time)
	result_json = {}
	result_json['checkin'] = checkin.to_json(checkin.time.date().strftime('%d.%m.%Y %H:%M:%S'))
	result_json['success'] = True
	return jsonify(result_json)

@api.route('/checkins/<int:checkin_id>', methods = ['PUT'])
def edit_checkin(checkin_id):
	checkin = Checkin.query.filter_by(id = checkin_id).first()
	if not checkin:
		return bad_request(u'Запрошенный чекин не найден, изменение данных невозможно')
	if checkin.user_id != g.current_user.id:
		return bad_request(u'Вы не можете изменять чекины других пользователей')
	json = request.json
	date_string = json.get('date_string', "")
	if date_string == '':
		return bad_request(u'Неверные параметры запроса')
	regular_expression = re.compile("\d{1,2}\.\d{1,2}\.\d{4} \d{1,2}:\d{2}:\d{2}")
	if not regular_expression.match(date_string):
		return bad_request(u'Неверные параметры запроса')
	date = datetime.strptime(date_string, "%d.%m.%Y %H:%M:%S")
	if date > datetime.now():
		return bad_request(u'Вы не можете создать чекин заранее, выберите более раннюю дату')
	checkin.time = date
	db.session.add(checkin)
	db.session.commit()
	TimeCache.update_cache(g.current_user.id, checkin.time)
	result_json = {}
	result_json['checkin'] = checkin.to_json(checkin.time.date().strftime('%d.%m.%Y %H:%M:%S'))
	result_json['success'] = True
	return jsonify(result_json)








