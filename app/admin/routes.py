from app import db
from flask import render_template, flash, redirect, url_for, request, g, \
                    send_file, send_from_directory, current_app
from app.models import User, Const_public, Photo, Const_admin, ItemInside, ClientSource, \
                        Client, Visit, Booking, Video, VideoCategory, Promo, QuestionFromSite                    
from app.admin.forms import PhotoUploadForm, Const_adminForm, \
                    Const_publicForm, PhotoEditForm, ItemInsideForm, ClientSourceForm, \
                    ClientForm, VisitForm, BookingForm, ClientSearchForm, ClientChangeForm, \
                    PeriodInputForm, VideoCategoryForm, VideoForm, PromoForm, \
                    ConfirmGroupVisitAmountForm, EditVisitAmountForm
from flask_login import current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_babel import get_locale
import os
from functools import wraps
from sqlalchemy import func
import cyrtranslit
from app.admin import bp
from app.universal_routes import before_request_u, downloadFile_u, get_path_to_static_u, \
                    get_path_to_static_photo_albums_u, get_photos_for_photo_albums_u, \
                    get_video_type_name_u, required_roles_u, get_client_by_id


@bp.before_request
def before_request():
    return before_request_u()


def required_roles(*roles):
    return required_roles_u(*roles)


def add_str_timestamp(filename):#adds string timestamp to filename in order to make in unique
    dt = datetime.utcnow()
    stamp = round(dt.timestamp())
    uId = str(stamp)
    u_filename = uId+'_'+filename
    return u_filename


@bp.route('/upload_file',methods=['GET', 'POST'])#загрузить фото
@login_required
@required_roles('admin')
def upload_file():
    title = 'Загрузка фото'
    form = PhotoUploadForm()
    descr = 'Здесь загружаются фото для отображения в карусели на главной странице, или в галерее'    
    if form.validate_on_submit():
        f = form.photo.data        
        filename = secure_filename(f.filename)
        filename = add_str_timestamp(filename)
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        photo = Photo(name=filename,photo_type=form.photo_type.data,active=form.active.data,caption=form.caption.data,descr=form.descr.data)
        db.session.add(photo)
        db.session.commit()
        flash('Фото успешно загружено!')
        return redirect(url_for('admin.upload_file'))
    return render_template('admin/upload_file.html', title=title,form=form,descr=descr)


@bp.route('/delete_file/<fid>')#физически удалить фото
@login_required
@required_roles('admin')
def delete_file(fid = None):
    photo = Photo.query.filter(Photo.id == fid).first()
    if photo is not None:
        if photo.active:
            flash('Нельзя удалить фото, которое отображается на сайте. Сначала его нужно скрыть.')
            return redirect(url_for('admin.files',param='all',album_name='None'))
        else:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], photo.name))
                db.session.delete(photo)
                db.session.commit()
                flash('Фото удалено с сервера')                
            except:
                flash('Не удалось выполнить физическое удаление фото с сервера. Файл не найден.')
                return redirect(url_for('admin.files',param='all',album_name='None'))
    else:
        flash('Фото для удаления не найдено')
        return redirect(url_for('admin.files',param='all',album_name='None'))
    return redirect(url_for('admin.files',param='all',album_name='None'))


@bp.route('/edit_file/<fid>',methods=['GET', 'POST'])#изменить фото
@login_required
@required_roles('admin')
def edit_file(fid = None):
    title = 'Редактирование типа и описания фото'
    form = PhotoEditForm()    
    descr = 'Здесь можно изменить заголовок, описание или тип фото'
    photo = Photo.query.filter(Photo.id == fid).first()
    if request.method == 'GET':
        form = PhotoEditForm(obj=photo)
    if form.validate_on_submit():
        photo.photo_type = form.photo_type.data
        photo.caption = form.caption.data
        photo.descr = form.descr.data
        db.session.commit()        
        flash('Фото успешно изменено!')
        return redirect(url_for('admin.files',param='all',album_name='None'))
    return render_template('admin/edit_file.html', title=title,form=form,descr=descr)


@bp.route('/files/<param>/<album_name>')#список загруженных фото
@login_required
@required_roles('admin')
def files(param,album_name=None):
    if param == 'all':
        files = Photo.query.all()
    elif param == 'carousel':
        files = Photo.query.filter(Photo.photo_type=='carousel').all()
    elif param == 'gallery':
        files = Photo.query.filter(Photo.photo_type=='gallery').all()
    elif param == 'photoalbum':
        if album_name == 'None_album_selected':
            files = Photo.query.filter(Photo.photo_type=='photoalbum').all()
        else:
            files = Photo.query \
                .filter(Photo.photo_type=='photoalbum') \
                .filter(Photo.photoalbum==album_name).all()
    return render_template('admin/files.html',files=files)


@bp.route('/files_download/<ftype>/<album_name>/<fname>')#файл для скачивания на комп
def downloadFile(ftype,fname,album_name):
    return downloadFile_u(ftype,fname,album_name)


@bp.route('/get_path_to_static/<fname>')#путь к директории с фото, для отображения фото
def get_path_to_static(fname):
    return get_path_to_static_u(fname)


@bp.route('/get_path_to_static_photo_albums/<album_name>/<fname>')#путь к директории с фото, для отображения фото (фотоальбомы)
def get_path_to_static_photo_albums(album_name,fname):
    return get_path_to_static_photo_albums_u(album_name,fname)


@bp.route('/activate_files/<fid>')#активировать фото для отображения на сайте
@login_required
@required_roles('admin')
def activateFile(fid = None):
    f = Photo.query.filter(Photo.id == fid).first()    
    try:        
        f.active = True
        db.session.commit()
        flash('Фото успешно активировано!')
    except:
        flash('Не удалось')
    return redirect(url_for('admin.files',param='all',album_name='None'))


