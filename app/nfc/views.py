# -*- coding: utf-8 -*-

from flask import jsonify
from . import nfc
from app import db
from app.model import User, Checkin, TimeCache
from datetime import datetime


@nfc.route('/<string:nfc_label>', methods = ['GET'])
def index(nfc_label):
    print nfc_label
    now = datetime.now()
    now = now.replace(second = 0, microsecond = 0)
    user = User.query.filter_by(nfc_label = nfc_label).first()
    if not user:
        return jsonify({
            'success': False,
            'message': u'Пользователь с указанным кодом NFC-карты не найден'
            })
    checkin = Checkin(time = now, user_id = user.id, trustLevel = True)
    db.session.add(checkin)
    TimeCache.update_cache(user.id, now)
    return jsonify({
        'success': True,
        'message': u'Операция прошла успешно!'
        })




