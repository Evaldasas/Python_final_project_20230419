import os
import forms
import secrets
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_mail import Message
from flask_login import LoginManager, current_user, logout_user, login_user, UserMixin, login_required
from PIL import Image


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

secret_key = os.urandom(32)
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'notes.db')+'?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


from flask_mail import Message, Mail

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_password'

mail = Mail(app)

def default_time():
    return datetime.now()

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("Name", db.String(20), unique=True, nullable=False)
    e_mail = db.Column("Email", db.String(120), unique=True, nullable=False)
    password = db.Column("Password", db.String(60), unique=True, nullable=False)
    user_image = db.Column(db.String(20), nullable=False, default='default.jpg')
    date = db.Column("Date", db.DateTime, default= default_time)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column("Category", db.String (100), nullable=False)
    date = db.Column("Date", db.DateTime, default= default_time)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", lazy=True)
         
class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    note_title = db.Column("Note title", db.String (100), nullable=False)
    note_information = db.Column("Note", db.String(), nullable=False)
    date = db.Column("Date", db.DateTime, default= default_time)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), default= '0')
    category = db.relationship("Category", lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", lazy=True)
  
class Picture(db.Model):
    __tablename__ = 'picture'
    id = db.Column(db.Integer, primary_key=True)
    image_link = db.Column("image link",  db.String (100), nullable = False)
    date = db.Column("Date", db.DateTime, default= default_time)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"))
    note = db.relationship("Note", lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.RegisterForm()
    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, e_mail=form.e_mail.data, password=encrypted_password)
        db.session.add(user)
        db.session.commit()
        flash('You have succesfully registered. Please login.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(e_mail=form.e_mail.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('my_categories'))
        else:
            flash('Could not login. Please try again!', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return render_template('index.html')

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Renew password request',
                  sender = 'your_email@example.com',
                  recipients = [user.e_mail])
    msg.body = f'''Please follow this link to renew your password:
    {url_for('reset_token', token=token, _external=True)}
    Please do nothing if you did not send this request.
    '''
    print(msg.body)
    # mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def password_reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = forms.PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(e_mail = form.e_mail.data).first()
        send_reset_email(user)
        flash('We have send you an e-mail. Please follow the instructions.', 'info')
        return redirect(url_for('login'))
    return render_template('password_reset_request.html', title='Reset Password 1', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Token has expired!', 'warning')
        return redirect(url_for('password_reset_request'))
    form = forms.PasswordResetForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.slaptazodis = hashed_password
        db.session.commit()
        flash('Your password has been renewed! Now you can login', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password 2', form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pictures', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def save_note_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/note_pictures', picture_fn)
    output_size = (400, 400)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route("/my_profile", methods=['GET', 'POST'])
@login_required
def my_profile():
    form = forms.ProfileUpdateForm()
    if form.validate_on_submit():
        if form.profile_image.data:
            profile_image = save_picture(form.profile_image.data)
            current_user.user_image = profile_image
        current_user.name = form.name.data
        current_user.e_mail = form.e_mail.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('my_profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.e_mail.data = current_user.e_mail
    profile_image = url_for('static', filename='profile_pictures/' + current_user.user_image)
    return render_template('my_profile.html', title='Account', form=form, profile_image = profile_image)

@app.route("/my_categories", methods=['GET', 'POST'])
@login_required
def my_categories():
    page = request.args.get('page', 1, type=int)
    my_categories = Category.query.filter(Category.user_id == current_user.id).order_by(Category.date.desc()).paginate(page=page, per_page=6)
    return render_template("my_categories.html", my_categories = my_categories, datetime=datetime)

@app.route("/my_notes", methods=['GET', 'POST'])
@login_required
def my_notes():
    page = request.args.get('page', 1, type=int)
    my_notes = Note.query.filter(Note.user_id == current_user.id).order_by(Note.date.desc()).paginate(page=page, per_page=6)
    return render_template("my_notes.html", my_notes = my_notes, datetime=datetime)

@app.route("/new_category", methods=['GET', 'POST'])
@login_required
def new_category():
    form = forms.AddCategoryForm()
    if form.validate_on_submit():
        new_category = Category(category_name=form.category_name.data, user_id = current_user.id)
        db.session.add(new_category)
        db.session.commit()
        flash('New category has been added.', 'success')
        return redirect(url_for('my_categories'))
    return render_template("new_category.html", form = form)


@app.route("/category_notes/<int:id>", methods=['GET', 'POST'])
@login_required
def category_notes(id):
    page = request.args.get('page', 1, type=int)
    category = Category.query.get(id)
    all_notes = Note.query.filter(Note.category_id == id).order_by(Note.date.desc()).paginate(page=page, per_page=3)
    return render_template("category_notes.html", all_notes = all_notes, category = category, id = id, datetime=datetime)

@app.route("/note/<int:id>", methods=['GET', 'POST'])
@login_required
def note(id):
    note = Note.query.get(id)
    note_id = note.id
    note_images = Picture.query.filter_by(note_id = note_id)
    return render_template("note.html", note = note, note_images = note_images)


@app.route("/new_category_note/<int:id>", methods=['GET', 'POST'])
@login_required
def new_category_note(id):
    form = forms.NewCategoryNoteForm()
    category = Category.query.filter(Category.id == id).first()
    if form.validate_on_submit():
        category_name = category.category_name
        new_category_note = Note(note_title = form.note_title.data, note_information = form.note_information.data, category_id = id, user_id = current_user.id)
        db.session.add(new_category_note)
        db.session.commit()
        if form.note_image.data:
            image_link = save_note_picture(form.note_image.data)
            new_image = Picture(image_link = image_link, note_id = new_category_note.id, user_id = current_user.id)
            db.session.add(new_image)
            db.session.commit()
            flash('New note has been added to category ' + category_name + '.', 'success')
        else:
            flash('New note has been added to category ' + category_name + '. You did not add any pictures.', 'success')
        return redirect(url_for('category_notes', id=id))
    return render_template("new_category_note.html", form = form, category = category)

@app.route("/delete_note/<int:id>")
@login_required
def delete_note(id):
    note = Note.query.get(id)
    category = note.category_id
    note_id = note.id
    db.session.delete(note)
    db.session.commit()
    pictures = Picture.query.filter_by(note_id = note_id)
    if pictures:
        for picture in pictures:
            p_file_name = picture.image_link
            picture_path = os.path.join(app.root_path, 'static/note_pictures', p_file_name)
            db.session.delete(picture)
            db.session.commit()
            if os.path.exists(picture_path):
                os.remove(picture_path)
            else:
                flash("The file does not exist",'warning')
    flash('Note has been deleted.', 'success')
    return redirect(url_for('category_notes', id = category))

@app.route("/delete_category/<int:id>")
@login_required
def delete_category(id):
    category = Category.query.get(id)
    category_id = category.id
    db.session.delete(category)
    db.session.commit()
    notes = Note.query.filter_by(category_id = category_id)
    if notes:
        for note in notes:
            note_id = note.id
            db.session.delete(note)
            db.session.commit()
            pictures = Picture.query.filter_by(note_id = note_id)
            if pictures:
                for picture in pictures:
                    p_file_name = picture.image_link
                    picture_path = os.path.join(app.root_path, 'static/note_pictures', p_file_name)
                    db.session.delete(picture)
                    db.session.commit()
                    if os.path.exists(picture_path):
                        os.remove(picture_path)
                    else:
                        flash("The file does not exist",'warning')
    flash('Category has been deleted.', 'success')
    return redirect(url_for('my_categories'))

@app.route("/update_note/<int:id>", methods=['GET', 'POST'])
@login_required
def update_note(id):
    form = forms.UpdateNoteForm()
    note_to_update = Note.query.get(id)
    images = Picture.query.filter_by(note_id = id)
    image = Picture.query.filter_by(note_id = id).first()
    if form.validate_on_submit():
        note_to_update.note_title = form.note_title.data
        note_to_update.note_information = form.note_information.data
        db.session.commit()
        if form.note_image.data:
            image_link = save_note_picture(form.note_image.data)
            new_image = Picture(image_link = image_link, note_id = note_to_update.id)
            db.session.add(new_image)
            db.session.commit()
        flash('Your note has been updated!', 'success')
        return redirect(url_for('note', id = id))
    elif request.method == 'GET':
        form.note_title.data = note_to_update.note_title
        form.note_information.data = note_to_update.note_information
        if image:
            note_image = url_for('static', filename='note_pictures/' + image.image_link)
        else:
            note_image = None
        return render_template('update_note.html', title='Note', form=form, note_image = note_image, images = images)
            

@app.route("/update_category/<int:id>", methods=['GET', 'POST'])
@login_required
def update_category(id):
    form = forms.UpdateCategoryForm()
    category_to_update = Category.query.get(id)
    if form.validate_on_submit():
        category_to_update.category_name = form.category_name.data
        db.session.commit()
        flash('Your category has been updated!', 'success')
        return redirect(url_for('category_notes', id = id))
    elif request.method == 'GET':
        form.category_name.data = category_to_update.category_name
    return render_template('update_category.html', title='Category', form=form)

@app.context_processor
def base():
    form = forms.SearchForm()
    return dict(form = form)

@app.route("/search", methods=['GET', 'POST'] )
@login_required
def search():
    notes = Note.query
    form = forms.SearchForm()
    if form.validate_on_submit():
        searched = form.searched.data
        notes = notes.filter(db.and_(Note.user_id == current_user.id, Note.note_title.like('%' + searched + '%')))
        notes = notes.order_by(Note.date).all()
        return render_template("search.html", form = form, searched = searched, notes = notes)
    

@app.route("/delete_image/<int:id>/<int:note_id>", methods=['GET', 'POST'])
@login_required
def delete_image(id, note_id):
    n_id = note_id
    image = Picture.query.get(id)
    db.session.delete(image)
    db.session.commit()
    flash('Image has been deleted.', 'success')
    return redirect(url_for('update_note', id = n_id))


@app.errorhandler(404)
def klaida_404(error):
    return render_template("404.html"), 404


@app.errorhandler(403)
def klaida_403(error):
    return render_template("403.html"), 403


@app.errorhandler(500)
def klaida_500(error):
    return render_template("500.html"), 500


if __name__ == '__main__':
    db.create_all()
    app.run(host='127.0.0.1', port=8000, debug=True)