@bp.route('/deactivate_files/<fid>')#активировать фото для отображения на сайте
@login_required
@required_roles('admin')
def deactivateFile(fid = None):
    f = Photo.query.filter(Photo.id == fid).first()    
    try:        
        f.active = False
        db.session.commit()
        flash('Деактивировано')
    except:
        flash('Не удалось')
    return redirect(url_for('admin.files',param='all',album_name='None'))


@bp.route('/const_admin',methods=['GET', 'POST'])#константы для админки
@login_required
@required_roles('admin')
def const_admin():
    title='Константы админки'
    form = Const_adminForm()
    descr = 'Здесь изменяются константы админки, используемые для расчетов'
    const_set = None
    try:
        const_set = Const_admin.query.first()
    except:
        pass
    if request.method == 'GET':
        if const_set is not None:
            form = Const_adminForm(obj=const_set)
    if form.validate_on_submit():
        if const_set is not None:
            const_set.rate=form.rate.data
            const_set.max_amount = form.max_amount.data
            const_set.group_rate=form.group_rate.data
            const_set.group_max_amount=form.group_max_amount.data
            const_set.google_analytics_tracking_id = form.google_analytics_tracking_id.data
        else:
            const = Const_admin(rate=form.rate.data,group_rate=form.group_rate.data, \
                group_max_amount=form.group_max_amount.data, \
                max_amount=form.max_amount.data,google_analytics_tracking_id=form.google_analytics_tracking_id.data)
            db.session.add(const)
        db.session.commit()
        flash('Значения констант изменены!')
        return redirect(url_for('admin.const_admin'))
    return render_template('admin/const_admin.html', title=title,form=form,descr=descr)


@bp.route('/const_public',methods=['GET', 'POST'])#константы для паблика
@login_required
@required_roles('admin')
def const_public():
    title='Константы паблика'
    form = Const_publicForm()
    descr = 'Здесь изменяются константы админки, используемые для расчетов'
    const_set = None
    try:
        const_set = Const_public.query.first()
    except:
        pass
    if request.method == 'GET':#показываем данные из БД в форме
        if const_set is not None:
            form = Const_publicForm(obj=const_set)
    if form.validate_on_submit():#обновляем данные в БД
        if const_set is not None:
            const_set.descr = form.descr.data
            const_set.working_hours = form.working_hours.data
            const_set.show_working_hours = form.show_working_hours.data
            const_set.addr = form.addr.data
            const_set.ya_map_id = form.ya_map_id.data
            const_set.ya_map_width = form.ya_map_width.data
            const_set.ya_map_height = form.ya_map_height.data
            const_set.ya_map_static = form.ya_map_static.data
            const_set.phone = form.phone.data
            const_set.insta = form.insta.data
            const_set.insta_url = form.insta_url.data
        else:
            const = Const_public(descr=form.descr.data,working_hours=form.working_hours.data, \
                                show_working_hours=form.show_working_hours.data,addr=form.addr.data, \
                                ya_map_id=form.ya_map_id.data,ya_map_width=form.ya_map_width.data, \
                                ya_map_height=form.ya_map_height.data,ya_map_static=form.ya_map_static.data, \
                                phone=form.phone.data,insta=form.insta.data,insta_url=form.insta_url.data)
            db.session.add(const)
        db.session.commit()
        flash('Значения констант изменены!')
        return redirect(url_for('admin.const_public'))
    return render_template('admin/const_public.html', title=title,form=form,descr=descr)


@bp.route('/users')#список пользователей
@login_required
@required_roles('admin')
def users():
    title = 'Список пользователей'
    users = User.query.all()
    return render_template('admin/users.html', title=title, users=users)


@bp.route('/give_admin_role/<uid>')#присвоить пользователю роль admin
@login_required
@required_roles('admin')
def give_admin_role(uid = None):
    u = User.query.filter(User.id == uid).first()    
    try:
        u.role = 'admin'
        db.session.commit()        
    except:
        flash('Не удалось сменить роль')
    return redirect(url_for('admin.users'))


@bp.route('/give_user_role/<uid>')#присвоить пользователю роль user
@login_required
@required_roles('admin')
def give_user_role(uid = None):
    u = User.query.filter(User.id == uid).first()    
    try:
        u.role = 'user'
        db.session.commit()        
    except:
        flash('Не удалось сменить роль')
    return redirect(url_for('admin.users'))


@bp.route('/edit_item_inside/<item_id>',methods=['GET', 'POST'])#предменты в коворкинге (списком на главной)
@login_required
@required_roles('admin')
def edit_item_inside(item_id = None):
    title='Оборудование внутри коворкинга'
    form = ItemInsideForm()
    descr = 'Здесь изменяется список оборудования в коворкинге'
    item = ItemInside.query.filter(ItemInside.id == item_id).first()
    if request.method == 'GET':
        form = ItemInsideForm(obj=item)
    if form.validate_on_submit():
        item.num = form.num.data
        item.name = form.name.data
        item.active = form.active.data
        db.session.commit()
        flash('Значения изменены!')
        return redirect(url_for('admin.item_inside'))
    return render_template('admin/item_inside.html', title=title,form=form,descr=descr)


