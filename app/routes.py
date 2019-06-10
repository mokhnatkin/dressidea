from app import app, db
from flask import render_template, flash, redirect, url_for, request, g, send_file, send_from_directory
from app.forms import LoginForm, RegistrationForm, PhotoUploadForm, Const_adminForm, \
                        Const_publicForm, PhotoEditForm, ItemInsideForm, ClientSourceForm, \
                        ClientForm, VisitForm, BookingForm, ClientSearchForm, ClientChangeForm, \
                        PeriodInputForm, VideoCategoryForm, VideoForm
from app.models import User, Const_public, Photo, Const_admin, ItemInside, ClientSource, \
                        Client, Visit, Booking, Video, VideoCategory
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from datetime import timedelta
from flask_babel import get_locale
import os
from functools import wraps
from sqlalchemy import func


@app.before_request
def before_request():
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
    

#A function defintion which will work as a decorator for each view – we can call this with @required_roles
def required_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if get_current_user_role() not in roles:
                flash('У вашей роли недостаточно полномочий','error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper
 

def get_current_user_role():#возвращает роль текущего пользователя
    return current_user.role
    

@app.route('/')
@app.route('/index')
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
    return render_template('index.html',title=title, carousel_photos=carousel_photos, carousel_photos_len=carousel_photos_len, \
                        show_carousel=show_carousel, rate = rate, max_amount = max_amount, items = items, \
                        meta_description = meta_description, meta_keywords=meta_keywords)


@app.route('/login',methods=['GET','POST'])#вход
def login():
    title = 'Вход'
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неправильный логин или пароль')
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('const_public')
        return redirect(next_page)
    return render_template('login.html',title=title,form=form)


@app.route('/logout')#выход
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register',methods=['GET','POST'])#регистрация
@login_required
@required_roles('admin')
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь добавлен!')
        return redirect(url_for('login'))
    return render_template('register.html',title='Регистрация',form=form)


def add_str_timestamp(filename):#adds string timestamp to filename in order to make in unique
    dt = datetime.utcnow()
    stamp = round(dt.timestamp())
    uId = str(stamp)
    u_filename = uId+'_'+filename
    return u_filename


@app.route('/upload_file',methods=['GET', 'POST'])#загрузить фото
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
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        photo = Photo(name=filename,photo_type=form.photo_type.data,active=form.active.data,caption=form.caption.data,descr=form.descr.data)
        db.session.add(photo)
        db.session.commit()
        flash('Фото успешно загружено!')
        return redirect(url_for('upload_file'))
    return render_template('upload_file.html', title=title,form=form,descr=descr)


@app.route('/delete_file/<fid>')#физически удалить фото
@login_required
@required_roles('admin')
def delete_file(fid = None):
    photo = Photo.query.filter(Photo.id == fid).first()
    if photo is not None:
        if photo.active:
            flash('Нельзя удалить фото, которое отображается на сайте. Сначала его нужно скрыть.')
            return redirect(url_for('files'))
        else:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo.name))
                db.session.delete(photo)
                db.session.commit()
                flash('Фото удалено с сервера')                
            except:
                flash('Не удалось выполнить физическое удаление фото с сервера. Файл не найден.')
                return redirect(url_for('files'))
    else:
        flash('Фото для удаления не найдено')
        return redirect(url_for('files'))
    return redirect(url_for('files'))


@app.route('/edit_file/<fid>',methods=['GET', 'POST'])#изменить фото
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
        return redirect(url_for('files'))
    return render_template('edit_file.html', title=title,form=form,descr=descr)


@app.route('/files')#список загруженных файлов
@login_required
@required_roles('admin')
def files():
    files = Photo.query.all()
    return render_template('files.html',files=files)


@app.route('/gallery')#список загруженных файлов
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
    return render_template('gallery.html',title=title,const_public=const_public, \
                        gallery_photos=gallery_photos,gallery_photos_len=gallery_photos_len, \
                        show_photos=show_photos, meta_description=meta_description,meta_keywords=meta_keywords)


