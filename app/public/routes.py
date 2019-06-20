from app import db
from flask import render_template, flash, redirect, url_for, request, g, \
                    send_file, current_app
from app.models import Const_public, Photo, Const_admin, ItemInside, \
                    Video, VideoCategory, QuestionFromSite                    
from app.public.forms import QuestionForm
from datetime import datetime
from flask_babel import get_locale
import os
from app.public import bp
from app.universal_routes import before_request_u, downloadFile_u, get_path_to_static_u, \
                    get_path_to_static_photo_albums_u, get_photos_for_photo_albums_u, \
                    get_video_type_name_u, send_email


@bp.before_request
def before_request():
    return before_request_u()


@bp.route('/')
@bp.route('/index')
def index():#главная страница
    title = 'Швейный коворкинг, город Алматы'
    meta_description = 'Место для любителей шитья, город Алматы. Всё швейное оборудование в наличии. Оплата по времени.'
    meta_keywords = 'Швейный коворкинг, швейная техника, швейное оборудование, аренда рабочего места, Алматы'
    items = ItemInside.query.filter(ItemInside.active==True).order_by(ItemInside.num).all()
    rate = None
    max_amount = None
    try:
        rate = round(g.const_admin.rate)
        max_amount = round(g.const_admin.max_amount)
    except:
        pass
    carousel_photos = None #фото для карусели
    carousel_photos_len = None
    show_carousel = False
    try:
        carousel_photos=Photo.query.with_entities(Photo.name) \
                            .filter(Photo.photo_type=='carousel') \
                            .filter(Photo.active==True).all()
        carousel_photos_len = len(carousel_photos)
    except:
        pass
    if carousel_photos_len is not None and carousel_photos_len>0:
        show_carousel = True
    else:
        show_carousel = False
    return render_template('public/index.html',title=title, carousel_photos=carousel_photos, carousel_photos_len=carousel_photos_len, \
                        show_carousel=show_carousel, rate = rate, max_amount = max_amount, items = items, \
                        meta_description = meta_description, meta_keywords=meta_keywords)


@bp.route('/gallery')#фото галлерея
def gallery():
    title = 'Фото швейного коворкинга Алматы'
    meta_description = 'Фотографии швейного оборудования. Швейный коворкинг, место для любителей шитья, город Алматы.'
    meta_keywords = 'Фото, шить, швейное оборудование, швейная мастерская, Алматы'
    gallery_photos = None #фото для карусели
    gallery_photos_len = None
    show_photos = False
    try:
        gallery_photos=Photo.query.with_entities(Photo.name, Photo.caption, Photo.descr) \
                            .filter(Photo.photo_type=='gallery') \
                            .filter(Photo.active==True).all()
        gallery_photos_len = len(gallery_photos)
    except:
        pass
    if gallery_photos_len is not None and gallery_photos_len>0:
        show_photos = True
    else:
        show_photos = False    
    return render_template('public/gallery.html',title=title,const_public=g.const_public, \
                        gallery_photos=gallery_photos,gallery_photos_len=gallery_photos_len, \
                        show_photos=show_photos, meta_description=meta_description,meta_keywords=meta_keywords)


@bp.route('/files_download/<ftype>/<album_name>/<fname>')#файл для скачивания на комп
def downloadFile(ftype,fname,album_name):
    return downloadFile_u(ftype,fname,album_name)


@bp.route('/get_path_to_static/<fname>')#путь к директории с фото, для отображения фото
def get_path_to_static(fname):
    return get_path_to_static_u(fname)


@bp.route('/get_path_to_static_photo_albums/<album_name>/<fname>')#путь к директории с фото, для отображения фото (фотоальбомы)
def get_path_to_static_photo_albums(album_name,fname):
    return get_path_to_static_photo_albums_u(album_name,fname)


def get_photos_for_photo_albums(album_name):
    return get_photos_for_photo_albums_u(album_name)


def get_video_type_name(video_id):
    return get_video_type_name_u(video_id)


@bp.route('/robots.txt')
@bp.route('/sitemap.xml')
def static_from_root():#отдает файлы robots.txt и sitemap.xml для поисковых машин
    return get_path_to_static(request.path[1:])


@bp.route('/about')#о проекте
def about():#о проекте
    title = 'Швейный коворкинг, город Алматы, о проекте'
    meta_description = 'Место для любителей шитья, город Алматы. О проекте, история'
    meta_keywords = 'Швейный коворкинг, швейное оборудование, Алматы, о проекте'    
    return render_template('public/about.html',title=title, meta_description = meta_description, \
                            meta_keywords=meta_keywords)