@bp.route('/item_inside',methods=['GET','POST'])#дополнить список оборудования
@login_required
@required_roles('admin')
def item_inside():
    title='Оборудование внутри коворкинга'
    descr = 'Здесь изменяется список оборудования в коворкинге'
    form = ItemInsideForm()
    items = ItemInside.query.all()
    if form.validate_on_submit():
        num = form.num.data
        try:
            item_num_already_in_DB = ItemInside.query.filter(ItemInside.num == num).first()            
        except:
            pass
        name = form.name.data
        try:
            item_name_already_in_DB = ItemInside.query.filter(ItemInside.name == name).first()            
        except:
            pass            
        if item_num_already_in_DB is None and item_name_already_in_DB is None:
            item = ItemInside(num=num,name=name,active=form.active.data)        
            db.session.add(item)
            db.session.commit()
            flash('Добавлено!')
        else:
            flash('Ошибка - оборудование с таким порядковым номером или названием уже есть в базе. Выберите другой номер / название!')
        return redirect(url_for('admin.item_inside'))
    return render_template('admin/item_inside.html',title=title,descr=descr,form=form,items=items)


@bp.route('/admin')#админка - общее описание
@login_required
def admin():    
    return render_template('admin/admin.html',title='Админка')


@bp.route('/sources',methods=['GET','POST'])#дополнить список источников
@login_required
@required_roles('admin')
def sources():
    title='Источники (откуда приходят клиенты)'
    descr = 'Здесь администрируются источники (откуда приходят клиенты)'
    form = ClientSourceForm()
    items = ClientSource.query.all()
    if form.validate_on_submit():
        name = form.name.data
        try:
            item_name_already_in_DB = ClientSource.query.filter(ClientSource.name == name).first()            
        except:
            pass
        if item_name_already_in_DB is None:
            item = ClientSource(name=name,active=form.active.data)        
            db.session.add(item)
            db.session.commit()
            flash('Добавлено!')
        else:
            flash('Ошибка - такой источник уже есть в базе')
        return redirect(url_for('admin.sources'))
    return render_template('admin/sources.html',title=title,descr=descr,form=form,items=items)


@bp.route('/edit_source/<item_id>',methods=['GET', 'POST'])#редактируем источники
@login_required
@required_roles('admin')
def edit_source(item_id = None):
    title='Список источников'
    form = ClientSourceForm()
    descr = 'Здесь изменяется список источников (откуда приходят клиенты)'
    item = ClientSource.query.filter(ClientSource.id == item_id).first()
    if request.method == 'GET':
        form = ClientSourceForm(obj=item)
    if form.validate_on_submit():
        item.name = form.name.data
        item.active = form.active.data
        db.session.commit()
        flash('Значения изменены!')
        return redirect(url_for('admin.sources'))
    return render_template('admin/sources.html', title=title,form=form,descr=descr)


@bp.route('/add_client',methods=['GET','POST'])#добавить клиента
@login_required
def add_client():
    title='Добавить клиента'
    descr = 'Здесь создается карточка клиента'
    form = ClientForm()
    if form.validate_on_submit():
        phone = form.phone.data
        try:
            phone_already_in_DB = Client.query.filter(Client.phone == phone).first()
        except:
            pass
        name = form.name.data
        if phone_already_in_DB is None:
            if form.source.data == 'not_set':
                client = Client(name=name,phone=phone,insta=form.insta.data,comment=form.comment.data)
            else:
                try:
                    source_id = int(form.source.data)
                    client = Client(name=name,phone=phone,insta=form.insta.data,source_id=source_id,comment=form.comment.data)                    
                except:
                    client = Client(name=name,phone=phone,insta=form.insta.data,comment=form.comment.data)                    
                    flash('Не получилось получить id канала. Клиент будет создан без указания канала.')
            db.session.add(client)
            db.session.commit()
            flash('Клиент добавлен. Теперь можно добавить визит или бронь.')
        else:
            flash('Ошибка - клиент с таким телефоном уже есть в базе.')
        return redirect(url_for('admin.add_client'))
    return render_template('admin/add_client.html',title=title,descr=descr,form=form)


def show_source_name(source_id):#возвращает имя канала исходя из id
    s = ClientSource.query.filter(ClientSource.id == source_id).first()
    name = s.name
    return name


@bp.route('/clients',methods=['GET', 'POST'])#все клиенты
@login_required
def clients():
    title = 'Список клиентов'
    descr = 'Для поиска клиента воспользуйтесь формой поиска. Чтобы посмотреть детальную информацию по клиенту, нажмите на его имя.'
    form = ClientSearchForm()
    clients = Client.query.order_by(Client.timestamp.desc()).all()
    client_found = False
    client_by_phone = None
    if form.validate_on_submit():
        try:
            client_by_phone = Client.query.filter(Client.phone == form.phone.data).first()
            if client_by_phone is not None:
                client_found = True                
            else:                
                flash('Клиент с данным номером не найден в базе.')
        except:
            flash('Не удалось выполнить поиск.')    
    return render_template('admin/clients.html',title=title,descr=descr,clients=clients, \
                    show_source_name=show_source_name,form=form,\
                    client_by_phone=client_by_phone,client_found=client_found)


@bp.route('/client_info/<client_id>')#информация по клиенту
@login_required
def client_info(client_id=None):
    title = 'Информация по клиенту'
    descr = 'Подробная информация по клиенту - брони, визиты'
    show_visits = False
    show_bookings = False
    total_stat = None
    client = Client.query.filter(Client.id == client_id).first()
    visits = Visit.query.filter(Visit.client_id == client_id) \
                        .filter(Visit.end != None) \
                        .order_by(Visit.begin).all()                        
    if visits is not None and len(visits)>0:
        show_visits = True
        total_stat, stat_per_day, stat_per_client = compute_stat(visits)
    bookings = Booking.query.filter(Booking.client_id == client_id) \
                        .order_by(Booking.begin).all()
    if bookings is not None and len(bookings)>0:
        show_bookings = True                        
    return render_template('admin/client_info.html',title=title,descr=descr,client=client,\
                            show_visits=show_visits,visits=visits,show_source_name=show_source_name, \
                            show_bookings=show_bookings,bookings=bookings,total_stat=total_stat)


