from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user
from . import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from datetime import datetime, timedelta, date, time as dt_time
from flask import Markup
from time import strftime

class Permission:
    CHECKIN = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATOR= 0x08
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), unique = True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref = 'role', lazy = 'dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.CHECKIN | Permission.COMMENT | Permission.WRITE_ARTICLES),
            'LockedUser': (Permission.CHECKIN),
            'Moderator': (Permission.CHECKIN | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.MODERATOR),
            'Administrator': (0xff)
        }
        for r in roles:
            role = Role.query.filter_by(name = r).first()
            if role is None:
                role = Role(name = r)
            role.permissions = roles[r]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(64), unique = True, index = True)
    username = db.Column(db.String(64), unique = True, index = True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default = False)
    nfc_label = db.Column(db.String(64), unique = True, index = True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    checkins = db.relationship('Checkin', backref = 'user', lazy = 'dynamic')
    #other info
    first_name = db.Column(db.String(64))
    middle_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    member_since = db.Column(db.DateTime(), default = datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default = datetime.utcnow)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['TIMELOCK_ADMIN']:
                self.role = Role.query.filter_by(permissions = 0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(permissions = 0x07).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __rept__(self):
        return '<User %r' % self.username

    def generate_confirmation_token(self, expiration = 3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm' : self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def is_moderator(self):
        return self.can(Permission.MODERATOR)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def password_is_empty(self):
        return not self.password_hash

    def __repr__(self):
        return '<User %r>' % self.username

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key = True)
    company_name = db.Column(db.String(64), unique = True, index = True)
    users = db.relationship('User', backref = 'company', lazy = 'dynamic')

class Checkin(db.Model):
    __tablename__ = 'checkins'
    id = db.Column(db.Integer, primary_key = True)
    time = db.Column(db.DateTime(), default = datetime.utcnow)
    trustLevel = db.Column(db.Boolean, default = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def get_checkins_page(page):
        current_day = datetime.now().date()
        delta = timedelta(days = current_day.weekday() + 7 * (page - 1))

        monday = current_day - delta
        tuesday = monday + timedelta(days = 1)
        wednesday = tuesday + timedelta(days = 1)
        thursday = wednesday + timedelta(days = 1)
        friday = thursday + timedelta(days = 1)
        saturday = friday + timedelta(days = 1)
        sunday = saturday + timedelta(days = 1)
        next_monday = sunday + timedelta(days = 1)

        dict = {
        monday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(monday, tuesday)).order_by(Checkin.time),
        tuesday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(tuesday, wednesday)).order_by(Checkin.time),
        wednesday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(wednesday, thursday)).order_by(Checkin.time),
        thursday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(thursday, friday)).order_by(Checkin.time),
        friday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(friday, saturday)).order_by(Checkin.time),
        saturday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(saturday, sunday)).order_by(Checkin.time),
        sunday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(sunday, next_monday)).order_by(Checkin.time)
        }

        html_dict = {
        monday: Checkin.get_graphics_html(dict[monday], monday.weekday()),
        tuesday: Checkin.get_graphics_html(dict[tuesday], tuesday.weekday()),
        wednesday: Checkin.get_graphics_html(dict[wednesday], wednesday.weekday()),
        thursday: Checkin.get_graphics_html(dict[thursday], thursday.weekday()),
        friday: Checkin.get_graphics_html(dict[friday], friday.weekday()),
        saturday: Checkin.get_graphics_html(dict[saturday], saturday.weekday()),
        sunday: Checkin.get_graphics_html(dict[sunday], sunday.weekday())
        }

        return html_dict

    @staticmethod
    def get_graphics_html(checkins, weekday):
        result_string = "";

        if (checkins.count() < 2):
            if (checkins.count() == 0):
                result_string = "<p>Empty day</p>"
            else:
                #this case will be processed later
                print("this case will be processed later")
        else:
            result_string = '<canvas class="box" id="Mycanvas{}" width="720" height="40" border="6"\
                            onmouseover="tooltip(this)" onmouseout="hide_info(this)"></canvas>'.format(weekday)
            result_string += '<script>\
                                var canvas = document.getElementById(\'Mycanvas{0}\');\
                                var holst = canvas.getContext(\'2d\');\
                                holst.strokeStyle = "rgb(103, 103, 103)";\
                                holst.strokeRect(0, 0, 720, 30);'.format(weekday)
            #add marking to graphics
            i = 1
            minutes_count = float(1440)
            width = 720
            while (i < 24):
                x_offset = int(width * ((i * 60) / minutes_count))
                y_offset = 24
                if (i % 6 == 0):
                    y_offset = 12
                result_string += 'holst.strokeRect({0}, {1}, 0, {2});'.format(x_offset, y_offset, 30 - y_offset)
                i += 1
            #add labels with time
            i = 3
            while (i <= 21):
                x_offset = int(width * ((i * 60) / minutes_count))
                y_offset = 30
                time = "{0}:00".format(i)
                result_string += 'holst.textAlign = "center";\
                                holst.textBaseline = "top";\
                                holst.fillText("{0}", {1}, {2});'.format(time, x_offset, y_offset)
                i += 3
            i = 0
            while (i < checkins.count() - 1):
                first_checkin = checkins[i]
                second_checkin = checkins[i + 1]
                begin_minutes = first_checkin.time.hour * 60 + first_checkin.time.minute
                end_minutes = second_checkin.time.hour * 60 + second_checkin.time.minute
                x_begin = int(width * (begin_minutes / minutes_count))
                x_end = int(width * (end_minutes / minutes_count))
                begin_color = "#F3C05E"
                end_color = "#F3C05E"
                if (first_checkin.trustLevel):
                    begin_color = "green"
                if (second_checkin.trustLevel):
                    end_color = "green"
                result_string += 'var my_gradient{0} = holst.createLinearGradient({1},0,{2},0);\
                                    my_gradient{0}.addColorStop(0,\"{4}\");\
                                    my_gradient{0}.addColorStop(1,\"{5}\");\
                                    holst.fillStyle = my_gradient{0};\
                                    holst.fillRect({1}, 0, {3}, 30);'.format(i, x_begin, x_end, x_end - x_begin, begin_color, end_color)
                i = i + 2
            result_string += '</script>'
            if (checkins.count() % 2 != 1):
                result_string += "<div class=\"checkins-empty-space\"></div>"
        if (checkins.count() % 2 == 1):
            if (checkins.count() == 1):
                result_string += '<p>Only one checkins in '
            else:
                result_string += '<p>And one more checkins in '
            result_string += '<a class="total-time">{0}</a></p>'.format((checkins[checkins.count() - 1].time).strftime("%-H:%M:%S"))
        return Markup(result_string)

    @staticmethod
    def get_checkin_with_time(selected_date, user_id):
        checkin = Checkin.query.filter_by(time = selected_date, user_id = user_id).first()
        return checkin







