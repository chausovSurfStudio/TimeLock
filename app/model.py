from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user
from . import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from datetime import datetime, timedelta, date, time as dt_time

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

        print("last monday = ", monday.strftime('%y-%m-%d %H:%M:%S'))
        print("next monday = ", next_monday.strftime('%y-%m-%d %H:%M:%S'))

        checkins = Checkin.query.filter(Checkin.time.between(monday, next_monday)).filter_by(user_id = current_user.id)
        dict = {
        monday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(monday, tuesday)),
        tuesday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(tuesday, wednesday)),
        wednesday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(wednesday, thursday)),
        thursday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(thursday, friday)),
        friday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(friday, saturday)),
        saturday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(saturday, sunday)),
        sunday: Checkin.query.filter_by(user_id = current_user.id).filter(Checkin.time.between(sunday, next_monday))
        }
        return dict