@bp.route('/add_visit_booking',methods=['GET', 'POST'])#список клиентов для добавления визита или брони
@login_required
def add_visit_booking():
    title='Добавить визит или бронь'
    descr = 'Перед добавлением визита / брони клиента нужно создать, после чего клиента можно выбрать из списка ниже. Если нужного клиента нет, воспользуйтесь формой поиска.'
    form = ClientSearchForm()
    client_by_phone = None
    client_found = False
    page = request.args.get('page',1,type=int)
    clients = Client.query \
            .order_by(Client.timestamp.desc()) \
            .paginate(page,current_app.config['PAGINATION_ITEMS_PER_PAGE'],False)
    next_url = url_for('admin.add_visit_booking',page=clients.next_num) if clients.has_next else None
    prev_url = url_for('admin.add_visit_booking',page=clients.prev_num) if clients.has_prev else None            
    if form.validate_on_submit():
        try:
            client_by_phone = Client.query.filter(Client.phone == form.phone.data).first()            
            if client_by_phone is not None:
                client_found = True
                flash('Клиент найден!')
            else:                
                flash('Клиент с данным номером не найден в базе. Его нужно создать.')
        except:
            flash('Не удалось выполнить поиск.')
    return render_template('admin/add_visit_booking.html',title=title,descr=descr,clients=clients.items,\
                    form=form,client_found=client_found,client_by_phone=client_by_phone, \
                    next_url=next_url,prev_url=prev_url)


@bp.route('/add_visit/<client_id>',methods=['GET', 'POST'])#добавляем визит
@login_required
def add_visit_for_client(client_id = None):
    title='Добавить визит'
    client = Client.query.filter(Client.id == client_id).first()
    descr = 'Добавление визита. Клиент: ' + client.name + ', телефон ' + str(client.phone)
    form = VisitForm()
    if form.validate_on_submit():
        #проверим, чтобы не было открытых визитов у этого клиента
        open_visits = Visit.query \
            .filter(Visit.client_id == client_id) \
            .filter(Visit.end.is_(None)).all()
        if open_visits is not None and len(open_visits)>0:
            has_open_visits = True
        else:
            has_open_visits = False
        if not has_open_visits:
            if form.promo_id.data == 'not_set':#промоакция не указана
                visit = Visit(client_id=client_id,comment=form.comment.data)
            else:
                visit = Visit(client_id=client_id,promo_id=form.promo_id.data,comment=form.comment.data)
            db.session.add(visit)
            db.session.commit()
            flash('Визит открыт')
            return redirect(url_for('admin.visits_today',param='today'))
        else:
            flash('У клиента есть открытые визиты. Перед добавлением нового визита их необходимо закрыть.')
            return redirect(url_for('admin.visits_today',param='all'))
    return render_template('admin/add_visit_for_client.html',title=title,descr=descr,client=client,form=form)


@bp.route('/add_booking/<client_id>',methods=['GET', 'POST'])#добавляем бронь
@login_required
def add_booking_for_client(client_id = None):
    title='Добавить бронь.'
    client = Client.query.filter(Client.id == client_id).first()
    descr = 'Добавление брони. Клиент: ' + client.name + ', телефон ' + str(client.phone)
    form = BookingForm()
    if form.validate_on_submit():
        UTC_OFFSET_TIMEDELTA = datetime.utcnow() - datetime.now()
        begin = datetime.combine(form.begin_d.data, form.begin_t.data) + UTC_OFFSET_TIMEDELTA
        end = datetime.combine(form.end_d.data, form.end_t.data) + UTC_OFFSET_TIMEDELTA
        booking = Booking(client_id=client_id,begin=begin,end=end,comment=form.comment.data)
        db.session.add(booking)
        db.session.commit()
        return redirect(url_for('admin.all_bookings',param='all'))
    return render_template('admin/add_booking_for_client.html',title=title,descr=descr,client=client,form=form)


