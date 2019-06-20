from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField                
from wtforms.validators import DataRequired, ValidationError, Length


class QuestionForm(FlaskForm):#задать вопрос на сайте
    name = StringField('Ваше имя',validators=[DataRequired(), Length(min=1,max=50)])
    phone = StringField('Ваш мобильный телефон в формате 87771234567',validators=[DataRequired(), Length(min=11,max=11)])
    question = TextAreaField('Ваш вопрос',validators=[Length(min=3,max=1000)])
    submit = SubmitField('Задать вопрос')

    def validate_phone(self,phone):
        try:
            p = int(phone.data)
        except:
            raise ValidationError('Номер мобильного телефона должен содержать только цифры, например 87771234567')        
        if len(phone.data) != 11:
            raise ValidationError('Введите номер в формате 87771234567')
   