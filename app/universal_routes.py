from flask import g, send_file, current_app, flash, redirect, url_for
from app.models import Const_public, Const_admin, Photo, Client, Subscription_type, Subscription, Visit
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


def get_full_subscription_info(active_only = False):#развернутое текстовое описание типов абонементов
    config_types = current_app.config['SUBSCRIPTION_TYPES']
    types_dict = dict()
    for t in config_types:
        types_dict[t[0]] = t[1]
    subscription_types = list()
    subscription_types_dict = dict()
    if active_only:
        _typesDB =  Subscription_type.query.filter(Subscription_type.active == True).all()
    else:
        _typesDB =  Subscription_type.query.all()
    for a in _typesDB:
        str_type = types_dict[a._type]
        if a._type == 'limited':
            desc = a.name + ': ' + str_type + '  |  ' +  str(a.days_valid)  + ' дней  |  ' +  str(a.hours_valid) + ' часов  |  ' + str(round(a.price)) + ' тг.'
        else:
            desc = a.name + ': ' + str_type + '  |  ' +  str(a.days_valid)  + ' дней  |  ' +  str(round(a.price)) + ' тг.'
        item = (str(a.id),desc)
        subscription_types.append(item)
        subscription_types_dict[a.id] = desc
    return subscription_types, subscription_types_dict


def compute_hours_for_subscription(client_id,subscription_id):#сколько времени клиент провел в рамках абонемента
    items = Visit.query \
                .filter(Visit.client_id == client_id) \
                .filter(Visit.subscription_id == subscription_id) \
                .filter(Visit.end != None).all()#все закрытые визиты по данному клиенту и абонементу
    visits = len(items)
    seconds = 0.0
    for item in items:
        duration = item.end - item.begin
        seconds += duration.total_seconds()
    hours = round(seconds / 3600,1)
    return hours,visits


def check_if_subscription_valid(_id):#является ли абонемент действующим
    res = False
    item = Subscription.query \
        .join(Subscription_type) \
        .with_entities(Subscription.id,Subscription.end,Subscription.start,Subscription.client_id,Subscription_type._type,Subscription_type.hours_valid) \
        .filter(Subscription.id == _id).first()
    now_moment = datetime.utcnow().date()#today's date
    if (item.end.date() < now_moment) or (item.start.date() > now_moment):
        return res
    else:
        if item._type == 'limited':
            hours, visits = compute_hours_for_subscription(item.client_id,item.id)
            if hours < item.hours_valid:
                res = True
        else:
            res = True
    return res


def check_if_client_has_valid_subscriptions(client_id):#есть ли у клиента действующие абонементы
    res = False
    items = Subscription.query \
            .with_entities(Subscription.id) \
            .filter(Subscription.client_id == client_id).all()
    for item in items:
        is_valid = check_if_subscription_valid(item.id)
        if is_valid:
            res = True
            break    
    return res


def find_valid_subscription(client_id):#возвращает id первого действующего абонемента    
    items = Subscription.query \
            .with_entities(Subscription.id) \
            .filter(Subscription.client_id == client_id).all()
    for item in items:
        is_valid = check_if_subscription_valid(item.id)
        if is_valid:
            res = item.id
            break
    return res    


def valid_subscription_for_client(client_id):#возвращаем массив с действующим абонементом по клиенту
    subscription_types, subscription_types_dict = get_full_subscription_info()
    subscription_id = find_valid_subscription(client_id)
    _item = Subscription.query.filter(Subscription.id == subscription_id).first()
    sub_desc = subscription_types_dict[_item.type_id]
    not_set = [('not_set','--визит не в рамках абонемента--')]
    valid_subscriptions = [(str(subscription_id),sub_desc)] + not_set
    return valid_subscriptions


def get_sub_desc(sub_id=None):#текстовое описание абонемента
    res = None
    if sub_id != None:
        subscription_types, subscription_types_dict = get_full_subscription_info()
        _item = Subscription.query.filter(Subscription.id == sub_id).first()    
        res = "Номер " + str(sub_id) + " - " +subscription_types_dict[_item.type_id]
    return res    