def compute_amount_no_promo(begin,param):#рассчитать стоимость визита без акций
    const_admin = Const_admin.query.first()
    if param == 'standard':
        rate = const_admin.rate
    elif param == 'group_by_hours':
        rate = const_admin.group_rate
    max_amount = const_admin.max_amount
    group_max_amount = const_admin.group_max_amount
    now = datetime.utcnow()
    delta = now - begin
    days, seconds = delta.days, delta.seconds
    duration = days*24*3600 + seconds
    amount_real = rate / 3600 * duration
    amount = (amount_real // 100) * 100#округляем до 100 тг в меньшую сторону
    if param == 'standard':
        amount = min(amount, max_amount)#применяем максимальный чек
    elif param == 'group_by_hours':
        amount = min(amount, group_max_amount)
    return amount


def compute_amount(begin,promo_id):#рассчитать стоимость визита    
    if promo_id:#выбрана акция
        promo = Promo.query.filter(Promo.id == promo_id).first()
        if get_promo_type_name(promo.promo_type) in ('fix_value','group_visit'):#фиксированная цена или групповой визит
            amount = promo.value
        elif get_promo_type_name(promo.promo_type) == 'discount':#скидка
            coef = (1-promo.value / 100)
            amount = compute_amount_no_promo(begin,'standard') * coef
        elif get_promo_type_name(promo.promo_type) == 'group_visit_by_hours':#групповой - по часам
            amount = compute_amount_no_promo(begin,'group_by_hours')
    else:
        amount = compute_amount_no_promo(begin,'standard')
    return amount


def time_live(begin,now):#сколько времени клиент уже находится в заведении    
    delta = now - begin
    days, seconds = delta.days, delta.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    res = str(hours)+' ч. '+str(minutes)+' м.'
    return res


def get_promo_name(promo_id):
    promos = Promo.query.with_entities(Promo.id,Promo.name).all()
    for p in promos:
        if p.id == promo_id:
            res = p.name
    return res


@bp.route('/visits_today/<param>')#визиты
@login_required
def visits_today(param=None):
    descr = None
    if param is None:
        param = 'today'
    title = 'Сейчас в коворкинге'    
    tomor_date = datetime.utcnow().date() + timedelta(days=1)
    yest_date = datetime.utcnow().date()
    visits = None
    if param == 'all':#все визиты
        descr = 'Все визиты'
        visits = Visit.query.join(Client) \
                .with_entities(Client.name,Client.phone,Visit.id,Visit.client_id,Visit.begin,Visit.end,Visit.comment,Visit.amount,Visit.promo_id) \
                .order_by(Visit.begin.desc()).all()
    elif param == 'today':#сегодняшние
        descr = 'Сегодняшние визиты'
        visits = Visit.query.join(Client) \
                .with_entities(Client.name,Client.phone,Visit.id,Visit.client_id,Visit.begin,Visit.end,Visit.comment,Visit.amount,Visit.promo_id) \
                .filter(Visit.begin > yest_date) \
                .filter(Visit.begin < tomor_date) \
                .order_by(Visit.begin.desc()).all()
    return render_template('admin/visits_today.html',title=title,visits=visits, \
                            time_live=time_live,compute_amount=compute_amount, \
                            get_promo_name=get_promo_name, descr=descr,param=param, \
                            get_now=datetime.utcnow)


@bp.route('/close_visit/<visit_id>')#завершить визит
@login_required
def close_visit(visit_id=None):
    visit = Visit.query.filter(Visit.id == visit_id).first()
    if visit.promo_id:
        promo = Promo.query.filter(Promo.id == visit.promo_id).first()
        if get_promo_type_name(promo.promo_type) == 'group_visit':#подтвердить стоимость группового визита
            return redirect(url_for('admin.confirm_and_close_group_visit',visit_id=visit_id,amount=promo.value))
    amount = compute_amount(visit.begin,visit.promo_id)
    visit.amount = amount
    visit.end = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin.visits_today',param='today'))


@bp.route('/confirm_and_close_group_visit/<visit_id>/<amount>',methods=['GET', 'POST'])#подтверждаем и закрываем групповой визит
@login_required
def confirm_and_close_group_visit(visit_id,amount):
    title='Подтвердить и закрыть групповой визит'
    form = ConfirmGroupVisitAmountForm()    
    visit = Visit.query.filter(Visit.id == visit_id).first()
    if request.method == 'GET':
        form.amount.data = float(amount)
    if form.validate_on_submit():
        visit.amount = form.amount.data
        visit.end = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('admin.visits_today',param='today'))
    return render_template('admin/confirm_and_close_group_visit.html', title=title, form=form)


@bp.route('/open_closed_visit/<visit_id>')#открыть завершенный по ошибке визит
@login_required
def open_closed_visit(visit_id=None):
    visit = Visit.query.filter(Visit.id == visit_id).first()    
    visit.amount = None
    visit.end = None
    db.session.commit()
    return redirect(url_for('admin.visits_today',param='today'))    


@bp.route('/all_bookings/<param>')#брони
@login_required
def all_bookings(param=None):
    if param is None:
        param = 'future'
    title = 'Список броней'
    #now_moment = datetime.utcnow()
    tomor_date = datetime.utcnow().date() + timedelta(days=1)
    yest_date = datetime.utcnow().date()
    bookings = None
    if param == 'all':#все брони
        descr = 'Все брони'
        bookings = Booking.query.join(Client) \
                    .with_entities(Client.name,Client.phone,Booking.id,Booking.client_id,Booking.begin,Booking.end,Booking.comment,Booking.attended) \
                    .order_by(Booking.begin.desc()).all()
    elif param == 'today':#сегодняшние
        descr = 'Брони на сегодня'
        bookings = Booking.query.join(Client) \
                    .with_entities(Client.name,Client.phone,Booking.id,Booking.client_id,Booking.begin,Booking.end,Booking.comment,Booking.attended) \
                    .filter(Booking.begin > yest_date) \
                    .filter(Booking.begin < tomor_date) \
                    .order_by(Booking.begin).all()
    elif param == 'future':#будущие
        descr = 'Брони на будущее'
        bookings = Booking.query.join(Client) \
                    .with_entities(Client.name,Client.phone,Booking.id,Booking.client_id,Booking.begin,Booking.end,Booking.comment,Booking.attended) \
                    .filter(Booking.begin >= g.now_moment) \
                    .order_by(Booking.begin).all()
    return render_template('admin/all_bookings.html',title=title,bookings=bookings,descr=descr)


@bp.route('/change_booking_status_positive/<booking_id>')#изменить статус брони - пришел
@login_required
def change_booking_status_positive(booking_id=None):
    booking = Booking.query.filter(Booking.id == booking_id).first()
    booking.attended = True
    db.session.commit()
    return redirect(url_for('admin.all_bookings',param='all'))


@bp.route('/change_booking_status_negative/<booking_id>')#изменить статус брони - не пришел
@login_required
def change_booking_status_negative(booking_id=None):
    booking = Booking.query.filter(Booking.id == booking_id).first()
    booking.attended = False
    db.session.commit()
    return redirect(url_for('admin.all_bookings',param='all'))