@bp.route('/video')#видео мастер-классов
def video():#мастер классы
    title = 'Швейный коворкинг, город Алматы, мастер-классы'
    meta_description = 'Место для любителей шитья, город Алматы. Мастер классы'
    meta_keywords = 'Швейный коворкинг, швейное оборудование, Алматы, мастер классы, фото, видео'
    videos_uploaded = False
    #все активные категории, где есть видео
    categories = VideoCategory.query.join(Video) \
                .filter(VideoCategory.active == True) \
                .order_by(VideoCategory.num).all()
    videos = VideoCategory.query.join(Video) \
                    .with_entities(VideoCategory.id,Video.v_type,Video.descr,Video.comment,Video.url,Video.timestamp) \
                    .filter(VideoCategory.active == True) \
                    .filter(Video.active == True) \
                    .order_by(VideoCategory.num) \
                    .order_by(Video.timestamp.desc()).all()
    if len(videos) > 0:
        videos_uploaded = True
    else:
        videos_uploaded = False
    return render_template('public/video.html',title=title, meta_description = meta_description, \
                            meta_keywords=meta_keywords, videos=videos, categories=categories, \
                            get_video_type_name=get_video_type_name, \
                            get_path_to_static_photo_albums=get_path_to_static_photo_albums,len=len,
                            get_photos_for_photo_albums=get_photos_for_photo_albums, \
                            videos_uploaded=videos_uploaded)


@bp.route('/ask_question',methods=['GET','POST'])#задать вопрос
def ask_question():
    title = 'Задать вопрос'
    form = QuestionForm()
    meta_description = 'Алматы, швейный коворкинг, Dressidea, задать вопрос'
    meta_keywords = 'Швейный коворкинг, швейная техника, швейное оборудование, аренда рабочего места, Алматы, задать вопрос'
    if form.validate_on_submit():
        q_name = form.name.data
        q_phone = form.phone.data
        q_question = form.question.data
        q = QuestionFromSite(name=q_name,phone=q_phone,question=q_question)
        try:
            db.session.add(q)
            db.session.commit()
            try:
                get_q_from_DB = QuestionFromSite.query \
                    .filter(QuestionFromSite.name == q_name) \
                    .filter(QuestionFromSite.phone == q_phone) \
                    .filter(QuestionFromSite.question == q_question) \
                    .first()
                _id = str(get_q_from_DB.id)
                _timestamp = get_q_from_DB.timestamp
            except:
                pass
            send_email('Новый вопрос с dressidea.kz',
                        sender=current_app.config['SENDER_EMAIL'],
                        recipients=[current_app.config['ADMIN_EMAIL']],
                        text_body=render_template('email/new_question.txt',
                                                    _id=_id,q_name=q_name,q_phone=q_phone,q_question=q_question,_timestamp=_timestamp),
                        html_body=render_template('email/new_question.html',
                                                    _id=_id,q_name=q_name,q_phone=q_phone,q_question=q_question,_timestamp=_timestamp))
            if _id:
                flash('Спасибо, мы получили Ваш вопрос и свяжемся с Вами в ближайшее время! Номер вопроса: '+_id)
            else:
                flash('Спасибо, мы получили Ваш вопрос и свяжемся с Вами в ближайшее время!')
        except:
            flash('Вопрос не может быть задан из-за технических неполадок. Пожалуйста, попробуйте чуть позже.')
            return redirect(url_for('public.ask_question'))
        return redirect(url_for('public.ask_question'))
    return render_template('public/ask_question.html',title=title,form=form, \
        meta_description=meta_description,meta_keywords=meta_keywords)


@bp.route('/pricing')#цена
def pricing():#цена
    title = 'Швейный коворкинг, город Алматы, цена'
    meta_description = 'Место для любителей шитья, город Алматы. Цена, стоимость.'
    meta_keywords = 'Швейный коворкинг, швейное оборудование, Алматы, цена, стоимость, визит, групповой визит'
    rate = None
    max_amount = None
    try:
        rate = round(g.const_admin.rate)
        max_amount = round(g.const_admin.max_amount)
        group_rate = round(g.const_admin.group_rate)
        group_max_amount = round(g.const_admin.group_max_amount)
    except:
        pass    
    return render_template('public/pricing.html',title=title, meta_description = meta_description, \
                            meta_keywords=meta_keywords, rate=rate, max_amount=max_amount, \
                            group_rate=group_rate, group_max_amount=group_max_amount)