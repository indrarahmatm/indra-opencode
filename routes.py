import re
import os
import io
import requests
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, send_from_directory, session, make_response, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, mail, db, csrf, cache
import logging
import datetime

# Configure security logging
import os
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(log_dir, exist_ok=True)
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)
# Avoid adding handlers multiple times
if not security_logger.handlers:
    security_handler = logging.FileHandler(os.path.join(log_dir, 'security.log'))
    security_handler.setLevel(logging.WARNING)
    security_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    security_handler.setFormatter(security_formatter)
    security_logger.addHandler(security_handler)
from models import User, Product, Order, OrderItem, Review, Wishlist, Category, ProductImage, Chat, ShippingCourier, ShippingZone, FreeShippingPromo, Setting
from services.midtrans import (
    is_midtrans_enabled, create_snap_token, check_transaction_status,
    get_payment_methods, get_midtrans_status_from_code
)
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ======================
# RAJAONGKIR INTEGRATION
# ======================
def get_rajaongkir_api_key():
    """Get API key from database or config"""
    key = Setting.get('rajaongkir_api_key')
    if not key:
        key = app.config.get('RAJAONGKIR_API_KEY', '')
    return key

RAJAONGKIR_BASE_URL = app.config.get('RAJAONGKIR_BASE_URL', 'https://rajaongkir.komerce.id/api/v1')

