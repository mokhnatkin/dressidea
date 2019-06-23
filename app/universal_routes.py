from flask import g, send_file, current_app, flash, redirect, url_for
from app.models import Const_public, Const_admin, Photo, Client
from datetime import datetime
from flask_babel import get_locale
import os
from functools import wraps
from flask_login import current_user
from flask_mail import Message
from app import mail
from threading import Thread


#A function defintion which will work as a decorator for each view – we can call this with @required_roles
def required_roles_u(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if get_current_user_role() not in roles:
                flash('У вашей роли недостаточно полномочий','error')
                return redirect(url_for('public.index'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def get_current_user_role():#возвращает роль текущего пользователя
    return current_user.role


def before_request_u():#fetch some data before each request
    g.locale = str(get_locale())
    const_public = None
    const_admin = None
    try:
        const_public = Const_public.query.first()
        const_admin = Const_admin.query.first()
    except:
        pass
    g.const_public = const_public
    g.const_admin = const_admin
    debug_flag = os.environ.get('FLASK_DEBUG')
    if debug_flag == '1':
        g.debug_flag = True #признак - находится ли приложение в отладке
    else:
        g.debug_flag = False
    g.now_moment = datetime.utcnow()


def downloadFile_u(ftype,fname,album_name):
    if ftype=='photoalbum':
        p = os.path.join(os.path.dirname(os.path.abspath(current_app.config['UPLOAD_FOLDER'])),current_app.config['UPLOAD_FOLDER'],current_app.config['PHOTO_ALBUMS_FOLDER'],album_name,fname)
    else:
        p = os.path.join(os.path.dirname(os.path.abspath(current_app.config['UPLOAD_FOLDER'])),current_app.config['UPLOAD_FOLDER'],fname)
    return send_file(p, as_attachment=True)


def get_path_to_static_u(fname):
    p = os.path.join(os.path.dirname(os.path.abspath(current_app.config['UPLOAD_FOLDER'])),current_app.config['UPLOAD_FOLDER'],fname)
    return send_file(p)


def get_path_to_static_photo_albums_u(album_name,fname):
    p = os.path.join(os.path.dirname(os.path.abspath(current_app.config['UPLOAD_FOLDER'])),current_app.config['UPLOAD_FOLDER'],current_app.config['PHOTO_ALBUMS_FOLDER'],album_name,fname)
    return send_file(p)


def get_photos_for_photo_albums_u(album_name):#список фото для отображения в каруселе в мастер-классах
    photos = Photo.query \
            .filter(Photo.photo_type=='photoalbum') \
            .filter(Photo.photoalbum==album_name).all()
    return photos


def get_video_type_name_u(video_id):#получаем имя типа мастер-класса исходя из выбранного в форме
    v_types = current_app.config['V_TYPES']#типы мастер=классов (для системы)
    res = None   
    for key,val in v_types.items():
        if val==video_id:
            res = key    
    return res


def get_client_by_id(_id):#объект "клиент" по id
    client = Client.query.filter(Client.id == _id).first()
    return client


def send_async_email(app,msg):#async mail
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body,#отправка email
               attachments=None, sync=False):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()