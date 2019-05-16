from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DecimalField, IntegerField
from wtforms import DateTimeField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import User, ClientSource
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import TimeField


class LoginForm(FlaskForm):#вход
    username = StringField('Логин',validators=[DataRequired()])
    password = PasswordField('Пароль',validators=[DataRequired()])
    remember_me = BooleanField('Запомни меня')
    submit = SubmitField('Вход')


class RegistrationForm(FlaskForm):#зарегистрироваться
    username = StringField('Логин',validators=[DataRequired()])
    email = StringField('E-mail',validators=[DataRequired(), Email()])
    password = PasswordField('Пароль',validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль',validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Добавить')

    def validate_username(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пользователь с таким логином уже зарегистрирован.')

    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пользователь с таким e-mail адресом уже зарегистрирован.')


class PhotoUploadForm(FlaskForm):#загрузить фото
    photo = FileField(label='Выберите фото для загрузки',validators=[FileRequired(),FileAllowed(['jpeg', 'jpg', 'png'], 'Только изображение!')])
    photo_types = [('carousel','Карусель'), ('gallery','Галерея')]#типы фото
    photo_type = SelectField(label='Куда загрузить фото',choices = photo_types)
    caption = StringField('Заголовок')
    descr = StringField('Описание')
    active = BooleanField(label='Сразу отобразить фото на сайте')
    submit = SubmitField('Загрузить')


class PhotoEditForm(FlaskForm):#редактировать фото    
    photo_types = [('carousel','Карусель'), ('gallery','Галерея')]#типы фото
    photo_type = SelectField(label='Куда загрузить фото',choices = photo_types)
    caption = StringField('Заголовок')
    descr = StringField('Описание')    
    submit = SubmitField('Изменить')    


class Const_adminForm(FlaskForm):#константы админки
    rate = DecimalField(label='Тариф за час, тг',validators=[DataRequired()])
    max_amount = DecimalField(label='Максимальный чек, тг',validators=[DataRequired()])
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


class ClientForm(FlaskForm):#добавляем клиента
    sources = ClientSource.query \
                .with_entities(ClientSource.id,ClientSource.name) \
                .filter(ClientSource.active==True).all()
    sources_str = list()
    sources_str.append(('not_set','--выберите--'))
    for s in sources:
        s_id = str(s[0])
        sources_str.append((s_id,s[1]))
    name = StringField('Имя',validators=[DataRequired(), Length(min=1,max=50)])
    phone = StringField('Мобильный телефон; образец 87017166243',validators=[DataRequired(), Length(min=11,max=11)])
    insta = StringField('Instagram; образец @dressidea_coworking',validators=[Length(max=50)])
    source = SelectField('Откуда пришел клиент?',choices = sources_str)
    comment = TextAreaField('Комментарий',validators=[Length(max=200)])
    submit = SubmitField('Добавить')


class ClientChangeForm(FlaskForm):#изменяем данные клиента
    sources = ClientSource.query.with_entities(ClientSource.id,ClientSource.name).all()
    sources_str = list()
    sources_str.append(('not_set','--выберите--'))
    for s in sources:
        s_id = str(s[0])
        sources_str.append((s_id,s[1]))
    name = StringField('Имя',validators=[DataRequired(), Length(min=1,max=50)])
    phone = StringField('Мобильный телефон; образец 87017166243',validators=[DataRequired(), Length(min=11,max=11)])
    insta = StringField('Instagram; образец @dressidea_coworking',validators=[Length(max=50)])
    source = SelectField('Откуда пришел клиент?',choices = sources_str)
    comment = TextAreaField('Комментарий',validators=[Length(max=200)])
    submit = SubmitField('Изменить')


class ClientSearchForm(FlaskForm):#ищем клиента для добавления брони / визита
    phone = StringField('Мобильный телефон; образец 87017166243',validators=[DataRequired(), Length(min=11,max=11)])
    submit = SubmitField('Найти')


class VisitForm(FlaskForm):#добавляем визит
    comment = StringField('Комментарий (необязательно)',validators=[Length(min=0,max=200)])
    submit = SubmitField('Добавить визит')


class BookingForm(FlaskForm):#добавляем / изменяем бронь
    begin_d = DateField('Начало, дата', format='%Y-%m-%d',validators=[DataRequired()])
    begin_t= TimeField('Начало, время', format='%H:%M',validators=[DataRequired()])
    end_d = DateField('Конец, дата', format='%Y-%m-%d',validators=[DataRequired()])
    end_t= TimeField('Конец, время', format='%H:%M',validators=[DataRequired()])
    comment = StringField('Комментарий (необязательно)',validators=[Length(min=0,max=200)])
    submit = SubmitField('Добавить / изменить бронь')

