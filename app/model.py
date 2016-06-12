#coding=utf-8

from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user
from . import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from datetime import datetime, timedelta, date, time as dt_time
from flask import Markup
from time import strftime
import hashlib
import calendar

class Permission:
    CHECKIN = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATOR= 0x08
    ADMINISTER = 0x80


############################################################################################################################################ 

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


############################################################################################################################################ 

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(64), unique = True, index = True)
    username = db.Column(db.String(64), unique = True, index = True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default = False)
    nfc_label = db.Column(db.String(64), unique = True, index = True)
    #other info
    first_name = db.Column(db.String(64))
    middle_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    member_since = db.Column(db.DateTime(), default = datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default = datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    rate = db.Column(db.Integer, default = 40)
    #relationship
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    checkins = db.relationship('Checkin', backref = 'user', lazy = 'dynamic')
    timeCaches = db.relationship('TimeCache', backref = 'user', lazy = 'dynamic')
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
    notes = db.relationship('Note', backref = 'author', lazy = 'dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['TIMELOCK_ADMIN']:
                self.role = Role.query.filter_by(permissions = 0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(permissions = 0x07).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

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

    def gravatar(self, size = 100, default = 'retro', rating ='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url = url, hash = hash, size = size, default = default, rating = rating)

    def equal_company(self, user):
        return self.company == user.company

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id }).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        json_user = {
            'username': self.username,
            'member_since': self.member_since.strftime('%d.%m.%Y %H:%M:%S'),
            'last_seen': self.last_seen.strftime('%d.%m.%Y %H:%M:%S'),
            'avatar': self.gravatar(size = 300),
            'id': self.id,
            'company_name': self.company.company_name,
        }
        return json_user

    def to_json_detailed(self):
        json_user = {
            'username': self.username,
            'member_since': self.member_since.strftime('%d.%m.%Y %H:%M:%S'),
            'last_seen': self.last_seen.strftime('%d.%m.%Y %H:%M:%S'),
            'avatar': self.gravatar(size=300),
            'id': self.id,
            'company_name': self.company.company_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'middle_name': self.middle_name,
        }
        return json_user

    def __repr__(self):
        return '<User %r>' % self.username


############################################################################################################################################ 

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



############################################################################################################################################ 

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key = True)
    company_name = db.Column(db.String(64), unique = True, index = True)
    users = db.relationship('User', backref = 'company', lazy = 'dynamic')


############################################################################################################################################ 

class Checkin(db.Model):
    __tablename__ = 'checkins'
    id = db.Column(db.Integer, primary_key = True)
    time = db.Column(db.DateTime(), default = datetime.utcnow)
    trustLevel = db.Column(db.Boolean, default = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def get_checkins_page(page, user_id):
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
        monday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(monday, tuesday)).order_by(Checkin.time),
        tuesday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(tuesday, wednesday)).order_by(Checkin.time),
        wednesday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(wednesday, thursday)).order_by(Checkin.time),
        thursday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(thursday, friday)).order_by(Checkin.time),
        friday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(friday, saturday)).order_by(Checkin.time),
        saturday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(saturday, sunday)).order_by(Checkin.time),
        sunday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(sunday, next_monday)).order_by(Checkin.time)
        }

        work_time_list = [
        Checkin.get_work_time_for_checkins(dict[monday]),
        Checkin.get_work_time_for_checkins(dict[tuesday]),
        Checkin.get_work_time_for_checkins(dict[wednesday]),
        Checkin.get_work_time_for_checkins(dict[thursday]),
        Checkin.get_work_time_for_checkins(dict[friday]),
        Checkin.get_work_time_for_checkins(dict[saturday]),
        Checkin.get_work_time_for_checkins(dict[sunday])
        ]
        
        week_time = 0
        for minutes in work_time_list:
            week_time += minutes
        week_time_hours = week_time // 60
        week_time_minutes = week_time % 60
        format_string = "{0}:{1}"
        if (week_time_minutes < 10):
            format_string = "{0}:0{1}"
        week_time_string = format_string.format(week_time_hours, week_time_minutes)

        work_time_formats = []
        for minutes in work_time_list:
            total_hours = minutes // 60
            total_minutes = minutes % 60
            format_string = "{0}:{1}"
            if (total_minutes < 10):
                format_string = "{0}:0{1}"
            total_string = format_string.format(total_hours, total_minutes)
            work_time_formats.append(total_string)

        notes = {
        monday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(monday, datetime.min.time())).order_by(Note.id).all(),
        tuesday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(tuesday, datetime.min.time())).order_by(Note.id).all(),
        wednesday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(wednesday, datetime.min.time())).order_by(Note.id).all(),
        thursday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(thursday, datetime.min.time())).order_by(Note.id).all(),
        friday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(friday, datetime.min.time())).order_by(Note.id).all(),
        saturday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(saturday, datetime.min.time())).order_by(Note.id).all(),
        sunday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(sunday, datetime.min.time())).order_by(Note.id).all(),
        }

        result_dict = {
        monday: [Checkin.get_graphics_html(dict[monday], monday.weekday()), work_time_formats[0], notes[monday]],
        tuesday: [Checkin.get_graphics_html(dict[tuesday], tuesday.weekday()), work_time_formats[1], notes[tuesday]],
        wednesday: [Checkin.get_graphics_html(dict[wednesday], wednesday.weekday()), work_time_formats[2], notes[wednesday]],
        thursday: [Checkin.get_graphics_html(dict[thursday], thursday.weekday()), work_time_formats[3], notes[thursday]],
        friday: [Checkin.get_graphics_html(dict[friday], friday.weekday()), work_time_formats[4], notes[friday]],
        saturday: [Checkin.get_graphics_html(dict[saturday], saturday.weekday()), work_time_formats[5], notes[saturday]],
        sunday: [Checkin.get_graphics_html(dict[sunday], sunday.weekday()), work_time_formats[6], notes[sunday]] 
        }

        return result_dict, week_time_string, week_time

    @staticmethod
    def get_checkins_page_api(page, user_id):
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
        monday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(monday, tuesday)).order_by(Checkin.time),
        tuesday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(tuesday, wednesday)).order_by(Checkin.time),
        wednesday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(wednesday, thursday)).order_by(Checkin.time),
        thursday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(thursday, friday)).order_by(Checkin.time),
        friday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(friday, saturday)).order_by(Checkin.time),
        saturday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(saturday, sunday)).order_by(Checkin.time),
        sunday: Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(sunday, next_monday)).order_by(Checkin.time)
        }

        work_time_list = [
        Checkin.get_work_time_for_checkins(dict[monday]),
        Checkin.get_work_time_for_checkins(dict[tuesday]),
        Checkin.get_work_time_for_checkins(dict[wednesday]),
        Checkin.get_work_time_for_checkins(dict[thursday]),
        Checkin.get_work_time_for_checkins(dict[friday]),
        Checkin.get_work_time_for_checkins(dict[saturday]),
        Checkin.get_work_time_for_checkins(dict[sunday])
        ]

        date_tuple = monday.isocalendar()
        year = date_tuple[0]
        week = date_tuple[1]
        cache = TimeCache.query.filter_by(user_id = user_id, year = year, week = week).first()
        cache_time = 0
        if cache:
            cache_time = cache.time

        notes = {
        monday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(monday, datetime.min.time())).order_by(Note.id).all(),
        tuesday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(tuesday, datetime.min.time())).order_by(Note.id).all(),
        wednesday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(wednesday, datetime.min.time())).order_by(Note.id).all(),
        thursday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(thursday, datetime.min.time())).order_by(Note.id).all(),
        friday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(friday, datetime.min.time())).order_by(Note.id).all(),
        saturday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(saturday, datetime.min.time())).order_by(Note.id).all(),
        sunday: Note.query.filter_by(author_id = user_id, timestamp = datetime.combine(sunday, datetime.min.time())).order_by(Note.id).all(),
        }

        result_dict = {
        monday: [dict[monday], work_time_list[0], notes[monday]],
        tuesday: [dict[tuesday], work_time_list[1], notes[tuesday]],
        wednesday: [dict[wednesday], work_time_list[2], notes[wednesday]],
        thursday: [dict[thursday], work_time_list[3], notes[thursday]],
        friday: [dict[friday], work_time_list[4], notes[friday]],
        saturday: [dict[saturday], work_time_list[5], notes[saturday]],
        sunday: [dict[sunday], work_time_list[6], notes[sunday]] 
        }

        return result_dict, cache_time

    @staticmethod
    def get_graphics_html(checkins, weekday):
        result_string = "";

        if (checkins.count() < 2):
            if (checkins.count() == 0):
                result_string = "<p>On this day there was no checkins</p>"
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
            minutes_count = float(1440)
            width = 720
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
                begin_color = "#30D547"
                end_color = "#30D547"
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
            #add marking to graphics
            i = 1
            while (i < 24):
                x_offset = int(width * ((i * 60) / minutes_count))
                y_offset = 24
                if (i % 6 == 0):
                    y_offset = 12
                result_string += 'holst.strokeRect({0}, {1}, 0, {2});'.format(x_offset, y_offset, 30 - y_offset)
                i += 1
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

    @staticmethod
    def get_work_time_for_checkins(checkins):
        i = 0
        delta = 0
        while (i < checkins.count() - 1):
            first_checkin = checkins[i]
            second_checkin = checkins[i + 1]
            delta += (second_checkin.time - first_checkin.time).seconds // 60
            i +=2
        return delta

    @staticmethod
    def get_work_time_in_four_last_week(user_id):
        times = []
        for week in [1, 2, 3, 4]:
            times.append(Checkin.get_total_time_in_week(week, user_id))
        time_string = []
        for value in times:
            hours = value // 60
            minutes = value % 60
            if minutes < 10:
                minutes = "0{}".format(minutes)
            time_string.append("{}:{}".format(hours, minutes))
        return time_string, times;

    @staticmethod
    def get_total_time_in_week(week, user_id):
        current_day = datetime.now().date()
        delta = timedelta(days = current_day.weekday() + 7 * (week - 1))

        begin_day = current_day - delta
        i = 0
        time = 0
        while i < 7:
            end_day = begin_day + timedelta(days = 1)
            checkins = Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(begin_day, end_day)).order_by(Checkin.time)
            time += Checkin.get_work_time_for_checkins(checkins)
            begin_day = end_day
            i += 1
        return time

    def to_json(self, date):
        json_post = {
            'id': self.id,
            'trust_level': self.trustLevel,
            'time': self.time.strftime('%d.%m.%Y %H:%M:%S'),
            'date': date,
        }
        return json_post


