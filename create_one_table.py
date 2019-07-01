from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://dressidea:fjEidk89@localhost:3306/dressidea'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)

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
    visits = db.relationship('Order',backref='client',lazy='dynamic')

    def __repr__(self):
        return '<Client {}>'.format(self.name)

class Order(db.Model):#мои заказы
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_id = db.Column(db.Integer,db.ForeignKey('client.id'))
    description = db.Column(db.String(1000))
    begin = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)

#create tables in DB
Order.__table__.create(db.session.bind, checkfirst=True)
#Video.__table__.create(db.session.bind, checkfirst=True)

#drops tables
#Video.__table__.drop(db.session.bind)
#V_category.__table__.drop(db.session.bind)