@app.route('/files/<fname>')#файл для скачивания на комп
@login_required
@required_roles('admin')
def downloadFile(fname = None):
    p = os.path.join(os.path.dirname(os.path.abspath(app.config['UPLOAD_FOLDER'])),app.config['UPLOAD_FOLDER'],fname)
    return send_file(p, as_attachment=True)


@app.route('/get_path_to_static/<fname>')#путь к директории с фото, для отображения фото
def get_path_to_static(fname = None):
    p = os.path.join(os.path.dirname(os.path.abspath(app.config['UPLOAD_FOLDER'])),app.config['UPLOAD_FOLDER'],fname)
    return send_file(p)


@app.route('/activate_files/<fid>')#активировать фото для отображения на сайте
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
    return redirect(url_for('files'))


@app.route('/deactivate_files/<fid>')#активировать фото для отображения на сайте
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
    return redirect(url_for('files'))


@app.route('/const_admin',methods=['GET', 'POST'])#константы для админки
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
            const_set.google_analytics_tracking_id = form.google_analytics_tracking_id.data
        else:
            const = Const_admin(rate=form.rate.data,max_amount=form.max_amount.data,google_analytics_tracking_id=form.google_analytics_tracking_id.data)
            db.session.add(const)
        db.session.commit()
        flash('Значения констант изменены!')
        return redirect(url_for('const_admin'))
    return render_template('const_admin.html', title=title,form=form,descr=descr)


@app.route('/const_public',methods=['GET', 'POST'])#константы для паблика
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
        return redirect(url_for('const_public'))
    return render_template('const_public.html', title=title,form=form,descr=descr)


@app.route('/users')#список пользователей
@login_required
@required_roles('admin')
def users():
    title = 'Список пользователей'
    users = User.query.all()
    return render_template('users.html', title=title, users=users)


@app.route('/give_admin_role/<uid>')#присвоить пользователю роль admin
@login_required
@required_roles('admin')
def give_admin_role(uid = None):
    u = User.query.filter(User.id == uid).first()    
    try:
        u.role = 'admin'
        db.session.commit()        
    except:
        flash('Не удалось сменить роль')
    return redirect(url_for('users'))


@app.route('/give_user_role/<uid>')#присвоить пользователю роль user
@login_required
@required_roles('admin')
def give_user_role(uid = None):
    u = User.query.filter(User.id == uid).first()    
    try:
        u.role = 'user'
        db.session.commit()        
    except:
        flash('Не удалось сменить роль')
    return redirect(url_for('users'))


@app.route('/edit_item_inside/<item_id>',methods=['GET', 'POST'])#предменты в коворкинге (списком на главной)
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
        return redirect(url_for('item_inside'))
    return render_template('item_inside.html', title=title,form=form,descr=descr)


@app.route('/item_inside',methods=['GET','POST'])#дополнить список оборудования
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
        return redirect(url_for('item_inside'))
    return render_template('item_inside.html',title=title,descr=descr,form=form,items=items)


@app.route('/admin')#админка - общее описание
@login_required
def admin():    
    return render_template('admin.html',title='Админка')


@app.route('/sources',methods=['GET','POST'])#дополнить список источников
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
        return redirect(url_for('sources'))
    return render_template('sources.html',title=title,descr=descr,form=form,items=items)


@app.route('/edit_source/<item_id>',methods=['GET', 'POST'])#редактируем источники
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
        return redirect(url_for('sources'))
    return render_template('sources.html', title=title,form=form,descr=descr)


@app.route('/add_client',methods=['GET','POST'])#добавить клиента
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
                    db.session.add(client)
                except:
                    client = Client(name=name,phone=phone,insta=form.insta.data,comment=form.comment.data)
                    db.session.add(client)
                    flash('Не получилось получить id канала. Клиент будет создан без указания канала.')            
            db.session.commit()
            flash('Клиент добавлен. Теперь можно добавить визит или бронь.')
        else:
            flash('Ошибка - клиент с таким телефоном уже есть в базе.')
        return redirect(url_for('add_client'))
    return render_template('add_client.html',title=title,descr=descr,form=form)


def show_source_name(source_id):#возвращает имя канала исходя из id
    s = ClientSource.query.filter(ClientSource.id == source_id).first()
    name = s.name
    return name


