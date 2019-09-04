from flask_wtf import FlaskForm
from flask import current_app
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
                TextAreaField, SelectField, DecimalField, IntegerField, \
                DateTimeField, MultipleFileField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import User, ClientSource, VideoCategory, Promo, Client
from wtforms.fields.html5 import DateField, TimeField



class PhotoUploadForm(FlaskForm):#загрузить фото
    photo_types = current_app.config['PHOTO_TYPES']
    ext_for_photos = current_app.config['EXT_FOR_PHOTOS']
    photo = FileField(label='Выберите фото для загрузки',validators=[FileRequired(),FileAllowed(ext_for_photos, 'Только изображение!')])    
    photo_type = SelectField(label='Куда загрузить фото',choices = photo_types)
    caption = StringField('Заголовок')
    descr = StringField('Описание')
    active = BooleanField(label='Сразу отобразить фото на сайте')
    submit = SubmitField('Загрузить')


class PhotoEditForm(FlaskForm):#редактировать фото    
    photo_types = current_app.config['PHOTO_TYPES']
    photo_type = SelectField(label='Куда загрузить фото',choices = photo_types)
    caption = StringField('Заголовок')
    descr = StringField('Описание')    
    submit = SubmitField('Изменить')


class Const_adminForm(FlaskForm):#константы админки
    rate = DecimalField(label='Тариф за час, тг',validators=[DataRequired()])
    max_amount = DecimalField(label='Максимальный чек, тг',validators=[DataRequired()])
    group_rate = DecimalField(label='Групповой визит - тариф за час, тг',validators=[DataRequired()])
    group_max_amount = DecimalField(label='Групповой визит - макс. чек, тг',validators=[DataRequired()])
    google_analytics_tracking_id = StringField('Google Аналитика Tracking ID')
    submit = SubmitField('Изменить')


class Const_publicForm(FlaskForm):#константы паблика
    descr = TextAreaField('Текстовое описание коворкинга',validators=[DataRequired(), Length(min=1,max=1000)])
    working_hours = StringField('Режим работы',validators=[DataRequired(), Length(min=1,max=200)])
    show_working_hours = BooleanField(label='Показывать режим работы на сайте')
    addr = StringField('Адрес',validators=[DataRequired(), Length(min=1,max=500)])
    ya_map_id = StringField('ID Яндекс.Карты')
    ya_map_width = IntegerField('Ширина карты, px')
    ya_map_height = IntegerField('Высота карты, px')
    ya_map_static = BooleanField(label='Статичная карта')
    phone = StringField('Телефон',validators=[DataRequired()])
    insta = StringField('Инстаграм имя',validators=[DataRequired()])
    insta_url = StringField('URL инстаграм профиля',validators=[DataRequired()])
    submit = SubmitField('Изменить')


class ItemInsideForm(FlaskForm):#добавить предметы внутри коворкинга
    num = IntegerField(label='Номер',validators=[DataRequired()])
    name = StringField('Название',validators=[DataRequired(), Length(min=1,max=100)])
    active = BooleanField(label='Сразу отобразить на сайте')
    submit = SubmitField('Добавить / изменить')


class ClientSourceForm(FlaskForm):#добавить / изменить источники    
    name = StringField('Название',validators=[DataRequired(), Length(min=1,max=100)])
    active = BooleanField(label='Активен')
    submit = SubmitField('Добавить / изменить')


class VideoForm(FlaskForm):#добавить видео мастер класса    
    v_types = current_app.config['V_TYPES_STR']
    v_type = SelectField('Выберите вид мастер-класса',choices = v_types,validators=[DataRequired()])
    category = SelectField('Выберите категорию',choices = [],validators=[DataRequired()])    
    url = StringField('Если видео: последняя часть ссылки на видео; например, если ссылка https://www.youtube.com/watch?v=Yai9fmGJTaQ, то в этом поле нужно указать Yai9fmGJTaQ; если фото: название альбома для системы', \
        validators=[DataRequired(), Length(min=1,max=500)])
    descr = StringField('Название видео / фотоальбома для отображения на сайте',validators=[DataRequired(), Length(min=1,max=500)])
    comment = TextAreaField('Описание видео / фотоальбома',validators=[DataRequired(), Length(min=1,max=1000)])
    photos = MultipleFileField('Фото для загрузки в карусель')
    active = BooleanField(label='Отображать на сайте')
    submit = SubmitField('Добавить / изменить видео / фотоальбом')

    def __init__(self, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)        
        categories = [(str(a.id), a.name) for a in VideoCategory.query.filter(VideoCategory.active==True)]        
        self.category.choices = categories


class VideoCategoryForm(FlaskForm):#добавить / изменить категории видео
    num = IntegerField(label='Номер (порядок отображения на сайте)',validators=[DataRequired()])
    name = StringField('Название категории',validators=[DataRequired(), Length(min=1,max=200)])
    active = BooleanField(label='Отображать на сайте')
    submit = SubmitField('Добавить / изменить')


