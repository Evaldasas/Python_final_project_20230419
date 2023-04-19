from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Email
from wtforms_sqlalchemy.fields import  QuerySelectField
from flask_wtf.file import FileField, FileAllowed
import app

class RegisterForm(FlaskForm):
    name = StringField('Full name', [DataRequired()])
    e_mail = StringField('Email', [DataRequired(), Email()])
    password = PasswordField('Password', [DataRequired()])
    confirmed_password = PasswordField("Repeat password", [EqualTo('password', 'Passwords does not match!')])
    submit = SubmitField("Register")
       
    def validate_name(self, name):
        user = app.User.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('This name is already in use. Please choose another one!')
    
    def validate_e_mail(self, e_mail):
        user = app.User.query.filter_by(e_mail=e_mail.data).first()
        if user:
            raise ValidationError('This e-mail is already in use. Please use different e-mail!')

class LoginForm(FlaskForm):
    e_mail = StringField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField('Login')

class PasswordResetRequestForm(FlaskForm):
    e_mail = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send request')

    def validate_email(self, e_mail):
        user = app.User.query.filter_by(e_mail=e_mail.data).first()
        if user is None:
            raise ValidationError('There is no account registered with this e-mail. Please register.')

class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirmed_password = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Renew password')

class ProfileUpdateForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    e_mail = StringField('E-mail', [DataRequired()])
    profile_image = FileField('Update profile picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_name(self, name):
        if name.data != app.current_user.name:
            user = app.User.query.filter_by(user = user.data).first()
            if user:
                raise ValidationError('This name is already in use. Please choose another one!')

    def validate_e_mail(self, e_mail):
        if e_mail.data != app.current_user.e_mail:
            user = app.User.query.filter_by(e_mail = e_mail.data).first()
            if user:
                raise ValidationError('This e-mail is already in use. Please use different e-mail!')

class AddCategoryForm(FlaskForm):
    category_name = StringField('Category name', [DataRequired()])
    submit = SubmitField('Add Category')

class UpdateCategoryForm(FlaskForm):
    category_name = StringField('Category name', [DataRequired()])
    submit = SubmitField('Update')

class NewCategoryNoteForm(FlaskForm):
    note_title = StringField('Note title', [DataRequired()])
    note_information = TextAreaField('Note text', [DataRequired()])
    note_image = FileField('Select picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Add note')

class UpdateNoteForm(FlaskForm):
    note_title = StringField('Note title', [DataRequired()])
    note_information = TextAreaField('Note text', [DataRequired()])
    note_image = FileField('Select picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class SearchForm(FlaskForm):
    searched = StringField('Searched', validators = [DataRequired()])
    submit = SubmitField('Submit')