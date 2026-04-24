import re
import os
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, mail, db
from models import User, Product, Order, OrderItem, Review, Wishlist

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
    return render_template('index.html', products=products)

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
    return render_template('index.html', products=products, search_query=q, jenis_filter=jenis_filter)

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

@app.route('/dashboard-peternak')
@login_required
def dashboard_peternak():
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    products = Product.query.filter_by(seller_id=current_user.id).all()
    return render_template('dashboard_peternak.html', products=products)

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
            flash('Produk berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard_peternak'))
        except (ValueError, TypeError):
            flash('Input tidak valid', 'danger')
            return redirect(url_for('produk_baru'))
    return render_template('produk_baru.html')

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

            if product.berat_kg <= 0 or product.berat_kg > 50 or product.harga <= 0 or product.stok < 0:
                flash('Input tidak valid', 'danger')
                return redirect(url_for('produk_edit', id=id))

            db.session.commit()
            flash('Produk berhasil diupdate', 'success')
            return redirect(url_for('dashboard_peternak'))
        except (ValueError, TypeError):
            flash('Input tidak valid', 'danger')
            return redirect(url_for('produk_edit', id=id))
    return render_template('produk_edit.html', product=product)

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

        total_harga = 0
        insufficient_stock = []
        for item in cart:
            product = Product.query.get(item['product_id'])
            if product:
                if item['jumlah'] > product.stok:
                    insufficient_stock.append(f"{product.name} (tersedia: {product.stok})")
                total_harga += product.harga * item['jumlah']
        
        if insufficient_stock:
            flash(f'Stok tidak mencukupi: {", ".join(insufficient_stock)}', 'danger')
            return redirect(url_for('keranjang'))

        order = Order(buyer_id=current_user.id, total_harga=total_harga,
                     nama_penerima=nama_penerima, alamat=alamat, telp=telp,
                     payment_method=payment_method, payment_status='pending')
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
        
        flash(f'Pesanan berhasil dibuat! ({payment_method.upper()})', 'success')
        return redirect(url_for('pesanan_saya'))

    total = 0
    for item in cart:
        product = Product.query.get(item['product_id'])
        if product:
            total += product.harga * item['jumlah']
    return render_template('checkout.html', total=total)

@app.route('/pesanan-saya')
@login_required
def pesanan_saya():
    if current_user.role != 'buyer':
        return redirect(url_for('index'))
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('pesanan_saya.html', orders=orders)

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
    return render_template('dashboard_admin.html', users=users, orders=orders)

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