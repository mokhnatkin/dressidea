from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin,db.Model):#пользователь
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(64),index=True,unique=True, nullable=False)
    email = db.Column(db.String(120),index=True,unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20),default='user', nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash,password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Const_public(db.Model):#храним константы для публичной части сайта
    id = db.Column(db.Integer,primary_key=True)
    descr = db.Column(db.String(1000))
    working_hours = db.Column(db.String(200))
    show_working_hours = db.Column(db.Boolean)
    addr = db.Column(db.String(500))    
    ya_map_id = db.Column(db.String(100))
    ya_map_width = db.Column(db.Integer)
    ya_map_height = db.Column(db.Integer)
    ya_map_static = db.Column(db.Boolean)
    phone = db.Column(db.String(20), nullable=False)
    insta = db.Column(db.String(50))
    insta_url = db.Column(db.String(100))


class Const_admin(db.Model):#храним константы для адм. части сайта (расчет)
    id = db.Column(db.Integer,primary_key=True)
    rate = db.Column(db.Float)
    max_amount = db.Column(db.Float)
    group_rate = db.Column(db.Float)
    google_analytics_tracking_id = db.Column(db.String(50))


class Photo(db.Model):#храним в таблице имена загруженных фото
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(200),index=True,unique=True)
    caption = db.Column(db.String(50))#100
    descr = db.Column(db.String(100))#1000
    photo_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime,default=datetime.utcnow)
    active = db.Column(db.Boolean)
    photoalbum = db.Column(db.String(500))

    def __repr__(self):
        return '<Photo {}>'.format(self.name)


class Client(db.Model):#карточка клиента
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),index=True, nullable=False)
    phone = db.Column(db.String(20),index=True,unique=True, nullable=False)
    insta = db.Column(db.String(50))
    source_id = db.Column(db.Integer,db.ForeignKey('client_source.id'))
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    comment = db.Column(db.String(200))
    bookings = db.relationship('Booking',backref='client',lazy='dynamic')
    visits = db.relationship('Visit',backref='client',lazy='dynamic')

    def __repr__(self):
        return '<Client {}>'.format(self.name)


class Booking(db.Model):#запись (регистрация) на посещение
    id = db.Column(db.Integer,primary_key=True)
    client_id = db.Column(db.Integer,db.ForeignKey('client.id'))
    begin = db.Column(db.DateTime,default=datetime.utcnow, nullable=False)
    end = db.Column(db.DateTime)
    comment = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    attended = db.Column(db.Boolean)


class Visit(db.Model):#посещение
    id = db.Column(db.Integer,primary_key=True)
    client_id = db.Column(db.Integer,db.ForeignKey('client.id'))
    begin = db.Column(db.DateTime,default=datetime.utcnow, nullable=False)
    end = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    comment = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    promo_id = db.Column(db.Integer,db.ForeignKey('promo.id'))


class ItemInside(db.Model):#что внутри коворкинга
    id = db.Column(db.Integer,primary_key=True)
    num = db.Column(db.Integer,unique=True, nullable=False)#номер для отображения
    name = db.Column(db.String(100),unique=True, nullable=False)
    active = db.Column(db.Boolean)


class ClientSource(db.Model):#источники - откуда приходят клиенты
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),unique=True, nullable=False)
    active = db.Column(db.Boolean)
    clients = db.relationship('Client',backref='clientsource',lazy='dynamic')


class VideoCategory(db.Model):#категории видео
    id = db.Column(db.Integer,primary_key=True)
    num = db.Column(db.Integer,unique=True, nullable=False)#номер для отображения
    name = db.Column(db.String(200),unique=True, nullable=False)
    active = db.Column(db.Boolean)
    videos = db.relationship('Video',backref='v_category',lazy='dynamic')


class Video(db.Model):#ссылки на мастер классы
    id = db.Column(db.Integer,primary_key=True)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    descr = db.Column(db.String(500),nullable=False)
    comment = db.Column(db.String(1000),nullable=False)
    url = db.Column(db.String(500),nullable=False)
    active = db.Column(db.Boolean)
    v_type = db.Column(db.Integer,nullable=False)#тип мастер класса - фото/видео
    category_id = db.Column(db.Integer,db.ForeignKey('video_category.id'))


class Promo(db.Model):#промо акции
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    promo_type = db.Column(db.Integer,nullable=False)#fix/discount/group/group_by_hours
    value = db.Column(db.Float,nullable=False)
    active = db.Column(db.Boolean)
    visits = db.relationship('Visit',backref='promo',lazy='dynamic')


class QuestionFromSite(db.Model):#вопрос с сайта
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),index=True, nullable=False)
    phone = db.Column(db.String(20),index=True, nullable=False)    
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    question = db.Column(db.String(1000))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
