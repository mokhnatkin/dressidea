from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://dressidea:fjEidk89@localhost:3306/dressidea'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)


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
    category_id = db.Column(db.Integer,db.ForeignKey('video_category.id'))

#create tables in DB
VideoCategory.__table__.create(db.session.bind, checkfirst=True)
#Video.__table__.create(db.session.bind, checkfirst=True)

#drops tables
#Video.__table__.drop(db.session.bind)
#V_category.__table__.drop(db.session.bind)