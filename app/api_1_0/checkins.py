from flask import jsonify, request, g, abort, url_for, current_app
from app import db
from app.model import Checkin, User
from . import api
from .errors import forbidden

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