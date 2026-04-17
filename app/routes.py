import os
import json
import gpxpy
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Marker, GPXTrack
from app.forms import RegistrationForm, LoginForm, MarkerForm, GPXUploadForm
from app.utils import gpx_to_geojson

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    markers = Marker.query.filter_by(is_public=True).all()
    return render_template('index.html', title='Главная', markers=markers, api_key=current_app.config['YANDEX_API_KEY'])


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data,
                    email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Регистрация', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Неверный email или пароль', 'danger')
    return render_template('login.html', title='Вход', form=form)


@main.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))


@main.route('/add_marker', methods=['GET', 'POST'])
@login_required
def add_marker():
    form = MarkerForm()
    # Если координаты переданы в URL (например, после клика по карте)
    if request.method == 'GET':
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        if lat and lon:
            form.latitude.data = float(lat)
            form.longitude.data = float(lon)
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{current_user.id}_{Marker.query.count()}{ext}"
            filepath = os.path.join(
                current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_filename = filename

        marker = Marker(
            title=form.title.data,
            description=form.description.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            image_filename=image_filename,
            user_id=current_user.id,
            is_public=form.is_public.data
        )
        db.session.add(marker)
        db.session.commit()
        flash('Метка успешно добавлена!', 'success')
        return redirect(url_for('main.index'))
    return render_template('add_marker.html', title='Добавить метку', form=form, api_key=current_app.config['YANDEX_API_KEY'])


@main.route('/my_markers')
@login_required
def my_markers():
    markers = Marker.query.filter_by(user_id=current_user.id).order_by(
        Marker.created_at.desc()).all()
    return render_template('markers.html', title='Мои метки', markers=markers, show_delete=True)


@main.route('/all_markers')
def all_markers():
    markers = Marker.query.filter_by(is_public=True).order_by(
        Marker.created_at.desc()).all()
    return render_template('markers.html', title='Все публичные метки', markers=markers, show_delete=False)


@main.route('/delete_marker/<int:marker_id>')
@login_required
def delete_marker(marker_id):
    marker = Marker.query.get_or_404(marker_id)
    if marker.user_id != current_user.id and not current_user.is_admin:
        flash('У вас нет прав для удаления этой метки.', 'danger')
        return redirect(url_for('main.index'))
    # Удаляем файл изображения, если есть
    if marker.image_filename:
        filepath = os.path.join(
            current_app.config['UPLOAD_FOLDER'], marker.image_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    db.session.delete(marker)
    db.session.commit()
    flash('Метка удалена.', 'success')
    return redirect(url_for('main.my_markers'))


@main.route('/upload_gpx', methods=['GET', 'POST'])
@login_required
def upload_gpx():
    form = GPXUploadForm()
    if form.validate_on_submit():
        gpx_file = form.gpx_file.data
        filename = secure_filename(gpx_file.filename)
        # Сохраняем оригинальный файл
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        gpx_file.save(filepath)

        # Конвертируем GPX в GeoJSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            geojson_data = gpx_to_geojson(gpx)
        except Exception as e:
            flash(f'Ошибка при обработке GPX: {str(e)}', 'danger')
            return redirect(url_for('main.upload_gpx'))

        track = GPXTrack(
            filename=filename,
            user_id=current_user.id,
            geojson_data=json.dumps(geojson_data)
        )
        db.session.add(track)
        db.session.commit()
        flash('GPX трек успешно загружен!', 'success')
        return redirect(url_for('main.index'))
    return render_template('upload_gpx.html', title='Загрузить GPX', form=form)


@main.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('main.index'))
    users = User.query.all()
    markers = Marker.query.all()
    return render_template('admin.html', title='Админ-панель', users=users, markers=markers)