@bp.route('/change_client_info/<client_id>',methods=['GET', 'POST'])#изменить данные клиента
@login_required
def change_client_info(client_id=None):
    title = 'Изменить данные клиента'
    descr = 'Здесь можно изменить данные клиента'
    current_source = None
    form = ClientChangeForm()
    client = Client.query.filter(Client.id == client_id).first()
    if request.method == 'GET':
        form = ClientChangeForm(obj=client)
        if client.source_id is not None:
            current_source = show_source_name(client.source_id)
    if form.validate_on_submit():
        client.name = form.name.data
        client.phone = form.phone.data
        client.insta = form.insta.data
        source_id = form.source.data
        if source_id != 'not_set':
            client.source_id = source_id
        client.comment = form.comment.data
        db.session.commit()
        flash('Данные клиента изменены!')
        return redirect(url_for('admin.clients'))
    return render_template('admin/add_client.html', title=title,form=form,descr=descr,current_source=current_source)


@bp.route('/edit_booking/<booking_id>',methods=['GET', 'POST'])#изменить данные брони
@login_required
def edit_booking(booking_id=None):
    title = 'Изменить данные брони'
    descr = 'Здесь можно изменить данные брони'
    form = BookingForm()
    booking = Booking.query.filter(Booking.id == booking_id).first()
    UTC_OFFSET_TIMEDELTA = datetime.utcnow() - datetime.now()
    if request.method == 'GET':        
        form.begin_d.data = (booking.begin-UTC_OFFSET_TIMEDELTA).date()
        form.begin_t.data = (booking.begin-UTC_OFFSET_TIMEDELTA).time()
        form.end_d.data = (booking.end-UTC_OFFSET_TIMEDELTA).date()
        form.end_t.data = (booking.end-UTC_OFFSET_TIMEDELTA).time()
        form.comment.data = booking.comment
    if form.validate_on_submit():
        booking.begin = datetime.combine(form.begin_d.data, form.begin_t.data) + UTC_OFFSET_TIMEDELTA
        booking.end = datetime.combine(form.end_d.data, form.end_t.data) + UTC_OFFSET_TIMEDELTA
        booking.comment = form.comment.data
        db.session.commit()
        flash('Данные брони изменены!')
        return redirect(url_for('admin.all_bookings',param='all'))
    return render_template('admin/add_booking_for_client.html', title=title,form=form,descr=descr)


def bookings_by_status(bookings):#вспомогательная функция - статусы по броням
    count_pos = 0
    count_neg = 0
    count_undefined = 0
    for b in bookings:
        if b.attended == True:
            count_pos += 1
        elif b.attended == False:
            count_neg += 1
        else:
            count_undefined += 1
    res = list()
    total = len(bookings)
    res.append({'status':'Всего','count':total})
    res.append({'status':'Клиент пришел','count':count_pos})
    res.append({'status':'Клиент НЕ пришел','count':count_neg})
    res.append({'status':'Статус не указан','count':count_undefined})
    return res


def compute_stat(visits):#вспомогательная функция - инфо по визитам
    count = 0
    sum = 0
    dates = dict()
    clients = dict()
    for v in visits:
        count += 1
        sum += v.amount
        day = v.begin.date()
        if day in dates:
            dates[day] += 1
        else:
            dates[day] = 1
        client_id = v.client_id
        if client_id in clients:
            clients[client_id] += 1
        else:
            clients[client_id] = 1            
    total_stat = {'count':count,'sum':round(sum),'av_check':round((sum/count))}
    stat_per_day = list()
    for key,val in dates.items():
        amount = 0
        for v in visits:
            if v.begin.date() == key:
                amount += v.amount
        d = {'date':key,'count':val,'sum':round(amount)}
        stat_per_day.append(d)
    stat_per_client = list()
    for key,val in clients.items():
        amount = 0
        for v in visits:
            if v.client_id == key:
                amount += v.amount
        c = {'client_id':key,'count':val,'sum':round(amount)}
        stat_per_client.append(c)
        stat_per_client.sort(key=lambda x: x['sum'], reverse=True)#сортируем по убыванию
    return total_stat, stat_per_day, stat_per_client


@bp.route('/stat',methods=['GET', 'POST'])#статистика за заданный период
@login_required
def stat():
    title = 'Статистика визитов'
    descr = 'Статистика визитов за выбранный период. Укажите нужный период (обе даты включительно).'
    form = PeriodInputForm()
    show_stat = False
    visits = None
    total_stat = None
    stat_per_day = None
    stat_per_client = None
    bookings_stat = None
    today = datetime.utcnow()
    beg_d = datetime(today.year,today.month,1)
    end_d = today
    form.begin_d.data = beg_d
    form.end_d.data = end_d
    if form.validate_on_submit():
        begin_d = form.begin_d.data
        end_d = form.end_d.data  + timedelta(days=1)
        try:#все закрытые визиты за заданный в форме период
            visits = Visit.query \
                .filter(Visit.end != None) \
                .filter(Visit.begin >= begin_d) \
                .filter(Visit.begin < end_d) \
                .all()
            total_stat, stat_per_day, stat_per_client = compute_stat(visits)
            bookings = Booking.query \
                .filter(Booking.timestamp >= begin_d) \
                .filter(Booking.timestamp < end_d) \
                .all()
            bookings_stat = bookings_by_status(bookings)
            show_stat = True
        except:
            flash('Не могу выгрузить данные для расчета статистики')
    return render_template('admin/stat.html',title=title,form=form,descr=descr,show_stat=show_stat,\
                                        total_stat=total_stat,stat_per_day=stat_per_day, \
                                        len=len,stat_per_client=stat_per_client, \
                                        get_client_by_id=get_client_by_id, bookings_stat=bookings_stat)


@bp.route('/delete_visit/<visit_id>')#удалить визит
@login_required
@required_roles('admin')
def delete_visit(visit_id = None):
    visit = Visit.query.filter(Visit.id == visit_id).first()
    if visit is not None:
        try:
            db.session.delete(visit)
            db.session.commit()
            flash('Визит удалён')                
        except:
            flash('Не удалось удалить визит.')
            return redirect(url_for('admin.visits_today',param='all'))
    else:
        flash('Визит для удаления не найден. Возможно, он уже был удалён ранее.')
        return redirect(url_for('admin.visits_today',param='all'))
    return redirect(url_for('admin.visits_today',param='all'))


