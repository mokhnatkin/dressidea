from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://dressidea:fjEidk89@localhost:3306/dressidea'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)


class QuestionFromSite(db.Model):#вопрос с сайта
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),index=True, nullable=False)
    phone = db.Column(db.String(20),index=True, nullable=False)    
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    question = db.Column(db.String(1000))

#create tables in DB
QuestionFromSite.__table__.create(db.session.bind, checkfirst=True)
#Video.__table__.create(db.session.bind, checkfirst=True)

#drops tables
#Video.__table__.drop(db.session.bind)
#V_category.__table__.drop(db.session.bind)