class ClientForm(FlaskForm):#добавляем клиента
    name = StringField('Имя',validators=[DataRequired(), Length(min=1,max=50)])
    phone = StringField('Мобильный телефон; образец 87017166243',validators=[DataRequired(), Length(min=11,max=11)])
    insta = StringField('Instagram; образец dressidea_coworking',validators=[Length(max=50)])
    source = SelectField('Откуда пришел клиент?',choices = [])
    comment = TextAreaField('Комментарий',validators=[Length(max=200)])
    can_place_orders = BooleanField(label='Отображать в списке при создании заказа')
    submit = SubmitField('Добавить / изменить')

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        s_1 = [('not_set','--не указано--')]
        sources_db = [(str(a.id), a.name) for a in ClientSource.query.filter(ClientSource.active==True)]
        sources = s_1 + sources_db
        self.source.choices = sources


class ClientSearchForm(FlaskForm):#ищем клиента для добавления брони / визита
    phone = StringField('Мобильный телефон; образец 87017166243')
    name = StringField('Имя')
    submit = SubmitField('Найти')


class VisitForm(FlaskForm):#добавляем визит
    promo_id = SelectField('Промоакция',choices = [])
    comment = StringField('Комментарий (необязательно)',validators=[Length(min=0,max=200)])
    submit = SubmitField('Добавить визит')

    def __init__(self, *args, **kwargs):
        super(VisitForm, self).__init__(*args, **kwargs)
        s_1 = [('not_set','--стандартный визит--')]
        promos_db = [(str(a.id), a.name) for a in Promo.query.filter(Promo.active==True)]
        promos = s_1 + promos_db
        self.promo_id.choices = promos


class BookingForm(FlaskForm):#добавляем / изменяем бронь
    begin_d = DateField('Начало, дата', format='%Y-%m-%d',validators=[DataRequired()])
    begin_t= TimeField('Начало, время', format='%H:%M',validators=[DataRequired()])
    end_d = DateField('Конец, дата', format='%Y-%m-%d',validators=[DataRequired()])
    end_t= TimeField('Конец, время', format='%H:%M',validators=[DataRequired()])
    comment = StringField('Комментарий (необязательно)',validators=[Length(min=0,max=200)])
    submit = SubmitField('Добавить / изменить бронь')


class PeriodInputForm(FlaskForm):#указать период для статистики - с по
    begin_d = DateField('Начало, дата', format='%Y-%m-%d',validators=[DataRequired()])
    end_d = DateField('Конец, дата', format='%Y-%m-%d',validators=[DataRequired()])
    submit = SubmitField('Показать')


class PromoForm(FlaskForm):#добавить промо акции
    promo_types = current_app.config['PROMO_TYPES_STR']
    name = StringField('Название акции',validators=[DataRequired(), Length(min=1,max=100)])
    promo_type = SelectField('Тип акции',choices = promo_types)
    value = DecimalField('Значение (тг. или %)',validators=[DataRequired()])
    active = BooleanField(label='Акция активна')
    submit = SubmitField('Добавить / Изменить')


class ConfirmVisitAmountForm(FlaskForm):#подтвердить стоимость визита
    amount = DecimalField('Сумма')
    submit = SubmitField('Подтвердить сумму и закрыть визит')


class EditVisitAmountForm(FlaskForm):#изменить стоимость визита
    promo_id = SelectField('Промоакция',choices = [])
    comment = StringField('Комментарий (необязательно)',validators=[Length(min=0,max=200)])
    amount = DecimalField('Сумма',validators=[DataRequired()])
    submit = SubmitField('Изменить визит')

    def __init__(self, *args, **kwargs):
        super(EditVisitAmountForm, self).__init__(*args, **kwargs)
        s_1 = [('not_set','--стандартный визит--')]
        promos_db = [(str(a.id), a.name) for a in Promo.query.filter(Promo.active==True)]
        promos = s_1 + promos_db
        self.promo_id.choices = promos


class OrderForm(FlaskForm):#добавляем заказ
    client_id = SelectField('Клиент',choices = [])
    name = StringField('Название заказа',validators=[DataRequired(),Length(min=1,max=100)])
    description = TextAreaField('Описание заказа')
    begin = DateField('Дата приёма', format='%Y-%m-%d',validators=[DataRequired()])
    submit = SubmitField('Добавить заказ')

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        s_1 = [('not_set','--выберите клиента--')]
        clients_db = [(str(a.id), a.name+', тел.'+a.phone) for a in Client.query.filter(Client.can_place_orders==True).all()]
        clients = s_1 + clients_db
        self.client_id.choices = clients
    

class EditOrderForm(FlaskForm):#меняем заказ
    statuses = current_app.config['ORDER_STATUS']
    name = StringField('Название заказа',validators=[DataRequired(),Length(min=1,max=100)])
    status = SelectField('Статус',choices = statuses)
    description = TextAreaField('Описание заказа')
    begin = DateField('Дата приёма', format='%Y-%m-%d',validators=[DataRequired()])
    end = DateField('Дата сдачи', format='%Y-%m-%d',validators=[DataRequired()])
    amount = DecimalField('Стоимость')
    submit = SubmitField('Изменить / закрыть заказ')


  