@app.route('/clients',methods=['GET', 'POST'])#все клиенты
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
    return render_template('clients.html',title=title,descr=descr,clients=clients, \
                    show_source_name=show_source_name,form=form,\
                    client_by_phone=client_by_phone,client_found=client_found)


@app.route('/client_info/<client_id>')#информация по клиенту
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
        total_stat, stat_per_day = compute_stat(visits)
    bookings = Booking.query.filter(Booking.client_id == client_id) \
                        .order_by(Booking.begin).all()
    if bookings is not None and len(bookings)>0:
        show_bookings = True                        
    return render_template('client_info.html',title=title,descr=descr,client=client,\
                            show_visits=show_visits,visits=visits,show_source_name=show_source_name, \
                            show_bookings=show_bookings,bookings=bookings,total_stat=total_stat)


@app.route('/add_visit_booking',methods=['GET', 'POST'])#список клиентов для добавления визита или брони
@login_required
def add_visit_booking():
    title='Добавить визит или бронь'
    descr = 'Перед добавлением визита / брони клиента нужно создать, после чего клиента можно выбрать из списка ниже. Если нужного клиента нет, воспользуйтесь формой поиска.'
    form = ClientSearchForm()
    client_by_phone = None
    client_found = False
    clients = Client.query.order_by(Client.timestamp.desc()).limit(10).all()
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
    return render_template('add_visit_booking.html',title=title,descr=descr,clients=clients,\
                    form=form,client_found=client_found,client_by_phone=client_by_phone)


@app.route('/add_visit/<client_id>',methods=['GET', 'POST'])#добавляем визит
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
            visit = Visit(client_id=client_id,comment=form.comment.data)
            db.session.add(visit)
            db.session.commit()
            return redirect(url_for('visits_today',param='today'))
        else:
            flash('У клиента есть открытые визиты. Перед добавлением нового визита их необходимо закрыть.')
            return redirect(url_for('visits_today',param='all'))
    return render_template('add_visit_for_client.html',title=title,descr=descr,client=client,form=form)


@app.route('/add_booking/<client_id>',methods=['GET', 'POST'])#добавляем бронь
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
        return redirect(url_for('all_bookings',param='all'))
    return render_template('add_booking_for_client.html',title=title,descr=descr,client=client,form=form)


def compute_amount(begin):#рассчитать стоимость визита
    const_admin = Const_admin.query.first()
    rate = const_admin.rate    
    max_amount = const_admin.max_amount
    now = datetime.utcnow()
    delta = now - begin
    days, seconds = delta.days, delta.seconds
    duration = days*24*3600 + seconds
    amount_real = rate / 3600 * duration
    amount = (amount_real // 100) * 100#округляем до 100 тг в меньшую сторону
    amount = min(amount, max_amount)#применяем максимальный чек
    return amount


def time_live(begin):#сколько времени клиент уже находится в заведении
    now = datetime.utcnow()
    delta = now - begin
    days, seconds = delta.days, delta.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    res = str(hours)+' ч. '+str(minutes)+' м.'
    return res


@app.route('/visits_today/<param>')#визиты
@login_required
def visits_today(param=None):
    if param is None:
        param = 'today'
    title = 'Сейчас в коворкинге'
    #now_moment = datetime.utcnow()
    tomor_date = datetime.utcnow().date() + timedelta(days=1)
    yest_date = datetime.utcnow().date()
    visits = None
    if param == 'all':#все визиты
        descr = 'Все визиты'
        visits = Visit.query.join(Client) \
                .with_entities(Client.name,Client.phone,Visit.id,Visit.client_id,Visit.begin,Visit.end,Visit.comment,Visit.amount) \
                .order_by(Visit.begin.desc()).all()
    elif param == 'today':#сегодняшние
        descr = 'Сегодняшние визиты'
        visits = Visit.query.join(Client) \
                .with_entities(Client.name,Client.phone,Visit.id,Visit.client_id,Visit.begin,Visit.end,Visit.comment,Visit.amount) \
                .filter(Visit.begin > yest_date) \
                .filter(Visit.begin < tomor_date) \
                .order_by(Visit.begin.desc()).all()
    return render_template('visits_today.html',title=title,visits=visits, \
                            time_live=time_live,compute_amount=compute_amount,descr=descr,param=param)


@app.route('/close_visit/<visit_id>')#завершить визит
@login_required
def close_visit(visit_id=None):
    visit = Visit.query.filter(Visit.id == visit_id).first()
    amount = compute_amount(visit.begin)
    visit.amount = amount
    visit.end = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('visits_today',param='today'))


