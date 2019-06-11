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

    