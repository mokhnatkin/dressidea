import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir,'.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')   
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')#path to uploaded files
    MAX_CONTENT_PATH = os.environ.get('MAX_CONTENT_PATH')#max size of uploaded file - 20MB
    PAGINATION_ITEMS_PER_PAGE = int(os.environ.get('PAGINATION_ITEMS_PER_PAGE'))    
    LANGUAGES = ['ru','en']
    EXT_FOR_PHOTOS = ['jpeg', 'jpg', 'png']
    PHOTO_TYPES = [('carousel','Карусель'), ('gallery','Галерея'), ('photoalbum','Фотоальбом')]#типы фото
    PHOTO_ALBUMS_FOLDER = os.environ.get('PHOTO_ALBUMS_FOLDER')
    V_TYPES = {'video':0,'photo':1}#типы мастер-классов
    V_TYPES_STR = [('video','Видео (youtube)'),('photo','Фото (карусель)')]#типы мастер-классов (для отображения)
    PROMO_TYPES = {'not_set':0,'fix_value':1,'discount':2,'group_visit':3,'group_visit_by_hours':4,'individual':5}#типы и id промо акций
    PROMO_TYPES_STR = [('fix_value','Фиксированный чек'),('discount','Скидка'),('group_visit','Групповой визит'),('group_visit_by_hours','Групповой визит по часам'),('individual','Индивидуальная оплата')]
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')#where to send emails from site
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')#sender of sys emails
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT= os.environ.get('MAIL_PORT')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ORDER_STATUS = [('new','Новый заказ'),('done','Выполнен'),('canceled','Отменен')]
    USER_ROLES = [('user','Помощник'),('admin','Администратор'),('director','Директор')]
