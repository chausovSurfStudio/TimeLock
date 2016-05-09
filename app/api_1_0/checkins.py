from flask import jsonify, request, g, abort, url_for, current_app
from app import db
from app.model import Checkin, User
from . import api
from .errors import forbidden

@api.route('/checkins')
def get_checkins_page():
	(dict, cache) = Checkin.get_checkins_page_api(1, g.current_user.id)
	keys = dict.keys()
	keys.sort()

	result_json = {}
	days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
	i = 0
	for date in keys:
		result_json[days[i]] = {}
		result_json[days[i]]["date"] = date.strftime('%d.%m.%Y %H:%M:%S')
		result_json[days[i]]["time"] = dict[date][1]
		result_json[days[i]]["checkins"] = []
		for checkin in dict[date][0]:
			result_json[days[i]]["checkins"].append(checkin.to_json())
		result_json[days[i]]["notes"] = []
		for note in dict[date][2]:
			result_json[days[i]]["notes"].append(note.to_json())
		i += 1
	result_json["week_time"] = cache
	return jsonify(result_json)