@bp.route('/edit_visit/<visit_id>',methods=['GET', 'POST'])#изменить визит
@login_required
@required_roles('admin')
def edit_visit(visit_id = None):
    form = EditVisitAmountForm()
    visit = Visit.query.filter(Visit.id == visit_id).first()
    if request.method == 'GET':
        form = EditVisitAmountForm(obj=visit)
    if form.validate_on_submit():
        if form.promo_id.data != 'not_set':
            visit.promo_id = form.promo_id.data
        visit.comment = form.comment.data
        visit.amount = form.amount.data
        db.session.commit()        
        flash('Визит успешно изменен!')
        return redirect(url_for('admin.visits_today',param='all'))        
    return render_template('admin/edit_visit.html', form=form)


@bp.route('/delete_booking/<booking_id>')#удалить бронь
@login_required
@required_roles('admin')
def delete_booking(booking_id = None):
    booking = Booking.query.filter(Booking.id == booking_id).first()
    if booking is not None:
        try:
            db.session.delete(booking)
            db.session.commit()
            flash('Бронь удалёна')                
        except:
            flash('Не удалось удалить бронь.')
            return redirect(url_for('admin.all_bookings',param='all'))
    else:
        flash('Бронь для удаления не найдена. Возможно, она уже была удалена ранее.')
        return redirect(url_for('admin.all_bookings',param='all'))
    return redirect(url_for('admin.all_bookings',param='all'))


@bp.route('/video_category',methods=['GET','POST'])#список категорий видео
@login_required
@required_roles('admin')
def video_category():
    title='Категории видео'
    descr = 'Здесь изменяется список оборудования в коворкинге'
    form = VideoCategoryForm()
    items = VideoCategory.query.all()
    if form.validate_on_submit():
        num = form.num.data
        try:
            item_num_already_in_DB = VideoCategory.query.filter(VideoCategory.num == num).first()            
        except:
            pass
        name = form.name.data
        try:
            item_name_already_in_DB = VideoCategory.query.filter(VideoCategory.name == name).first()            
        except:
            pass            
        if item_num_already_in_DB is None and item_name_already_in_DB is None:
            item = VideoCategory(num=num,name=name,active=form.active.data)        
            db.session.add(item)
            db.session.commit()
            flash('Добавлено!')
        else:
            flash('Ошибка - категория с таким порядковым номером или названием уже есть в базе. Выберите другой номер / название!')
        return redirect(url_for('admin.video_category'))
    return render_template('admin/video_category.html',title=title,descr=descr,form=form,items=items)


@bp.route('/edit_video_category/<item_id>',methods=['GET', 'POST'])#предменты в коворкинге (списком на главной)
@login_required
@required_roles('admin')
def edit_video_category(item_id = None):
    title='Категории видео'
    form = VideoCategoryForm()
    descr = 'Здесь изменяется список категорий видео мастер-классов'
    item = VideoCategory.query.filter(VideoCategory.id == item_id).first()
    if request.method == 'GET':
        form = VideoCategoryForm(obj=item)
    if form.validate_on_submit():
        item.num = form.num.data
        item.name = form.name.data
        item.active = form.active.data
        db.session.commit()
        flash('Значения изменены!')
        return redirect(url_for('admin.video_category'))
    return render_template('admin/video_category.html', title=title,form=form,descr=descr)


@bp.route('/add_video',methods=['GET','POST'])#добавить видео
@login_required
def add_video():
    title='Добавить видео мастер-класса'
    descr = 'Здесь можно добавить новое видео / фотоальбом.'
    form = VideoForm()
    if form.validate_on_submit():
        url = form.url.data
        try:
            url_already_in_DB = Video.query.filter(Video.url == url).first()
        except:
            pass
        v_descr = form.descr.data
        comment = form.comment.data
        active = form.active.data
        category = int(form.category.data)
        if url_already_in_DB is None:
            v_type = get_video_type_id(form.v_type.data)
            if form.v_type.data == 'photo':#фото - создадим папку с безопасным именем
                url = cyrtranslit.to_latin(url,'ru')#to latin
                url = secure_filename(url)#secure folder name
                photo_album_already_in_DB = Video.query.filter(Video.url == url).first()
                if photo_album_already_in_DB is None:
                    new_folder_for_photo_album = os.path.join(current_app.config['UPLOAD_FOLDER'], current_app.config['PHOTO_ALBUMS_FOLDER'], url)
                    if not os.path.exists(new_folder_for_photo_album):
                        os.makedirs(new_folder_for_photo_album)#создаем папку для фото альбома
                    if form.photos.data:                        
                        for f in form.photos.data:                            
                            fname = secure_filename(f.filename)
                            fname = add_str_timestamp(fname)
                            f.save(os.path.join(new_folder_for_photo_album,fname))
                            photo_type = 'photoalbum'
                            photo = Photo(name=fname,photo_type=photo_type,photoalbum=url,active=True,caption=v_descr,descr=comment)
                            db.session.add(photo)
                else:
                    flash('Ошибка - фотоальбом с таким названием уже есть в базе')
                    return redirect(url_for('admin.add_video'))            
            video = Video(url=url,descr=v_descr,v_type=v_type,comment=comment,active=active,category_id=category)
            db.session.add(video)
            db.session.commit()
            flash('Мастер-класс добавлен.')
        else:
            flash('Ошибка - видео с такой ссылкой / альбом с таким названием уже есть в базе.')
            return redirect(url_for('admin.add_video'))
        return redirect(url_for('admin.add_video'))
    return render_template('admin/add_video.html',title=title,descr=descr,form=form)