############################################################################################################################################ 

class TimeCache(db.Model):
    __tablename__ = 'timeCaches'
    id = db.Column(db.Integer, primary_key = True)
    year = db.Column(db.Integer)
    week = db.Column(db.Integer)
    time = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def update_cache(user_id, date):
        date_tuple = date.isocalendar()
        year = date_tuple[0]
        week = date_tuple[1]
        delta = timedelta(days = date.weekday())
        begin_day = date.date() - delta;
        i = 0
        time = 0
        while i < 7:
            end_day = begin_day + timedelta(days = 1)
            checkins = Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(begin_day, end_day)).order_by(Checkin.time)
            time += Checkin.get_work_time_for_checkins(checkins)
            begin_day = end_day
            i += 1
        cache = TimeCache.query.filter_by(user_id = user_id, year = year, week = week).first()
        if not cache:
            cache = TimeCache(user_id = user_id, week = week, year = year, time = time)
        else:
            cache.time = time;
        db.session.add(cache)
        return time

    @staticmethod
    def get_cached_week_time(user_id, month_page):
        current_day = datetime.now().date()
        first_day = TimeCache.get_first_day(current_day, 0, -month_page + 1)
        last_day = TimeCache.get_last_day(first_day)
        day = first_day;

        # (year, week, weekday) = day.isocalendar()
        # (end_year, end_week, weekday) = last_day.isocalendar()
        # times = [];
        # while year < end_year or (year == end_year and week <= end_week):
        #     delta = timedelta(days = day.weekday())
        #     begin_day = day - delta;
        #     i = 0
        #     time = 0
        #     while i < 7:
        #         end_day = begin_day + timedelta(days = 1)
        #         checkins = Checkin.query.filter_by(user_id = user_id).filter(Checkin.time.between(begin_day, end_day)).order_by(Checkin.time)
        #         time += Checkin.get_work_time_for_checkins(checkins)
        #         begin_day = end_day
        #         i += 1
        #     times.append(time)
        #     day = day + timedelta(days = 7)
        #     (year, week, weekday) = day.isocalendar()
        # return times

        (year, week, weekday) = day.isocalendar()
        (end_year, end_week, weekday) = last_day.isocalendar()
        time = [];
        while year < end_year or (year == end_year and week <= end_week):
            cache = TimeCache.query.filter_by(user_id = user_id, year = year, week = week).first()
            if cache is not None:
                time.append(cache.time)
            else:
                time.append(0)
            day = day + timedelta(days = 7)
            (year, week, weekday) = day.isocalendar()
        return time

    @staticmethod
    def get_first_day(dt, d_years = 0, d_months = 0):
        # d_years, d_months are "deltas" to apply to dt
        y, m = dt.year + d_years, dt.month + d_months
        a, m = divmod(m - 1, 12)
        return date(y + a, m + 1, 1)

    @staticmethod
    def get_last_day(dt):
        return TimeCache.get_first_day(dt, 0, 1) + timedelta(-1)


############################################################################################################################################ 

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.now)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_json(self):
        json_post = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
            'author': self.author.to_json(),
        }
        return json_post


############################################################################################################################################      

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.now)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_json(self, date):
        json_post = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
            'date': date,
        }
        return json_post



