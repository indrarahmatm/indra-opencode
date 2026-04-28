import re
import os
import io
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, send_from_directory, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, mail, db, csrf
from models import User, Product, Order, OrderItem, Review, Wishlist, Category, ProductImage, Chat
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
            login_user(user, remember=True)
            flash('Login berhasil', 'success')
            if user.role == 'peternak':
                return redirect(url_for('dashboard_peternak'))
            elif user.role == 'buyer':
                return redirect(url_for('dashboard_buyer'))
            else:
                return redirect(url_for('dashboard_admin'))
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
    if current_user.role != 'peternak':
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
            flash(f'Stok tidak mencukupi. Total di keranjang: {existing["jumlah"] + product.stok}', 'warning')
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
        
        # Calculate shipping cost (ongkir)
        if total_weight_kg <= 0:
            ongkir = 0
        else:
            # Base cost 5000 for first kg, then 3000 per additional kg
            ongkir = int(5000 + max(0, (total_weight_kg - 1) * 3000))
        
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
    return render_template('checkout.html', subtotal=subtotal, ongkir=ongkir, total=total_harga)

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
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    items = OrderItem.query.filter_by(nama_peternak=current_user.username).all()
    return render_template('pesanan.html', items=items)

@app.route('/laporan')
@login_required
def laporan():
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    
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
    if current_user.role != 'peternak':
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
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'recent_orders': recent_orders,
        'top_products': top_products
    }
    
    return render_template('dashboard_admin.html', users=users, orders=orders, stats=stats)

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