@bp.route('/edit_video/<video_id>',methods=['GET', 'POST'])#изменить данные клиента
@login_required
def edit_video(video_id=None):
    title = 'Изменить видео'
    descr = 'Здесь можно изменить видео / фотоальбом. При изменении фотоальбома не меняется название альбома для системы и сами фото.'    
    form = VideoForm()
    video = Video.query.filter(Video.id == video_id).first()
    if request.method == 'GET':
        form = VideoForm(obj=video)
    if form.validate_on_submit():
        video.v_type = get_video_type_id(form.v_type.data)
        if form.v_type.data != 'photo':
            video.url = form.url.data
        video.descr = form.descr.data
        video.comment = form.comment.data
        video.active = form.active.data
        video.category_id = form.category.data
        db.session.commit()
        flash('Данные видео изменены!')
        return redirect(url_for('admin.video_list'))
    return render_template('admin/add_video.html',title=title,form=form,descr=descr)


def show_video_cat_name(cat_id):#возвращает имя канала исходя из id
    s = VideoCategory.query.filter(VideoCategory.id == cat_id).first()
    name = s.name
    return name

v_types = current_app.config['V_TYPES']#типы мастер=классов (для системы)
v_types_str = current_app.config['V_TYPES_STR']#типы мастер=классов (для отображения)


def get_video_type_id(video_name):#получаем id типа мастер-класса исходя из выбранного в форме
    res = v_types[video_name]
    return res


def get_video_type_name(video_id):#получаем имя типа мастер-класса исходя из выбранного в форме
    return get_video_type_name_u(video_id)


@bp.route('/video_list')#все видео мастер классов
@login_required
def video_list():
    title = 'Список мастер-классов'
    descr = 'Список всех мастер-классов (видео youtube и фотоальбомов)'
    videos = Video.query.order_by(Video.timestamp.desc()).all()
    return render_template('admin/video_list.html',title=title,descr=descr,videos=videos, \
                show_video_cat_name=show_video_cat_name,get_video_type_name=get_video_type_name)


@bp.route('/video_per_category/<cat_id>')#все видео мастер классов в данной категории
@login_required
def video_per_category(cat_id = None):
    videos = None    
    try:
        videos = Video.query \
            .filter(Video.category_id == cat_id) \
            .order_by(Video.timestamp.desc()).all()
    except:
        flash('Не могу получить список видео данной категории')
        pass
    title = 'Список видео категории ' + show_video_cat_name(cat_id)
    descr = 'Список всех видео мастер-классов в категории ' + show_video_cat_name(cat_id)
    return render_template('admin/video_list.html',title=title,descr=descr,videos=videos, \
                show_video_cat_name=show_video_cat_name)


def get_photos_for_photo_albums(album_name):#список фото для отображения в каруселе в мастер-классах
    return get_photos_for_photo_albums_u(album_name)


promo_types = current_app.config['PROMO_TYPES']#типы и id промо акций

def get_promo_type_id(promo_name):#получаем id типа акции исходя из выбранного в форме
    res = promo_types[promo_name]
    return res


def get_promo_type_name(promo_id):#получаем имя типа акции исходя из выбранного в форме
    res = None   
    for key,val in promo_types.items():
        if val==promo_id:
            res = key    
    return res    


@bp.route('/edit_promo/<_id>',methods=['GET', 'POST'])#изменить промоакцию
@login_required
@required_roles('admin')
def edit_promo(_id):
    title = 'Редактирование промоакции'
    form = PromoForm()    
    descr = 'Здесь можно изменить промоакцию'
    promo = Promo.query.filter(Promo.id == _id).first()
    if request.method == 'GET':
        form = PromoForm(obj=promo)
    if form.validate_on_submit():
        promo_type = get_promo_type_id(form.promo_type.data)
        promo.name = form.name.data
        promo.promo_type = promo_type
        promo.value = form.value.data
        promo.active=form.active.data
        db.session.commit()        
        flash('Промоакция успешно изменена!')
        return redirect(url_for('admin.promo_list'))
    return render_template('admin/edit_promo.html', title=title,form=form,descr=descr)


@bp.route('/add_promo',methods=['GET','POST'])#добавить промоакцию
@login_required
@required_roles('admin')
def add_promo():
    title='Добавить акцию'
    descr = 'Здесь можно добавить акцию'
    form = PromoForm()
    if form.validate_on_submit():
        promo_type = get_promo_type_id(form.promo_type.data)
        promo = Promo(name=form.name.data,promo_type=promo_type,value=form.value.data,active=form.active.data)
        db.session.add(promo)
        db.session.commit()
        flash('Акция добавлена.')
        return redirect(url_for('admin.add_promo'))
    return render_template('admin/add_promo.html',title=title,descr=descr,form=form)


@bp.route('/promo_list')#список акций
@login_required
def promo_list():
    title = 'Список акций'
    promos = Promo.query.all()
    return render_template('admin/promo_list.html',title=title, \
                    promos=promos,get_promo_type_name=get_promo_type_name)


@bp.route('/all_questions')#список вопросов
@login_required
def all_questions():
    title = 'Список вопросов с сайта'
    questions = QuestionFromSite.query \
                .order_by(QuestionFromSite.timestamp.desc()).all()
    return render_template('admin/all_questions.html',title=title,questions=questions)


@bp.route('/question/<q_id>')#просмотр вопроса с сайта
@login_required
def question(q_id):
    title = 'Вопрос ' + str(q_id)
    question = QuestionFromSite.query \
                .filter(QuestionFromSite.id == int(q_id)).first()
    return render_template('admin/question.html',title=title,question=question)

