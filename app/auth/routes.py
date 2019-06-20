from app import db
from app.auth import bp
from flask import render_template, flash, redirect, url_for, request, g
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User, Const_public, Const_admin
from flask_login import current_user, login_user, logout_user, login_required
from functools import wraps
from werkzeug.urls import url_parse
from datetime import datetime
from flask_babel import get_locale
import os
from app.universal_routes import before_request_u, required_roles_u


@bp.before_request
def before_request():
    return before_request_u()


def required_roles(*roles):
    return required_roles_u(*roles)


@bp.route('/login',methods=['GET','POST'])#вход
def login():
    title = 'Вход'
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неправильный логин или пароль')
            return redirect(url_for('auth.login'))
        login_user(user,remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('admin.admin')
        return redirect(next_page)
    return render_template('auth/login.html',title=title,form=form)


@bp.route('/logout')#выход
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.index'))


@bp.route('/register',methods=['GET','POST'])#регистрация
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
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',title='Регистрация',form=form)