def get_rajaongkir_provinces():
    api_key = get_rajaongkir_api_key()
    if not api_key:
        return []
    try:
        response = requests.get(f'{RAJAONGKIR_BASE_URL}/master/region/province', 
                                headers={'key': api_key}, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', [])
    except Exception as e:
        print(f'RajaOngkir error: {e}')
    return []

def get_rajaongkir_cities(province_id=None):
    api_key = get_rajaongkir_api_key()
    if not api_key:
        return []
    try:
        url = f'{RAJAONGKIR_BASE_URL}/master/region/city'
        params = {'province': province_id} if province_id else {}
        response = requests.get(url, headers={'key': api_key}, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', [])
    except Exception as e:
        print(f'RajaOngkir error: {e}')
    return []

def get_rajaongkir_cost(origin, destination, weight, courier):
    api_key = get_rajaongkir_api_key()
    if not api_key:
        return []
    try:
        response = requests.post(
            f'{RAJAONGKIR_BASE_URL}/calculate/domestic-cost',
            headers={'key': api_key, 'Content-Type': 'application/json'},
            json={
                'origin': str(origin),
                'destination': str(destination),
                'weight': int(weight),
                'courier': courier
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('data', [])
    except Exception as e:
        print(f'RajaOngkir cost error: {e}')
    return []

def get_default_shipping_cost(weight_kg):
    """Fallback calculation if RajaOngkir fails"""
    if weight_kg <= 0:
        return 0
    # Default: 5000 dasar + 3000 per kg
    return int(5000 + max(0, (weight_kg - 1) * 3000))

def calculate_shipping_cost(weight_kg, zone_code):
    """Calculate shipping cost based on zone"""
    if weight_kg <= 0:
        return 0
    
    # Get active zone from database
    zone = ShippingZone.query.filter_by(zone_code=zone_code, is_active=True).first()
    
    if zone:
        # Zone-based calculation: base_cost + (weight * cost_per_kg)
        return int(zone.base_cost + (weight_kg * zone.cost_per_kg))
    else:
        # Fallback to default calculation
        return get_default_shipping_cost(weight_kg)

def get_available_zones():
    """Get all active shipping zones"""
    return ShippingZone.query.filter_by(is_active=True).all()

# ======================
# TELEGRAM INTEGRATION
# ======================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8651533615:AAFsvHHS3_XbS0WqNk42G-z8I763q_n2A-w')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '6054204698')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def telegram_send_message(text):
    try:
        import requests as req
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
        req.post(f'{TELEGRAM_API_URL}/sendMessage', data=data, timeout=10)
        return True
    except Exception as e:
        app.logger.error(f'Telegram error: {e}')
        return False

def telegram_notify_order(order, event_type='new'):
    if event_type == 'new':
        msg = f"""<b>🛒 PESANAN BARU #{order.id}</b>

<b>Pembeli:</b> {order.buyer.username}
<b>Total:</b> Rp {order.total_harga:,}
<b>Pembayaran:</b> {order.payment_method.upper()}
<a href="http://127.0.0.1:5003/pesanan">➡️ Proses Pesanan</a>"""
    else:
        msg = f"""<b>📦 UPDATE PESANAN #{order.id}</b>

<b>Status:</b> {order.status.upper()}
<b>Total:</b> Rp {order.total_harga:,}
<a href="http://127.0.0.1:5003/pesanan-saya">➡️ Lihat Detail</a>"""
    return telegram_send_message(msg)

def telegram_notify_chat(username, pesan):
    msg = f"""<b>💬 CHAT BARU dari {username}</b>

{pesan}

<a href="http://127.0.0.1:5003/chat">➡️ Balas di EntokMart</a>"""
    return telegram_send_message(msg)

@app.route('/api/telegram/reply', methods=['POST'])
def telegram_api_reply():
    """API endpoint for Telegram bot to send admin replies to chat"""
    data = request.get_json()
    if not data:
        return {'error': 'No data'}, 400
    
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not user_id or not message:
        return {'error': 'Missing user_id or message'}, 400
    
    # Find the user
    user = User.query.get(user_id)
    if not user:
        return {'error': 'User not found'}, 404
    
    # Save admin reply to chat
    chat = Chat(user_id=user_id, pesan=message, is_from_admin=True)
    db.session.add(chat)
    db.session.commit()
    
    return {'success': True, 'message': 'Reply sent'}

@csrf.exempt
@app.route('/api/telegram/chat', methods=['POST'])
def telegram_api_chat():
    """API endpoint for Telegram bot to receive user messages"""
    data = request.get_json()
    if not data:
        return {'error': 'No data'}, 400
    
    user_id = data.get('user_id')
    message = data.get('message')
    username = data.get('username', 'Telegram User')
    
    if not user_id or not message:
        return {'error': 'Missing user_id or message'}, 400
    
    # Find or create user based on Telegram user_id
    # For now, we'll create a temporary user mapping or use existing user
    user = User.query.filter_by(email=f'tg_{user_id}@telegram.local').first()
    
    if not user:
        # Create a temporary user for Telegram
        user = User(
            username=username,
            email=f'tg_{user_id}@telegram.local',
            role='buyer'
        )
        user.set_password('telegram_user')
        db.session.add(user)
        db.session.commit()
    
    # Save chat message
    chat = Chat(user_id=user.id, pesan=message, is_from_admin=False)
    db.session.add(chat)
    db.session.commit()
    
    # Notify admin via Telegram
    telegram_notify_chat(username, message)
    
    return {'success': True, 'message': 'Chat received'}

# ======================
# RAJAONGKIR API ROUTES
# ======================
@app.route('/api/rajaongkir/provinces')
def api_rajaongkir_provinces():
    provinces = get_rajaongkir_provinces()
    return {'success': True, 'data': provinces}

@app.route('/api/rajaongkir/cities')
def api_rajaongkir_cities():
    province_id = request.args.get('province_id')
    cities = get_rajaongkir_cities(province_id)
    return {'success': True, 'data': cities}

@app.route('/api/rajaongkir/cost', methods=['POST'])
def api_rajaongkir_cost():
    origin = request.form.get('origin', '23')
    destination = request.form.get('destination')
    weight = int(request.form.get('weight', 1000))
    courier = request.form.get('courier', 'jne')
    
    if not destination:
        return {'success': False, 'message': 'Destination required'}
    
    costs = get_rajaongkir_cost(origin, destination, weight, courier)
    return {'success': True, 'data': costs}

def sanitize_input(text):
    if text:
        return re.sub(r'[<>\'\";]', '', str(text))
    return text

def validate_username(username):
    if not username or len(username) < 3 or len(username) > 50:
        return False
    return re.match(r'^[a-zA-Z0-9_]+$', username)

def validate_password(password):
    if not password or len(password) < 6:
        return False
    return True

def send_order_notification(order, status_text, recipient_email=None):
    try:
        from flask_mail import Message
        if not app.config.get('MAIL_USERNAME'):
            return False
        
        if recipient_email is None:
            recipient_email = order.buyer.email
        
        msg = Message(
            subject=f"EntokMart - Status Pesanan #{order.id} Updated",
            recipients=[recipient_email],
            body=f"Halo {order.buyer.username},\n\nPesanan #{order.id} Anda telah diupdate:\nStatus: {status_text}\nTotal: Rp {order.total_harga:,}\n\nTerima kasih telah berbelanja di EntokMart!"
        )
        mail.send(msg)
        return True
    except Exception:
        return False

def send_seller_notification(order, item, status_text):
    try:
        from flask_mail import Message
        if not app.config.get('MAIL_USERNAME'):
            return False
        
        seller = User.query.get(item.product.seller_id)
        if not seller or not seller.email:
            return False
        
        msg = Message(
            subject=f"EntokMart - Pesanan Baru #{order.id}",
            recipients=[seller.email],
            body=f"Halo {seller.username},\n\nAnda menerima pesanan baru:\nProduk: {item.nama_product}\nJumlah: {item.jumlah}\nTotal: Rp {item.harga_saat_buyer * item.jumlah:,}\n\nSegera proses pesanan ini!"
        )
        mail.send(msg)
        return True
    except Exception:
        return False

VALID_STATUSES = ['pending', 'diproses', 'dikirim', 'selesai']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('index.html', products=products, categories=categories)

@app.route('/produk')
def produk():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('index.html', products=products, categories=categories)

@app.route('/produk/search')
def search_produk():
    q = request.args.get('q', '').strip()
    jenis_filter = request.args.get('jenis', '')
    min_harga = request.args.get('min_harga', type=int)
    max_harga = request.args.get('max_harga', type=int)
    
    query = Product.query
    
    if q:
        query = query.filter(Product.name.ilike(f'%{q}%'))
    if jenis_filter:
        query = query.filter(Product.jenis == jenis_filter)
    if min_harga and min_harga > 0:
        query = query.filter(Product.harga >= min_harga)
    if max_harga and max_harga > 0:
        query = query.filter(Product.harga <= max_harga)
    
    products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.all()
    return render_template('index.html', products=products, search_query=q, jenis_filter=jenis_filter, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'buyer')

        if not validate_username(username):
            flash('Username harus 3-50 karakter, hanya huruf/angka/_', 'danger')
            return redirect(url_for('register'))
        
        if not validate_password(password):
            flash('Password minimal 6 karakter', 'danger')
            return redirect(url_for('register'))

        if not re.match(r'^[\w.+]+@[\w.]+$', email):
            flash('Email tidak valid', 'danger')
            return redirect(url_for('register'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username atau email sudah terdaftar', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registrasi berhasil! Silakan login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email dan password wajib diisi', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Check approval for non-admin users
            if user.role != 'admin' and not user.is_approved:
                flash('Akun Anda belum disetujui oleh admin. Silakan hubungi admin.', 'warning')
                return render_template('login.html')
            
            login_user(user, remember=True)
            security_logger.warning(f'LOGIN_SUCCESS: {email} from {request.remote_addr}')
            flash('Login berhasil', 'success')
            if user.role == 'peternak':
                return redirect(url_for('dashboard_peternak'))
            elif user.role == 'buyer':
                return redirect(url_for('dashboard_buyer'))
            else:
                return redirect(url_for('dashboard_admin'))
        security_logger.warning(f'LOGIN_FAILED: {email} from {request.remote_addr}')
        flash('Email atau password salah', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/password/reset', methods=['GET', 'POST'])
def password_reset_request():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            import secrets
            token = secrets.token_urlsafe(32)
            user.token_reset = token
            user.token_expiry = datetime.now() + timedelta(minutes=30)
            db.session.commit()
            
            reset_link = url_for('password_reset', token=token, _external=True)
            flash(f'Link reset: {reset_link}', 'info')
            return redirect(url_for('login'))
        
        flash('Email tidak ditemukan', 'warning')
    return render_template('password_reset_request.html')

@app.route('/password/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    user = User.query.filter_by(token_reset=token).first()
    
    if not user or user.token_expiry < datetime.now():
        flash('Token expired atau invalid', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        
        if len(new_password) < 6:
            flash('Password minimal 6 karakter', 'danger')
            return redirect(url_for('password_reset', token=token))
        
        user.set_password(new_password)
        user.token_reset = None
        user.token_expiry = None
        db.session.commit()
        
        flash('Password berhasil diupdate! Silakan login', 'success')
        return redirect(url_for('login'))
    
    return render_template('password_reset_form.html')

@app.route('/dashboard-peternak')
@login_required
def dashboard_peternak():
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    products = Product.query.filter_by(seller_id=current_user.id).all()
    return render_template('dashboard_peternak.html', products=products)

@app.route('/toko/<username>')
def toko(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    if not user.nama_toko:
        flash('Toko tidak ditemukan', 'warning')
        return redirect(url_for('index'))
    
    products = Product.query.filter_by(seller_id=user.id, stok__gt=0).all()
    return render_template('toko.html', seller=user, products=products)

@app.route('/toko/edit', methods=['GET', 'POST'])
@login_required
def toko_edit():
    if current_user.role not in ['peternak', 'admin']:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        current_user.nama_toko = request.form.get('nama_toko', '').strip()
        current_user.deskripsi_toko = request.form.get('deskripsi_toko', '').strip()
        current_user.no_hp = request.form.get('no_hp', '').strip()
        current_user.alamat = request.form.get('alamat', '').strip()
        db.session.commit()
        
        flash('Toko berhasil diupdate!', 'success')
        return redirect(url_for('dashboard_peternak'))
    
    return render_template('toko_edit.html')

@app.route('/produk/baru', methods=['GET', 'POST'])
@login_required
def produk_baru():
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            jenis = request.form['jenis'].strip()
            berat_kg = float(request.form['berat_kg'])
            harga = int(request.form['harga'])
            deskripsi = request.form['deskripsi'].strip()
            stok = int(request.form.get('stok', 0))
            
            image_url = request.form.get('image_url', '').strip()
            file = request.files.get('image')
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f'produk_{current_user.id}_{name}_{int(datetime.utcnow().timestamp())}.{ext}'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f'/static/uploads/{filename}'

            if not name or len(name) > 150:
                flash('Nama produk tidak valid', 'danger')
                return redirect(url_for('produk_baru'))
            if berat_kg <= 0 or berat_kg > 50:
                flash('Berat harus antara 0-50 kg', 'danger')
                return redirect(url_for('produk_baru'))
            if harga <= 0:
                flash('Harga tidak valid', 'danger')
                return redirect(url_for('produk_baru'))
            if stok < 0:
                flash('Stok tidak valid', 'danger')
                return redirect(url_for('produk_baru'))

            product = Product(seller_id=current_user.id, name=name, jenis=jenis,
                           berat_kg=berat_kg, harga=harga, deskripsi=deskripsi, 
                           image_url=image_url, stok=stok)
            db.session.add(product)
            db.session.commit()
            
            files = request.files.getlist('images')
            for i, file in enumerate(files):
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f'produk_{product.id}_{i}_{int(datetime.utcnow().timestamp())}.{ext}'
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img = ProductImage(
                        product_id=product.id,
                        image_url=f'/static/uploads/{filename}',
                        is_primary=(i == 0 and not image_url)
                    )
                    db.session.add(img)
            
            db.session.commit()
            flash('Produk berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard_peternak'))
        except (ValueError, TypeError):
            flash('Input tidak valid', 'danger')
            return redirect(url_for('produk_baru'))
    categories = Category.query.all()
    return render_template('produk_baru.html', categories=categories)

@app.route('/produk/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def produk_edit(id):
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    product = Product.query.get_or_404(id)
    if product.seller_id != current_user.id:
        return redirect(url_for('dashboard_peternak'))

    if request.method == 'POST':
        try:
            product.name = request.form['name'].strip()
            product.jenis = request.form['jenis'].strip()
            product.berat_kg = float(request.form['berat_kg'])
            product.harga = int(request.form['harga'])
            product.deskripsi = request.form['deskripsi'].strip()
            product.stok = int(request.form.get('stok', 0))
            
            file = request.files.get('image')
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f'produk_{product.id}_{int(datetime.utcnow().timestamp())}.{ext}'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                product.image_url = f'/static/uploads/{filename}'
            else:
                product.image_url = request.form.get('image_url', '').strip()

            files = request.files.getlist('images')
            for i, file in enumerate(files):
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f'produk_{product.id}_{len(product.images)}_{int(datetime.utcnow().timestamp())}.{ext}'
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    img = ProductImage(
                        product_id=product.id,
                        image_url=f'/static/uploads/{filename}',
                        is_primary=(len(product.images) == 0)
                    )
                    db.session.add(img)

            if product.berat_kg <= 0 or product.berat_kg > 50 or product.harga <= 0 or product.stok < 0:
                flash('Input tidak valid', 'danger')
                return redirect(url_for('produk_edit', id=id))

            db.session.commit()
            flash('Produk berhasil diupdate', 'success')
            return redirect(url_for('dashboard_peternak'))
        except (ValueError, TypeError):
            flash('Input tidak valid', 'danger')
            return redirect(url_for('produk_edit', id=id))
    categories = Category.query.all()
    return render_template('produk_edit.html', product=product, categories=categories)

@app.route('/produk/hapus/<int:id>')
@login_required
def produk_hapus(id):
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    product = Product.query.get_or_404(id)
    if product.seller_id == current_user.id:
        db.session.delete(product)
        db.session.commit()
        flash('Produk dihapus', 'success')
    return redirect(url_for('dashboard_peternak'))

@app.route('/dashboard-buyer')
@login_required
def dashboard_buyer():
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    return render_template('dashboard_buyer.html')

@app.route('/keranjang')
@login_required
def keranjang():
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    cart = session.get('cart', [])
    cart_items = []
    total = 0
    valid_cart = []
    for item in cart:
        product = Product.query.get(item['product_id'])
        if product:
            subtotal = product.harga * item['jumlah']
            cart_items.append({'product': product, 'jumlah': item['jumlah'], 'subtotal': subtotal})
            total += subtotal
            valid_cart.append(item)
    session['cart'] = valid_cart
    return render_template('keranjang.html', cart_items=cart_items, total=total)

@app.route('/keranjang/tambah/<int:product_id>', methods=['POST'])
@login_required
def keranjang_tambah(product_id):
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    
    product = Product.query.get(product_id)
    if not product:
        flash('Produk tidak ditemukan', 'danger')
        return redirect(url_for('index'))
    
    if product.stok <= 0:
        flash('Maaf, stok produk habis', 'warning')
        return redirect(url_for('keranjang'))
    
    jumlah = int(request.form.get('jumlah', 1))
    
    if jumlah > product.stok:
        flash(f'Stok tidak mencukupi. Tersedia: {product.stok}', 'warning')
        return redirect(url_for('keranjang'))
    
    cart = session.get('cart', [])

    existing = next((item for item in cart if item['product_id'] == product_id), None)
    if existing:
        new_qty = existing['jumlah'] + jumlah
        if new_qty > product.stok:
            flash(f'Stok tidak mencukupi. Tersedia: {product.stok}', 'warning')
            return redirect(url_for('keranjang'))
        existing['jumlah'] = new_qty
    else:
        cart.append({'product_id': product_id, 'jumlah': jumlah})

    session['cart'] = cart
    flash('Ditambahkan ke keranjang', 'success')
    return redirect(url_for('keranjang'))

@app.route('/keranjang/hapus/<int:product_id>')
@login_required
def keranjang_hapus(product_id):
    cart = session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]
    session['cart'] = cart
    flash('Item dihapus dari keranjang', 'success')
    return redirect(url_for('keranjang'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    cart = session.get('cart', [])
    if not cart:
        flash('Keranjang kosong', 'warning')
        return redirect(url_for('keranjang'))

    if request.method == 'POST':
        nama_penerima = request.form.get('nama_penerima', '').strip()
        alamat = request.form.get('alamat', '').strip()
        telp = request.form.get('telp', '').strip()
        payment_method = request.form.get('payment_method', 'cod')
        
        if not nama_penerima or not alamat or not telp:
            flash('Semua field wajib diisi', 'danger')
            return redirect(url_for('checkout'))

        subtotal = 0
        total_weight_kg = 0.0
        insufficient_stock = []
        for item in cart:
            product = Product.query.get(item['product_id'])
            if product:
                if item['jumlah'] > product.stok:
                    insufficient_stock.append(f"{product.name} (tersedia: {product.stok})")
                subtotal += product.harga * item['jumlah']
                total_weight_kg += product.berat_kg * item['jumlah']
        
        # Calculate shipping cost (ongkir) - use zones
        selected_zone = request.form.get('shipping_zone', '')
        
        if total_weight_kg > 0 and selected_zone:
            # Calculate using zone
            ongkir = calculate_shipping_cost(total_weight_kg, selected_zone)
        else:
            # Fallback to default calculation
            ongkir = get_default_shipping_cost(total_weight_kg)
        
        # Total harga includes ongkir
        total_harga = subtotal + ongkir
        
        if insufficient_stock:
            flash(f'Stok tidak mencukupi: {", ".join(insufficient_stock)}', 'danger')
            return redirect(url_for('keranjang'))
        
        order = Order(buyer_id=current_user.id, total_harga=total_harga,
                      nama_penerima=nama_penerima, alamat=alamat, telp=telp,
                      payment_method=payment_method, payment_status='pending',
                      ongkir=ongkir)
        db.session.add(order)
        db.session.commit()
        
        for item in cart:
            product = Product.query.get(item['product_id'])
            if product:
                order_item = OrderItem(order_id=order.id, product_id=product.id,
                                       jumlah=item['jumlah'], harga_saat_beli=product.harga,
                                       nama_product=product.name, nama_peternak=product.seller.username)
                db.session.add(order_item)
                product.stok -= item['jumlah']
        
        db.session.commit()
        
        # Clear cart
        session['cart'] = []
        
        # Send email confirmation (if mail is configured)
        try:
            from flask_mail import Message
            if app.config.get('MAIL_USERNAME'):
                msg = Message(
                    subject=f"EntokMart - Pesanan #{order.id} Diterima",
                    recipients=[current_user.email],
                    body=f"Halo {current_user.username},\n\nTerima kasih! Pesanan #{order.id} Anda telah diterima.\n\nSubtotal: Rp {subtotal:,}\nOngkir: Rp {ongkir:,}\nTotal: Rp {total_harga:,}\nMetode: {payment_method.upper()}\n\nKami akan segera memproses pesanan Anda."
                )
                mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
        
        # Notify admin via Telegram
        try:
            telegram_notify_order(order, event_type='new')
        except Exception as e:
            app.logger.error(f"Telegram notification failed: {e}")
        
        flash('Pesanan berhasil dibuat!', 'success')
        return redirect(url_for('pesanan_saya'))
        
        # Clear cart
        session['cart'] = []
        
        # Send email confirmation (if mail is configured)
        try:
            from flask_mail import Message
            if app.config.get('MAIL_USERNAME'):
                msg = Message(
                    subject=f"EntokMart - Pesanan #{order.id} Diterima",
                    recipients=[current_user.email],
                    body=f"Halo {current_user.username},\n\nTerima kasih! Pesanan #{order.id} Anda telah diterima.\n\nSubtotal: Rp {subtotal:,}\nOngkir: Rp {ongkir:,}\nTotal: Rp {total_harga:,}\nMetode: {payment_method.upper()}\n\nKami akan segera memproses pesanan Anda."
                )
                mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
        
        # Notify admin via Telegram
        try:
            telegram_notify_order(order, event_type='new')
        except Exception as e:
            app.logger.error(f"Telegram notification failed: {e}")
        
        flash('Pesanan berhasil dibuat!', 'success')
        return redirect(url_for('pesanan_saya'))
        
        for item in cart:
            product = Product.query.get(item['product_id'])
            if product:
                order_item = OrderItem(order_id=order.id, product_id=product.id,
                                   jumlah=item['jumlah'], harga_saat_beli=product.harga,
                                   nama_product=product.name, nama_peternak=product.seller.username)
                db.session.add(order_item)
                product.stok -= item['jumlah']
        
        db.session.commit()
        session['cart'] = []
        
        try:
            from flask_mail import Message
            if app.config.get('MAIL_USERNAME'):
                msg = Message(
                    subject=f"EntokMart - Pesanan #{order.id} Diterima",
                    recipients=[current_user.email],
                    body=f"Halo {current_user.username},\n\nTerima kasih! Pesanan #{order.id} Anda telah diterima.\n\nTotal: Rp {total_harga:,}\nMetode: {payment_method.upper()}\n\nKami akan segera memproses pesanan Anda."
                )
                mail.send(msg)
        except Exception:
            pass
        
        # Telegram notification
        telegram_notify_order(order, 'new')
        
        flash(f'Pesanan berhasil dibuat! ({payment_method.upper()})', 'success')
        return redirect(url_for('pesanan_saya'))

    # GET request - calculate totals for display
    subtotal = 0
    total_weight_kg = 0.0
    for item in cart:
        product = Product.query.get(item['product_id'])
        if product:
            subtotal += product.harga * item['jumlah']
            total_weight_kg += product.berat_kg * item['jumlah']
    
        # Calculate shipping cost (ongkir)
        if total_weight_kg <= 0:
            ongkir = 0
        else:
            # Base cost 5000 for first kg, then 3000 per additional kg
            ongkir = int(5000 + max(0, (total_weight_kg - 1) * 3000))
    
    # Total harga includes ongkir
    total_harga = subtotal + ongkir
    
    # GET request - display checkout form with totals
    zones = get_available_zones()
    return render_template('checkout.html', subtotal=subtotal, ongkir=ongkir, total=total_harga, zones=zones)

@app.route('/pesanan-saya')
@login_required
def pesanan_saya():
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('pesanan_saya.html', orders=orders)

@app.route('/pesanan-saya/batal/<int:order_id>')
@login_required
def pesanan_batal(order_id):
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash('Akses ditolak', 'danger')
        return redirect(url_for('pesanan_saya'))
    
    if order.status not in ['pending', 'diproses']:
        flash('Pesanan tidak bisa dibatalkan', 'warning')
        return redirect(url_for('pesanan_saya'))
    
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product:
            product.stok += item.jumlah
    
    order.status = 'dibatalkan'
    db.session.commit()
    flash('Pesanan berhasil dibatalkan', 'success')
    return redirect(url_for('pesanan_saya'))

@app.route('/pesanan-saya/detail/<int:order_id>')
@login_required
def pesanan_detail(order_id):
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash('Akses ditolak', 'danger')
        return redirect(url_for('pesanan_saya'))
    
    return render_template('pesanan_detail.html', order=order)

@app.route('/pesanan-saya/invoice/<int:order_id>')
@login_required
def pesanan_invoice(order_id):
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash('Akses ditolak', 'danger')
        return redirect(url_for('pesanan_saya'))
    
    # Only allow invoice for completed orders
    if order.status != 'selesai':
        flash('Invoice hanya dapat dibuat untuk pesanan yang selesai', 'warning')
        return redirect(url_for('pesanan_detail', order_id=order.id))
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # center
    )
    
    # Company info
    elements.append(Paragraph("EntokMart", title_style))
    elements.append(Paragraph("Marketplace untuk Peternak Entok", styles['Normal']))
    elements.append(Paragraph("https://entokmart.example.com", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Invoice title
    elements.append(Paragraph(f"INVOICE / PESANAN #{order.id}", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Date and order info
    date_str = order.created_at.strftime("%d %B %Y")
    elements.append(Paragraph(f"Tanggal: {date_str}", styles['Normal']))
    elements.append(Paragraph(f"Status Pembayaran: {order.payment_status}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Customer info
    elements.append(Paragraph("Bill To:", styles['Heading3']))
    elements.append(Paragraph(f"{order.nama_penerima}", styles['Normal']))
    elements.append(Paragraph(f"{order.alamat}", styles['Normal']))
    elements.append(Paragraph(f"Telp: {order.telp}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Order items table
    data = [['Produk', 'Peternak', 'Qty', 'Harga Satuan', 'Subtotal']]
    for item in order.items:
        data.append([
            item.nama_product,
            item.nama_peternak,
            str(item.jumlah),
            f"Rp {item.harga_saat_beli:,}",
            f"Rp {item.harga_saat_beli * item.jumlah:,}"
        ])
    
    # Add total row
    data.append(['', '', '', 'Total:', f"Rp {order.total_harga:,}"])
    
    table = Table(data, colWidths=[80*mm, 50*mm, 20*mm, 30*mm, 30*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Payment method
    elements.append(Paragraph(f"Metode Pembayaran: {order.payment_method.upper()}", styles['Normal']))
    if order.payment_method == 'manual' and order.transfer_proof_url:
        elements.append(Paragraph("Bukti Transfer: Telah diupload dan diverifikasi", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Footer
    elements.append(Paragraph("Terima kasih telah berbelanja di EntokMart!", styles['Italic']))
    elements.append(Paragraph("Untuk pertanyaan, hubungi kami melalui live chat atau Telegram @ecomm1_bot", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return make_response(
        buffer.getvalue(),
        200,
        {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename=invoice_entokmart_{order.id}.pdf'
        }
    )

@app.route('/bukti-transfer/<int:order_id>', methods=['GET', 'POST'])
@login_required
def bukti_transfer(order_id):
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash('Akses ditolak', 'danger')
        return redirect(url_for('pesanan_saya'))
    
    if order.payment_method != 'manual':
        flash('Metode pembayaran bukan transfer manual', 'warning')
        return redirect(url_for('pesanan_saya'))
    
    if request.method == 'POST':
        file = request.files.get('bukti')
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f'bukti_{order.id}_{current_user.id}.{ext}'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            order.transfer_proof_url = f'/static/uploads/{filename}'
            order.payment_status = 'pending'
            db.session.commit()
            flash('Bukti transfer berhasil diupload', 'success')
            return redirect(url_for('pesanan_saya'))
        else:
            flash('File tidak valid atau kosong', 'danger')
    
    return render_template('bukti_transfer.html', order=order)

@app.route('/pesanan')
@login_required
def pesanan():
    if current_user.role not in ['peternak', 'admin']:
        return redirect(url_for('index'))
    
    # Admin sees all orders, seller sees their orders
    if current_user.role == 'admin':
        items = OrderItem.query.join(Order).all()
    else:
        items = OrderItem.query.filter_by(nama_peternak=current_user.username).all()
    
    return render_template('pesanan.html', items=items)

@app.route('/laporan')
@login_required
def laporan():
    if current_user.role not in ['peternak', 'admin']:
        return redirect(url_for('index'))
    
    # Admin sees all orders, seller sees their orders
    if current_user.role == 'admin':
        items = OrderItem.query.join(Order).all()
    else:
        items = OrderItem.query.filter_by(nama_peternak=current_user.username).all()
    
    total_pesanan = len(items)
    total_pendapatan = sum(item.harga_saat_beli * item.jumlah for item in items)
    pesanan_selesai = [item for item in items if item.order.status == 'selesai']
    pesanan_dikirim = [item for item in items if item.order.status == 'dikirim']
    pesanan_diproses = [item for item in items if item.order.status in ['pending', 'diproses']]
    
    return render_template('laporan.html', 
                       total_pesanan=total_pesanan,
                       total_pendapatan=total_pendapatan,
                       pesanan_selesai=len(pesanan_selesai),
                       pesanan_dikirim=len(pesanan_dikirim),
                       pesanan_diproses=len(pesanan_diproses),
                       items=items)

@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        
        if not new_username or not new_email:
            flash('Username dan email wajib diisi', 'danger')
            return redirect(url_for('profil'))
        
        existing = User.query.filter(
            ((User.username == new_username) | (User.email == new_email)),
            User.id != current_user.id
        ).first()
        
        if existing:
            flash('Username atau email sudah digunakan', 'danger')
            return redirect(url_for('profil'))
        
        current_user.username = new_username
        current_user.email = new_email
        db.session.commit()
        flash('Profil berhasil diupdate', 'success')
        return redirect(url_for('profil'))
    
    return render_template('profil.html')

@app.route('/profil/password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_user.check_password(current_password):
            flash('Password saat ini salah', 'danger')
            return redirect(url_for('change_password'))
        
        if len(new_password) < 6:
            flash('Password baru minimal 6 karakter', 'danger')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('Password baru tidak cocok', 'danger')
            return redirect(url_for('change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password berhasil diubah', 'success')
        return redirect(url_for('profil'))
    
    return render_template('change_password.html')

@app.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Link reset password telah dikirim ke email Anda (fitur belum aktif)', 'info')
        else:
            flash('Email tidak ditemukan', 'danger')
        return redirect(url_for('login'))
    
    return render_template('lupa_password.html')

@app.route('/pesanan/update/<int:id>', methods=['POST'])
@login_required
def pesanan_update(id):
    if current_user.role not in ['peternak', 'admin']:
        return redirect(url_for('index'))
    
    order = Order.query.get(id)
    if not order:
        flash('Pesanan tidak ditemukan', 'danger')
        return redirect(url_for('pesanan'))
    
    status = request.form.get('status', '')
    resi = request.form.get('resi', '').strip()
    payment_status = request.form.get('payment_status', '')
    
    old_status = order.status
    if status and status in ['pending', 'diproses', 'dikirim', 'selesai']:
        order.status = status
    if resi:
        order.resi = resi
    if payment_status and payment_status in ['pending', 'confirmed', 'failed']:
        order.payment_status = payment_status
    
    db.session.commit()
    
    if old_status != order.status or resi:
        try:
            from flask_mail import Message
            if app.config.get('MAIL_USERNAME'):
                status_text = order.status.capitalize()
                if resi:
                    status_text += f" - No. Resi: {resi}"
                
                msg = Message(
                    subject=f"EntokMart - Pesanan #{order.id} Update",
                    recipients=[order.buyer.email],
                    body=f"Halo {order.buyer.username},\n\nPesanan #{order.id} Anda telah diupdate.\n\nStatus: {status_text}\nTotal: Rp {order.total_harga:,}\n\nTerima kasih!"
                )
                mail.send(msg)
        except Exception:
            pass
    
    flash('Pesanan diupdate', 'success')
    return redirect(url_for('pesanan'))

@app.route('/pesanan/bukti/<int:order_id>')
@login_required
def lihat_bukti_transfer(order_id):
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    if not order.transfer_proof_url:
        flash('Bukti transfer belum ada', 'warning')
        return redirect(url_for('pesanan'))
    
    return render_template('lihat_bukti.html', order=order)

@app.route('/pesanan/bayar-seller/<int:order_id>', methods=['POST'])
@login_required
def bayarkan_ke_seller(order_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'selesai':
        flash('Pesanan harus berstatus Selesai baru bisa dibayarkan ke seller', 'warning')
        return redirect(url_for('pesanan'))
    
    if order.seller_paid:
        flash('Pesanan sudah dibayarkan ke seller', 'info')
        return redirect(url_for('pesanan'))
    
    order.seller_paid = True
    order.seller_paid_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Pembayaran ke seller untuk order #{order.id} telah dikonfirmasi', 'success')
    return redirect(url_for('pesanan'))

@app.route('/admin')
@login_required
def dashboard_admin():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    users = User.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Analytics
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_revenue = sum(o.total_harga for o in Order.query.all() if o.status != 'cancelled')
    pending_orders = Order.query.filter_by(status='pending').count()
    processing_orders = Order.query.filter_by(status='processing').count()
    completed_orders = Order.query.filter_by(status='completed').count()
    
    # Revenue breakdown: Commission (5%) + Service Fee (Rp 2000 per order)
    commission_rate = 0.05  # 5%
    service_fee = 2000  # Rp 2000 per order
    commission_revenue = sum(o.total_harga * commission_rate for o in Order.query.all() if o.status != 'cancelled')
    service_revenue = sum(service_fee for o in Order.query.all() if o.status != 'cancelled')
    
    # Recent stats (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    recent_orders = Order.query.filter(Order.created_at >= week_ago).count()
    
    # Top products
    order_items = OrderItem.query.all()
    product_counts = {}
    for item in order_items:
        if item.nama_product:
            product_counts[item.nama_product] = product_counts.get(item.nama_product, 0) + item.jumlah
    
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    stats = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'commission_revenue': commission_revenue,
        'service_revenue': service_revenue,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'recent_orders': recent_orders,
        'top_products': top_products
    }
    
    return render_template('dashboard_admin.html', users=users, orders=orders, stats=stats)

@app.route('/admin/approve/<int:id>', methods=['POST'])
@login_required
def admin_approve_user(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    user.is_approved = True
    db.session.commit()
    flash(f'Akun {user.username} telah disetujui', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/reject/<int:id>', methods=['POST'])
@login_required
def admin_reject_user(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    username = user.username
    
    if user.role != 'admin':
        # Delete related chat messages
        Chat.query.filter_by(user_id=user.id).delete()
        # Delete related orders and order items
        OrderItem.query.filter(OrderItem.order_id.in_(
            db.session.query(Order.id).filter(Order.buyer_id == user.id)
        )).delete(synchronize_session=False)
        Order.query.filter_by(buyer_id=user.id).delete()
        # Delete products if seller
        Product.query.filter_by(seller_id=user.id).delete()
        # Delete user
        db.session.delete(user)
        db.session.commit()
        flash(f'Akun {username} telah dihapus', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/sellers')
@login_required
def admin_sellers():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    sellers = User.query.filter_by(role='peternak').all()
    return render_template('admin_sellers.html', sellers=sellers)

@app.route('/admin/seller/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_seller_edit(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    if user.role != 'peternak':
        flash('User bukan seller', 'danger')
        return redirect(url_for('admin_sellers'))
    
    if request.method == 'POST':
        user.nama_toko = request.form.get('nama_toko', '').strip()
        user.deskripsi_toko = request.form.get('deskripsi_toko', '').strip()
        user.no_hp = request.form.get('no_hp', '').strip()
        user.alamat = request.form.get('alamat', '').strip()
        user.verifikasi = 'verifikasi' in request.form
        db.session.commit()
        flash(f'Toko {user.username} berhasil diupdate', 'success')
        return redirect(url_for('admin_sellers'))
    
    return render_template('admin_seller_edit.html', seller=user)

@app.route('/admin/seller/delete/<int:id>', methods=['POST'])
@login_required
def admin_seller_delete(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    if user.role != 'peternak':
        flash('User bukan seller', 'danger')
        return redirect(url_for('admin_sellers'))
    
    # Delete all products of this seller first
    Product.query.filter_by(seller_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'Seller {user.username} dan produknya telah dihapus', 'success')
    return redirect(url_for('admin_sellers'))

@app.route('/admin/categories')
@login_required
def admin_categories():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    categories = Category.query.all()
    return render_template('admin_categories.html', categories=categories)

@app.route('/admin/category/add', methods=['POST'])
@login_required
def admin_category_add():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Nama kategori wajib diisi', 'danger')
        return redirect(url_for('admin_categories'))
    
    # Create slug
    import re
    slug = re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')
    
    # Check duplicate
    existing = Category.query.filter_by(name=name).first()
    if existing:
        flash('Kategori sudah ada', 'warning')
        return redirect(url_for('admin_categories'))
    
    category = Category(name=name, slug=slug, description=description)
    db.session.add(category)
    db.session.commit()
    flash(f'Kategori {name} ditambahkan', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/category/edit/<int:id>', methods=['POST'])
@login_required
def admin_category_edit(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    category = Category.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Nama kategori wajib diisi', 'danger')
        return redirect(url_for('admin_categories'))
    
    # Check duplicate (exclude current)
    existing = Category.query.filter(Category.name == name, Category.id != id).first()
    if existing:
        flash('Nama kategori sudah digunakan', 'warning')
        return redirect(url_for('admin_categories'))
    
    import re
    category.name = name
    category.slug = re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')
    category.description = description
    db.session.commit()
    flash(f'Kategori {name} diupdate', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/category/delete/<int:id>', methods=['POST'])
@login_required
def admin_category_delete(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    category = Category.query.get_or_404(id)
    name = category.name
    
    # Check if category is used by products
    products_count = Product.query.filter_by(jenis=name).count()
    if products_count > 0:
        flash(f'Kategori {name} masih digunakan oleh {products_count} produk. Hapus produk terlebih dahulu.', 'danger')
        return redirect(url_for('admin_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash(f'Kategori {name} dihapus', 'success')
    return redirect(url_for('admin_categories'))

# ==================== SHIPPING MANAGEMENT ====================

@app.route('/admin/shipping')
@login_required
def admin_shipping():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    couriers = ShippingCourier.query.all()
    zones = ShippingZone.query.all()
    promos = FreeShippingPromo.query.all()
    api_key = Setting.get('rajaongkir_api_key', '')
    app_api_key = Setting.get('app_api_key', '')
    
    return render_template('admin_shipping.html', couriers=couriers, zones=zones, promos=promos, api_key=api_key, app_api_key=app_api_key)

# Courier Management
@app.route('/admin/shipping/courier/add', methods=['POST'])
@login_required
def admin_courier_add():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Nama kurir wajib diisi', 'danger')
        return redirect(url_for('admin_shipping'))
    
    slug = re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')
    
    courier = ShippingCourier(name=name, slug=slug, description=description)
    db.session.add(courier)
    db.session.commit()
    flash(f'Kurir {name} ditambahkan', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/courier/toggle/<int:id>', methods=['POST'])
@login_required
def admin_courier_toggle(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    courier = ShippingCourier.query.get_or_404(id)
    courier.is_active = not courier.is_active
    db.session.commit()
    status = 'diaktifkan' if courier.is_active else 'dinonaktifkan'
    flash(f'Kurir {courier.name} {status}', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/courier/delete/<int:id>', methods=['POST'])
@login_required
def admin_courier_delete(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    courier = ShippingCourier.query.get_or_404(id)
    name = courier.name
    db.session.delete(courier)
    db.session.commit()
    flash(f'Kurir {name} dihapus', 'success')
    return redirect(url_for('admin_shipping'))

# Zone Management
@app.route('/admin/shipping/zone/add', methods=['POST'])
@login_required
def admin_zone_add():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    name = request.form.get('name', '').strip()
    zone_code = request.form.get('zone_code', '').strip().upper()
    base_cost = int(request.form.get('base_cost', 0) or 0)
    cost_per_kg = int(request.form.get('cost_per_kg', 0) or 0)
    estimated_days = request.form.get('estimated_days', '').strip()
    
    if not name or not zone_code:
        flash('Nama dan kode zona wajib diisi', 'danger')
        return redirect(url_for('admin_shipping'))
    
    existing = ShippingZone.query.filter_by(zone_code=zone_code).first()
    if existing:
        flash('Kode zona sudah ada', 'warning')
        return redirect(url_for('admin_shipping'))
    
    zone = ShippingZone(name=name, zone_code=zone_code, base_cost=base_cost, 
                        cost_per_kg=cost_per_kg, estimated_days=estimated_days)
    db.session.add(zone)
    db.session.commit()
    flash(f'Zona {name} ditambahkan', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/zone/edit/<int:id>', methods=['POST'])
@login_required
def admin_zone_edit(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    zone = ShippingZone.query.get_or_404(id)
    zone.name = request.form.get('name', '').strip()
    zone.base_cost = int(request.form.get('base_cost', 0) or 0)
    zone.cost_per_kg = int(request.form.get('cost_per_kg', 0) or 0)
    zone.estimated_days = request.form.get('estimated_days', '').strip()
    db.session.commit()
    flash(f'Zona {zone.name} diupdate', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/zone/toggle/<int:id>', methods=['POST'])
@login_required
def admin_zone_toggle(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    zone = ShippingZone.query.get_or_404(id)
    zone.is_active = not zone.is_active
    db.session.commit()
    status = 'diaktifkan' if zone.is_active else 'dinonaktifkan'
    flash(f'Zona {zone.name} {status}', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/zone/delete/<int:id>', methods=['POST'])
@login_required
def admin_zone_delete(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    zone = ShippingZone.query.get_or_404(id)
    name = zone.name
    db.session.delete(zone)
    db.session.commit()
    flash(f'Zona {name} dihapus', 'success')
    return redirect(url_for('admin_shipping'))

# Free Shipping Promo
@app.route('/admin/shipping/promo/add', methods=['POST'])
@login_required
def admin_promo_add():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    name = request.form.get('name', '').strip()
    minpurchase = int(request.form.get('minpurchase', 0) or 0)
    max_discount = int(request.form.get('max_discount', 0) or 0)
    
    if not name:
        flash('Nama promo wajib diisi', 'danger')
        return redirect(url_for('admin_shipping'))
    
    promo = FreeShippingPromo(name=name, minpurchase=minpurchase, max_discount=max_discount)
    db.session.add(promo)
    db.session.commit()
    flash(f'Promo {name} ditambahkan', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/promo/toggle/<int:id>', methods=['POST'])
@login_required
def admin_promo_toggle(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    promo = FreeShippingPromo.query.get_or_404(id)
    promo.is_active = not promo.is_active
    db.session.commit()
    status = 'diaktifkan' if promo.is_active else 'dinonaktifkan'
    flash(f'Promo {promo.name} {status}', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/promo/delete/<int:id>', methods=['POST'])
@login_required
def admin_promo_delete(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    promo = FreeShippingPromo.query.get_or_404(id)
    name = promo.name
    db.session.delete(promo)
    db.session.commit()
    flash(f'Promo {name} dihapus', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/api-key', methods=['POST'])
@login_required
def admin_update_api_key():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    api_key = request.form.get('api_key', '').strip()
    
    # Save to database
    Setting.set('rajaongkir_api_key', api_key)
    
    flash('API Key RajaOngkir berhasil diupdate', 'success')
    return redirect(url_for('admin_shipping'))

@app.route('/admin/shipping/generate-app-key', methods=['POST'])
@login_required
def admin_generate_app_key():
    """Generate API key for mobile app"""
    if current_user.role != 'admin':
        flash('Unauthorized', 'error')
        return redirect(url_for('index'))
    
    timestamp = str(int(time.time()))
    api_key = hashlib.sha256(f'entokmart_app_{timestamp}'.encode()).hexdigest()[:32]
    
    Setting.set('app_api_key', api_key)
    
    flash(f'App API Key generated: {api_key}', 'success')
    return redirect(url_for('admin_shipping'))


@app.route('/admin/users')
@login_required
def admin_users():
    """Admin user management page - all users (buyers and sellers)"""
    if current_user.role != 'admin':
        flash('Unauthorized', 'error')
        return redirect(url_for('index'))
    
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    if status_filter == 'pending':
        query = query.filter_by(is_approved=False)
    elif status_filter == 'approved':
        query = query.filter_by(is_approved=True)
    
    users = query.order_by(User.created_at.desc()).all()
    
    # Count statistics
    total_users = User.query.count()
    total_sellers = User.query.filter_by(role='peternak').count()
    total_buyers = User.query.filter_by(role='buyer').count()
    pending_approvals = User.query.filter_by(is_approved=False).count()
    
    return render_template('admin_users.html',
                           title='Kelola User',
                           users=users,
                           role_filter=role_filter,
                           status_filter=status_filter,
                           total_users=total_users,
                           total_sellers=total_sellers,
                           total_buyers=total_buyers,
                           pending_approvals=pending_approvals)


@app.route('/admin/payment')
@login_required
def admin_payment():
    """Payment gateway settings page"""
    if current_user.role != 'admin':
        flash('Unauthorized', 'error')
        return redirect(url_for('index'))
    
    # Get current settings
    midtrans_server_key = Setting.get('midtrans_server_key', '')
    midtrans_client_key = Setting.get('midtrans_client_key', '')
    midtrans_production = Setting.get('midtrans_production', 'false')
    
    # Mask server key for display
    display_server_key = midtrans_server_key[:8] + '****' if midtrans_server_key else ''
    
    return render_template('admin_payment.html',
                           title='Kelola Payment Gateway',
                           midtrans_enabled=is_midtrans_enabled(),
                           midtrans_server_key=display_server_key,
                           midtrans_client_key=midtrans_client_key,
                           midtrans_production=midtrans_production == 'true')


@app.route('/admin/payment/midtrans', methods=['POST'])
@login_required
def admin_save_midtrans():
    """Save Midtrans configuration"""
    if current_user.role != 'admin':
        return {'success': False, 'message': 'Unauthorized'}, 403
    
    server_key = request.form.get('server_key', '').strip()
    client_key = request.form.get('client_key', '').strip()
    production = request.form.get('production', 'false')
    
    if server_key:
        Setting.set('midtrans_server_key', server_key)
    if client_key:
        Setting.set('midtrans_client_key', client_key)
    Setting.set('midtrans_production', production)
    
    app.config['MIDTRANS_SERVER_KEY'] = server_key
    app.config['MIDTRANS_CLIENT_KEY'] = client_key
    app.config['MIDTRANS_IS_PRODUCTION'] = production == 'true'
    
    flash('Midtrans configuration saved', 'success')
    return redirect(url_for('admin_payment'))

@app.route('/admin/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_user_edit(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user.username = request.form.get('username', '').strip()
        user.email = request.form.get('email', '').strip().lower()
        new_role = request.form.get('role', '')
        if new_role in ['peternak', 'buyer', 'admin']:
            user.role = new_role
        db.session.commit()
        flash('User berhasil diupdate', 'success')
        return redirect(url_for('dashboard_admin'))
    
    return render_template('admin_user_edit.html', user=user)

@app.route('/admin/user/delete/<int:id>')
@login_required
def admin_user_delete(id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if id == current_user.id:
        flash('Tidak bisa hapus diri sendiri', 'danger')
        return redirect(url_for('dashboard_admin'))
    
    user = User.query.get_or_404(id)
    
    # Delete related data first
    Chat.query.filter_by(user_id=user.id).delete()
    OrderItem.query.filter(OrderItem.order_id.in_(
        db.session.query(Order.id).filter(Order.buyer_id == user.id)
    )).delete(synchronize_session=False)
    Order.query.filter_by(buyer_id=user.id).delete()
    Product.query.filter_by(seller_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} dihapus', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/wishlist')
@login_required
def wishlist():
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@app.route('/wishlist/tambah/<int:product_id>')
@login_required
def wishlist_tambah(product_id):
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash('Produk sudah ada di wishlist', 'info')
    else:
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Ditambahkan ke wishlist', 'success')
    return redirect(url_for('wishlist'))

@app.route('/wishlist/hapus/<int:product_id>')
@login_required
def wishlist_hapus(product_id):
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Dihapus dari wishlist', 'success')
    return redirect(url_for('wishlist'))

@app.route('/bandingkan')
def bandingkan():
    ids = request.args.getlist('ids', type=int)
    if len(ids) < 2:
        flash('Pilih minimal 2 produk untuk dibandingkan', 'warning')
        return redirect(url_for('index'))
    
    products = Product.query.filter(Product.id.in_(ids[:4])).all()
    if len(products) < 2:
        flash('Minimal 2 produk diperlukan', 'warning')
        return redirect(url_for('index'))
    
    return render_template('bandingkan.html', products=products)

@app.route('/produk/compare/<int:product_id>')
def bandingkan_tambah(product_id):
    product = Product.query.get_or_404(product_id)
    compare_list = session.get('compare', [])
    if product_id not in compare_list:
        if len(compare_list) >= 4:
            flash('Maksimal 4 produk untuk dibandingkan', 'warning')
        else:
            compare_list.append(product_id)
    session['compare'] = compare_list
    flash(f'Produk "{product.name}" ditambahkan ke comparison', 'success')
    
    if len(compare_list) >= 2:
        return redirect(url_for('bandingkan', ids=compare_list))
    return redirect(url_for('index'))

@app.route('/produk/compare/clear')
def bandingkan_clear():
    session.pop('compare', None)
    flash('Comparison cleared', 'info')
    return redirect(url_for('index'))

@app.route('/chat')
@login_required
def chat():
    selected_user_id = request.args.get('user_id', type=int)
    app.logger.debug(f"CHAT DEBUG: user_id from args = {selected_user_id}, type = {type(selected_user_id)}")
    selected_user = None
    
    if current_user.role == 'admin':
        users_with_chats = User.query.join(Chat).distinct().all()
        user_chats = []
        
        if selected_user_id:
            selected_user = User.query.filter_by(id=selected_user_id).first()
            app.logger.error(f"CHAT DEBUG: selected_user = {selected_user}")
            if selected_user:
                user_chats = Chat.query.filter_by(user_id=selected_user_id).order_by(Chat.created_at.asc()).all()
                app.logger.error(f"CHAT DEBUG: chats count = {len(user_chats)}")
        
        return render_template('chat_admin.html', chats=user_chats, users=users_with_chats, selected_user=selected_user)
    else:
        chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.asc()).all()
        return render_template('chat.html', chats=chats)

@app.route('/chat/kirim', methods=['POST'])
@login_required
def chat_kirim():
    pesan = request.form.get('pesan', '').strip()
    if not pesan:
        flash('Pesan tidak boleh kosong', 'warning')
        return redirect(url_for('chat'))
    
    chat = Chat(user_id=current_user.id, pesan=pesan, is_from_admin=False)
    db.session.add(chat)
    db.session.commit()
    
    # Telegram notification to admin
    telegram_notify_chat(current_user.username, pesan)
    
    flash('Pesan terkirim', 'success')
    return redirect(url_for('chat'))

@app.route('/chat/admin/kirim/<int:user_id>', methods=['POST'])
@login_required
def chat_admin_kirim(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    pesan = request.form.get('pesan', '').strip()
    if not pesan:
        return redirect(url_for('chat'))
    
    chat = Chat(user_id=user_id, pesan=pesan, is_from_admin=True)
    db.session.add(chat)
    db.session.commit()
    return redirect(url_for('chat'))

@app.route('/chat/read/<int:user_id>')
@login_required
def chat_read(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    Chat.query.filter_by(user_id=user_id, is_from_admin=False, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('chat', user_id=user_id))

@app.route('/produk/<int:product_id>/review', methods=['GET', 'POST'])
@login_required
def produk_review(product_id):
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    existing_review = Review.query.filter_by(product_id=product_id, buyer_id=current_user.id).first()
    if existing_review:
        flash('Anda sudah pernah memberi review', 'info')
        return redirect(url_for('index'))
    
    purchased = OrderItem.query.filter_by(product_id=product_id).join(Order).filter(Order.buyer_id == current_user.id).first()
    if not purchased:
        flash('Anda harus membeli produk ini terlebih dahulu untuk memberi review', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        rating = int(request.form.get('rating', 0))
        komentar = request.form.get('komentar', '').strip()
        
        if rating < 1 or rating > 5:
            flash('Rating harus 1-5', 'danger')
            return redirect(url_for('produk_review', product_id=product_id))
        
        review = Review(product_id=product_id, buyer_id=current_user.id, rating=rating, komentar=komentar)
        db.session.add(review)
        db.session.commit()
        flash('Review berhasil ditambahkan', 'success')
        return redirect(url_for('index'))
    
    return render_template('review.html', product=product)
# ======================
# TELEGRAM INTEGRATION
# ======================
import requests as req

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7157068412:AAEkomBO_qCBW7SfUvblefqJ-WL6m8TZluk')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '6054204698')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def telegram_send_message(text):
    try:
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
        req.post(f'{TELEGRAM_API_URL}/sendMessage', data=data, timeout=10)
        return True
    except Exception as e:
        app.logger.error(f'Telegram send error: {e}')
        return False

def format_telegram_pesanan(order):
    return f"""
<b>🛒 Pesanan Baru #${order.id}</b>

<b>Pembeli:</b> {order.buyer.username}
<b>Total:</b> Rp {order.total_harga:,}
<b>Metode:</b> {order.payment_method.upper()}
<b>Status:</b> {order.status}

<a href="http://127.0.0.1:5003/pesanan">Lihat di EntokMart</a>
"""

def format_telegram_chat(username, pesan):
    return f"<b>💬 Chat dari {username}:</b>\n{pesan}\n\n<a href=\"http://127.0.0.1:5003/chat\">Balas di EntokMart</a>"

# ======================
# PUBLIC API FOR APPLICATIONS
# ======================
import hashlib
import time

def validate_api_key(api_key):
    """Validate API key from request header"""
    if not api_key:
        return False, 'API Key required'
    
    # Check if it's the stored API key
    stored_key = Setting.get('app_api_key')
    if stored_key and api_key == stored_key:
        return True, 'Valid'
    
    # Also allow the default key in config
    default_key = app.config.get('API_KEY', '')
    if default_key and api_key == default_key:
        return True, 'Valid'
    
    return False, 'Invalid API Key'

def require_api_key(f):
    """Decorator to require API key"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        valid, msg = validate_api_key(api_key)
        if not valid:
            return {'success': False, 'message': msg}, 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/v1/products')
def api_products():
    """Get all products (public)"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Product.query.filter(Product.stok > 0)
    
    if category:
        query = query.filter(Product.jenis == category)
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page)
    
    result = {
        'success': True,
        'data': [{
            'id': p.id,
            'name': p.name,
            'jenis': p.jenis,
            'harga': p.harga,
            'berat_kg': p.berat_kg,
            'stok': p.stok,
            'deskripsi': p.deskripsi,
            'image_url': p.image_url,
            'seller': {
                'id': p.seller.id,
                'username': p.seller.username,
                'nama_toko': p.seller.nama_toko
            },
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in products.items],
        'pagination': {
            'page': products.page,
            'per_page': products.per_page,
            'total': products.total,
            'pages': products.pages
        }
    }
    return result

@app.route('/api/v1/products/<int:product_id>')
def api_product_detail(product_id):
    """Get product detail (public)"""
    product = Product.query.get_or_404(product_id)
    
    return {
        'success': True,
        'data': {
            'id': product.id,
            'name': product.name,
            'jenis': product.jenis,
            'harga': product.harga,
            'berat_kg': product.berat_kg,
            'stok': product.stok,
            'deskripsi': product.deskripsi,
            'image_url': product.image_url,
            'seller': {
                'id': product.seller.id,
                'username': product.seller.username,
                'nama_toko': product.seller.nama_toko,
                'no_hp': product.seller.no_hp,
                'alamat': product.seller.alamat
            },
            'created_at': product.created_at.isoformat() if product.created_at else None
        }
    }

@app.route('/api/v1/categories')
@cache.cached(timeout=300)
def api_categories():
    """Get all categories (public)"""
    categories = Category.query.all()
    return {
        'success': True,
        'data': [{
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'description': c.description
        } for c in categories]
    }

@app.route('/api/v1/sellers')
def api_sellers():
    """Get all sellers (public)"""
    sellers = User.query.filter(
        User.role == 'peternak',
        User.nama_toko != None
    ).all()
    
    return {
        'success': True,
        'data': [{
            'id': s.id,
            'username': s.username,
            'nama_toko': s.nama_toko,
            'deskripsi_toko': s.deskripsi_toko,
            'no_hp': s.no_hp,
            'alamat': s.alamat,
            'verifikasi': s.verifikasi
        } for s in sellers]
    }

@app.route('/api/v1/sellers/<username>')
def api_seller_detail(username):
    """Get seller detail and products (public)"""
    seller = User.query.filter_by(username=username).first_or_404()
    
    if not seller.nama_toko:
        return {'success': False, 'message': 'Toko tidak ditemukan'}, 404
    
    products = Product.query.filter_by(seller_id=seller.id, stok__gt=0).all()
    
    return {
        'success': True,
        'data': {
            'seller': {
                'id': seller.id,
                'username': seller.username,
                'nama_toko': seller.nama_toko,
                'deskripsi_toko': seller.deskripsi_toko,
                'no_hp': seller.no_hp,
                'alamat': seller.alamat,
                'verifikasi': seller.verifikasi
            },
            'products': [{
                'id': p.id,
                'name': p.name,
                'jenis': p.jenis,
                'harga': p.harga,
                'berat_kg': p.berat_kg,
                'stok': p.stok,
                'image_url': p.image_url
            } for p in products]
        }
    }

@app.route('/api/v1/orders/<int:order_id>')
def api_order_tracking(order_id):
    """Track order by ID (public with order code)"""
    order_code = request.args.get('code', '')
    
    order = Order.query.get_or_404(order_id)
    
    # Validate code or buyer
    if order_code or (current_user.is_authenticated and current_user.id == order.buyer_id):
        return {
            'success': True,
            'data': {
                'id': order.id,
                'status': order.status,
                'payment_status': order.payment_status,
                'payment_method': order.payment_method,
                'total_harga': order.total_harga,
                'ongkir': order.ongkir,
                'resi': order.resi,
                'nama_penerima': order.nama_penerima,
                'alamat': order.alamat,
                'telp': order.telp,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'items': [{
                    'name': item.nama_product,
                    'jumlah': item.jumlah,
                    'harga': item.harga_saat_beli
                } for item in order.items]
            }
        }
    
    return {'success': False, 'message': 'Unauthorized'}, 401

@app.route('/api/v1/zones')
def api_shipping_zones():
    """Get shipping zones (public)"""
    zones = ShippingZone.query.filter_by(is_active=True).all()
    
    return {
        'success': True,
        'data': [{
            'id': z.id,
            'name': z.name,
            'zone_code': z.zone_code,
            'base_cost': z.base_cost,
            'cost_per_kg': z.cost_per_kg,
            'estimated_days': z.estimated_days
        } for z in zones]
    }

@app.route('/api/v1/calculate-shipping', methods=['POST'])
@csrf.exempt
def api_calculate_shipping():
    """Calculate shipping cost"""
    data = request.get_json()
    if not data:
        return {'success': False, 'message': 'Invalid JSON'}, 400
    weight = float(data.get('weight', 0))
    zone_code = data.get('zone_code', '')
    
    if weight <= 0:
        return {'success': False, 'message': 'Weight required'}
    
    cost = calculate_shipping_cost(weight, zone_code)
    
    return {
        'success': True,
        'data': {
            'weight_kg': weight,
            'zone_code': zone_code,
            'cost': cost
        }
    }

@app.route('/api/v1/generate-key', methods=['POST'])
@login_required
def api_generate_key():
    """Generate new API key (admin only)"""
    if current_user.role != 'admin':
        return {'success': False, 'message': 'Unauthorized'}, 403
    
    # Generate random API key
    timestamp = str(int(time.time()))
    api_key = hashlib.sha256(f'entokmart_{timestamp}'.encode()).hexdigest()[:32]
    
    # Save to settings
    Setting.set('app_api_key', api_key)
    
    return {
        'success': True,
        'message': 'API Key generated',
        'api_key': api_key
    }


@app.route('/api/v1/payment/methods')
def api_payment_methods():
    """Get available payment methods"""
    return {
        'success': True,
        'methods': get_payment_methods(),
        'midtrans_enabled': is_midtrans_enabled()
    }


@app.route('/api/v1/payment/create-snap', methods=['POST'])
@login_required
def api_create_snap():
    """Create Midtrans Snap token for payment"""
    if not is_midtrans_enabled():
        return {'success': False, 'message': 'Payment gateway not configured'}, 400
    
    data = request.get_json()
    order_id = data.get('order_id')
    amount = data.get('amount')
    
    if not order_id or not amount:
        return {'success': False, 'message': 'Missing order_id or amount'}, 400
    
    # Get order details
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        return {'success': False, 'message': 'Order not found'}, 404
    
    if order.total_harga != amount:
        return {'success': False, 'message': 'Amount mismatch'}, 400
    
    # Build customer details
    customer_details = {
        'first_name': current_user.username,
        'email': current_user.email,
        'phone': current_user.phone or '',
    }
    
    # Build item details
    item_details = []
    for item in order.items:
        item_details.append({
            'id': str(item.id),
            'name': item.product.name,
            'price': int(item.price),
            'quantity': item.quantity,
        })
    
    # Add shipping as item
    if order.shipping_cost > 0:
        item_details.append({
            'id': 'shipping',
            'name': 'Biaya Pengiriman',
            'price': int(order.shipping_cost),
            'quantity': 1,
        })
    
    # Create Snap token
    result = create_snap_token(order_id, amount, customer_details, item_details)
    
    if result.get('success'):
        # Update order payment method
        order.payment_method = 'midtrans'
        order.payment_token = result.get('token')
        db.session.commit()
        
        return {
            'success': True,
            'token': result.get('token'),
            'redirect_url': result.get('redirect_url'),
        }
    else:
        return {'success': False, 'message': result.get('message')}, 500


@app.route('/api/v1/payment/status/<int:order_id>')
@login_required
def api_payment_status(order_id):
    """Check payment status for an order"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        return {'success': False, 'message': 'Order not found'}, 404
    
    if order.payment_method != 'midtrans':
        return {'success': False, 'message': 'Not a Midtrans payment'}, 400
    
    result = check_transaction_status(order_id)
    
    if result.get('success'):
        midtrans_status = result['data'].get('transaction_status', '')
        payment_status = get_midtrans_status_from_code(midtrans_status)
        
        return {
            'success': True,
            'order_id': order_id,
            'payment_status': payment_status,
            'midtrans_status': midtrans_status,
            'data': result['data']
        }
    else:
        return {'success': False, 'message': result.get('message')}, 500


@app.route('/api/v1/payment/notification', methods=['POST'])
def api_payment_notification():
    """Midtrans webhook notification handler"""
    data = request.get_json()
    
    order_id = data.get('order_id')
    status = data.get('transaction_status')
    
    if not order_id:
        return jsonify({'status': 'ok'}), 200
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'status': 'ok'}), 200
    
    # Update order status based on Midtrans notification
    payment_status = get_midtrans_status_from_code(status)
    
    if payment_status == 'confirmed':
        order.status = 'paid'
        order.payment_status = 'paid'
        order.midtrans_status = status
        
        # Update order items stock
        for item in order.items:
            product = item.product
            if product.stock >= item.quantity:
                product.stock -= item.quantity
        
        db.session.commit()
        
        # Send notification via Telegram
        try:
            from services.telegram import send_order_notification
            send_order_notification(order, 'paid')
        except:
            pass
    
    elif payment_status == 'failed':
        order.status = 'payment_failed'
        order.payment_status = 'failed'
        order.midtrans_status = status
        db.session.commit()
    
    return jsonify({'status': 'ok'}), 200


@app.route('/api/v1/payment/client-key')
def api_payment_client_key():
    """Get Midtrans client key for frontend"""
    config = get_midtrans_config()
    return {
        'success': True,
        'client_key': config.get('client_key', ''),
        'enabled': is_midtrans_enabled()
    }
