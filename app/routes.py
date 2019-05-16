from app import app, db
from flask import render_template, flash, redirect, url_for, request, g, send_file
from app.forms import LoginForm, RegistrationForm, PhotoUploadForm, Const_adminForm, \
                        Const_publicForm, PhotoEditForm, ItemInsideForm, ClientSourceForm, \
                        ClientForm, VisitForm, BookingForm, ClientSearchForm
from app.models import User, Const_public, Photo, Const_admin, ItemInside, ClientSource, \
                        Client, Visit, Booking
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_babel import get_locale
import os
from functools import wraps


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
    title = 'Швейный коворкинг Алматы'
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
                        show_carousel=show_carousel, rate = rate, max_amount = max_amount, items = items)


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


@app.route('/edit_file/<fid>',methods=['GET', 'POST'])#изменить фото
@login_required
@required_roles('admin')
def edit_file(fid = None):
    title = 'Редактирование типа и описания фото'
    form = PhotoEditForm()    
    descr = 'Здесь можно изменить заголовок, описание или тип фото'
    photo = Photo.query.filter(Photo.id == fid).first()
    if request.method == 'GET':        
        form.photo_type.data = photo.photo_type
        form.caption.data = photo.caption
        form.descr.data = photo.descr
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
    title = 'Фото швейного коворкинга, Алматы'
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
                        show_photos=show_photos)


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
            form.rate.data = const_set.rate
            form.max_amount.data = const_set.max_amount
            form.google_analytics_tracking_id.data = const_set.google_analytics_tracking_id
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
            form.descr.data = const_set.descr
            form.working_hours.data = const_set.working_hours
            form.show_working_hours.data = const_set.show_working_hours
            form.addr.data = const_set.addr
            form.ya_map_id.data = const_set.ya_map_id
            form.ya_map_width.data = const_set.ya_map_width
            form.ya_map_height.data = const_set.ya_map_height
            form.ya_map_static.data = const_set.ya_map_static
            form.phone.data = const_set.phone
            form.insta.data = const_set.insta
            form.insta_url.data = const_set.insta_url
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
        form.num.data = item.num
        form.name.data = item.name
        form.active.data = item.active
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
        form.name.data = item.name
        form.active.data = item.active
    if form.validate_on_submit():
        item.name = form.name.data
        item.active = form.active.data
        db.session.commit()
        flash('Значения изменены!')
        return redirect(url_for('sources'))
    return render_template('sources.html', title=title,form=form,descr=descr)


@app.route('/add_client',methods=['GET','POST'])#дополнить список источников
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
        source_id=form.source.data
        name=form.name.data
        if phone_already_in_DB is None:
            if source_id == 'not_set':
                client = Client(name=name,phone=phone,insta=form.insta.data,comment=form.comment.data)                
            else:
                client = Client(name=name,phone=phone,insta=form.insta.data,source_id=source_id,comment=form.comment.data)                
            db.session.add(client)
            db.session.commit()
            flash('Клиент добавлен. Теперь можно добавить визит или бронь.')
        else:
            flash('Ошибка - клиент с таким телефоном уже есть в базе')
        return redirect(url_for('add_client'))
    return render_template('add_client.html',title=title,descr=descr,form=form)


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
            client_found = True
            flash('Клиент найден!')
        except:
            flash('Клиент с данным номером не найден в базе. Его нужно создать.')
    return render_template('add_visit_booking.html',title=title,descr=descr,clients=clients,form=form,client_found=client_found,client_by_phone=client_by_phone)


@app.route('/add_visit/<client_id>',methods=['GET', 'POST'])
@login_required
def add_visit_for_client(client_id = None):
    title='Добавить визит'
    client = Client.query.filter(Client.id == client_id).first()
    descr = 'Добавление визита. Клиент: ' + client.name + ', телефон ' + str(client.phone)
    form = VisitForm()
    if form.validate_on_submit():
        visit = Visit(client_id=client_id,comment=form.comment.data)
        db.session.add(visit)
        db.session.commit()
        return redirect(url_for('visits_today'))
    return render_template('add_visit_for_client.html',title=title,descr=descr,client=client,form=form)


@app.route('/add_booking/<client_id>',methods=['GET', 'POST'])
@login_required
def add_booking_for_client(client_id = None):
    title='Добавить бронь.'
    client = Client.query.filter(Client.id == client_id).first()
    descr = 'Добавление брони. Клиент: ' + client.name + ', телефон ' + str(client.phone)
    form = BookingForm()
    if form.validate_on_submit():
        UTC_OFFSET_TIMEDELTA = datetime.utcnow() - datetime.now()
        begin = form.begin.data + UTC_OFFSET_TIMEDELTA
        end = form.end.data + UTC_OFFSET_TIMEDELTA
        booking = Booking(client_id=client_id,begin=begin,end=end,comment=form.comment.data)
        db.session.add(booking)
        db.session.commit()
        return redirect(url_for('all_bookings'))
    return render_template('add_booking_for_client.html',title=title,descr=descr,client=client,form=form)


def compute_amount(begin):#рассчитать стоимость визита
    const_admin = Const_admin.query.first()
    rate = const_admin.rate
    max_amount = const_admin.max_amount
    now_moment = datetime.utcnow()
    duration = (now_moment - begin).seconds
    amount = (duration * rate) / 3600
    amount = round(min(amount, max_amount))
    return amount


@app.route('/visits_today')#визиты сегодня, коворкинг LIVE
@login_required
def visits_today():
    title = 'Сейчас в коворкинге'
    now_moment = datetime.utcnow()
    now_moment_date = now_moment.date()    
    visits = Visit.query.join(Client) \
                .with_entities(Client.name,Client.phone,Visit.id,Visit.begin,Visit.end,Visit.comment,Visit.amount) \
                .filter(Visit.begin >= now_moment_date) \
                .order_by(Visit.begin.desc()).all()
    return render_template('visits_today.html',title=title,visits=visits,now_moment=now_moment,compute_amount=compute_amount,now_moment_date=now_moment_date)


@app.route('/close_visit/<visit_id>')#завершить визит
@login_required
def close_visit(visit_id=None):
    visit = Visit.query.filter(Visit.id == visit_id).first()
    amount = compute_amount(visit.begin)
    visit.amount = amount
    visit.end = datetime.utcnow()    
    db.session.commit()    
    return redirect(url_for('visits_today'))


@app.route('/all_bookings')#все брони
@login_required
def all_bookings():
    title = 'Список броней'
    bookings = Booking.query.join(Client) \
                    .with_entities(Client.name,Client.phone,Booking.id,Booking.begin,Booking.end,Booking.comment,Booking.attended) \
                    .order_by(Booking.begin).all()
    return render_template('all_bookings.html',title=title,bookings=bookings)


@app.route('/change_booking_status_positive/<booking_id>')#изменить статус брони - пришел
@login_required
def change_booking_status_positive(booking_id=None):
    booking = Booking.query.filter(Booking.id == booking_id).first()
    booking.attended = True
    db.session.commit()
    return redirect(url_for('all_bookings'))


@app.route('/change_booking_status_negative/<booking_id>')#изменить статус брони - не пришел
@login_required
def change_booking_status_negative(booking_id=None):
    booking = Booking.query.filter(Booking.id == booking_id).first()
    booking.attended = False
    db.session.commit()
    return redirect(url_for('all_bookings'))