@app.route('/open_closed_visit/<visit_id>')#открыть завершенный по ошибке визит
@login_required
def open_closed_visit(visit_id=None):
    visit = Visit.query.filter(Visit.id == visit_id).first()    
    visit.amount = None
    visit.end = None
    db.session.commit()
    return redirect(url_for('visits_today',param='today'))    


@app.route('/all_bookings/<param>')#брони
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
    return render_template('all_bookings.html',title=title,bookings=bookings,descr=descr)


@app.route('/change_booking_status_positive/<booking_id>')#изменить статус брони - пришел
@login_required
def change_booking_status_positive(booking_id=None):
    booking = Booking.query.filter(Booking.id == booking_id).first()
    booking.attended = True
    db.session.commit()
    return redirect(url_for('all_bookings',param='all'))


@app.route('/change_booking_status_negative/<booking_id>')#изменить статус брони - не пришел
@login_required
def change_booking_status_negative(booking_id=None):
    booking = Booking.query.filter(Booking.id == booking_id).first()
    booking.attended = False
    db.session.commit()
    return redirect(url_for('all_bookings',param='all'))


@app.route('/change_client_info/<client_id>',methods=['GET', 'POST'])#изменить данные клиента
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
        return redirect(url_for('clients'))
    return render_template('add_client.html', title=title,form=form,descr=descr,current_source=current_source)


@app.route('/edit_booking/<booking_id>',methods=['GET', 'POST'])#изменить данные брони
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
        return redirect(url_for('all_bookings',param='all'))
    return render_template('add_booking_for_client.html', title=title,form=form,descr=descr)


@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():#отдает файлы robots.txt и sitemap.xml для поисковых машин
    return get_path_to_static(request.path[1:])

def compute_stat(visits):
    count = 0
    sum = 0
    dates = dict()
    for v in visits:
        count += 1
        sum += v.amount
        day = v.begin.date()
        if day in dates:
            dates[day] += 1
        else:
            dates[day] = 1
    total_stat = {'count':count,'sum':round(sum)}
    stat_per_day = list()
    for key,val in dates.items():
        amount = 0
        for v in visits:
            if v.begin.date() == key:
                amount += v.amount
        d = {'date':key,'count':val,'sum':round(amount)}
        stat_per_day.append(d)    
    return total_stat, stat_per_day


@app.route('/stat',methods=['GET', 'POST'])#статистика за заданный период
@login_required
def stat():
    title = 'Статистика визитов'
    descr = 'Статистика визитов за выбранный период. Укажите нужный период (обе даты включительно).'
    form = PeriodInputForm()
    show_stat = False
    visits = None
    total_stat = None
    stat_per_day = None
    stat_per_day_len = None
    if form.validate_on_submit():
        begin_d = form.begin_d.data
        end_d = form.end_d.data  + timedelta(days=1)
        try:#все закрытые визиты за заданный в форме период
            visits = Visit.query \
                .filter(Visit.end != None) \
                .filter(Visit.begin >= begin_d) \
                .filter(Visit.begin < end_d) \
                .all()
            total_stat, stat_per_day = compute_stat(visits)
            stat_per_day_len = len(stat_per_day)
            show_stat = True
        except:
            flash('Не могу выгрузить данные для расчета статистики')
    return render_template('stat.html',title=title,form=form,descr=descr,show_stat=show_stat,\
                                        total_stat=total_stat,stat_per_day=stat_per_day,stat_per_day_len=stat_per_day_len)


@app.route('/delete_visit/<visit_id>')#удалить визит
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
            return redirect(url_for('visits_today',param='all'))
    else:
        flash('Визит для удаления не найден. Возможно, он уже был удалён ранее.')
        return redirect(url_for('visits_today',param='all'))
    return redirect(url_for('visits_today',param='all'))


