from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField                
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User


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