@app.route('/delete_booking/<booking_id>')#удалить бронь
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
            return redirect(url_for('all_bookings',param='all'))
    else:
        flash('Бронь для удаления не найдена. Возможно, она уже была удалена ранее.')
        return redirect(url_for('all_bookings',param='all'))
    return redirect(url_for('all_bookings',param='all'))


@app.route('/about')#о проекте
def about():#главная страница
    title = 'Швейный коворкинг, город Алматы, о проекте'
    meta_description = 'Место для любителей шитья, город Алматы. О проекте, история'
    meta_keywords = 'Швейный коворкинг, швейное оборудование, Алматы, о проекте'    
    return render_template('about.html',title=title, meta_description = meta_description, \
                            meta_keywords=meta_keywords)


@app.route('/video_category',methods=['GET','POST'])#список категорий видео
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
        return redirect(url_for('video_category'))
    return render_template('video_category.html',title=title,descr=descr,form=form,items=items)


@app.route('/edit_video_category/<item_id>',methods=['GET', 'POST'])#предменты в коворкинге (списком на главной)
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
        return redirect(url_for('video_category'))
    return render_template('video_category.html', title=title,form=form,descr=descr)


@app.route('/add_video',methods=['GET','POST'])#добавить видео
@login_required
def add_video():
    title='Добавить видео мастер-класса'
    descr = 'Здесь можно добавить новое видео'
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
            video = Video(url=url,descr=v_descr,comment=comment,active=active,category_id=category)
            db.session.add(video)
            db.session.commit()
            flash('Видео добавлено.')
        else:
            flash('Ошибка - видео с такой ссылкой уже есть в базе.')
        return redirect(url_for('add_video'))
    return render_template('add_video.html',title=title,descr=descr,form=form)


@app.route('/edit_video/<video_id>',methods=['GET', 'POST'])#изменить данные клиента
@login_required
def edit_video(video_id=None):
    title = 'Изменить видео'
    descr = 'Здесь можно изменить видео'    
    form = VideoForm()
    video = Video.query.filter(Video.id == video_id).first()
    if request.method == 'GET':
        form = VideoForm(obj=video)
    if form.validate_on_submit():
        video.url = form.url.data
        video.descr = form.descr.data
        video.comment = form.comment.data
        video.active = form.active.data
        video.category_id = form.category.data        
        db.session.commit()
        flash('Данные видео изменены!')
        return redirect(url_for('video_list'))
    return render_template('add_video.html',title=title,form=form,descr=descr)


def show_video_cat_name(cat_id):#возвращает имя канала исходя из id
    s = VideoCategory.query.filter(VideoCategory.id == cat_id).first()
    name = s.name
    return name

@app.route('/video_list')#все видео мастер классов
@login_required
def video_list():
    title = 'Список видео'
    descr = 'Список всех видео мастер-классов'
    videos = Video.query.order_by(Video.timestamp.desc()).all()
    return render_template('video_list.html',title=title,descr=descr,videos=videos, \
                show_video_cat_name=show_video_cat_name)


@app.route('/video_per_category/<cat_id>')#все видео мастер классов в данной категории
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
    return render_template('video_list.html',title=title,descr=descr,videos=videos, \
                show_video_cat_name=show_video_cat_name)


@app.route('/video')#видео мастер-классов
def video():#главная страница
    title = 'Швейный коворкинг, город Алматы, мастер-классы'
    meta_description = 'Место для любителей шитья, город Алматы. Мастер классы'
    meta_keywords = 'Швейный коворкинг, швейное оборудование, Алматы, мастер классы'
    #все активные категории, где есть видео
    categories = VideoCategory.query.join(Video) \
                .filter(VideoCategory.active == True) \
                .order_by(VideoCategory.num).all()
    videos = VideoCategory.query.join(Video) \
                    .with_entities(VideoCategory.id,Video.descr,Video.comment,Video.url,Video.timestamp) \
                    .filter(VideoCategory.active == True) \
                    .filter(Video.active == True) \
                    .order_by(VideoCategory.num) \
                    .order_by(Video.timestamp.desc()).all()
    return render_template('video.html',title=title, meta_description = meta_description, \
                            meta_keywords=meta_keywords, videos=videos, categories=categories)
                            