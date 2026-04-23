from flask import render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app
from models import db, User, Product, Order, OrderItem

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

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
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            session.clear()
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
            image_url = request.form.get('image_url', '').strip()

            if not name or len(name) > 150:
                flash('Nama produk tidak valid', 'danger')
                return redirect(url_for('produk_baru'))
            if berat_kg <= 0 or berat_kg > 50:
                flash('Berat harus antara 0-50 kg', 'danger')
                return redirect(url_for('produk_baru'))
            if harga <= 0:
                flash('Harga tidak valid', 'danger')
                return redirect(url_for('produk_baru'))

            product = Product(seller_id=current_user.id, name=name, jenis=jenis,
                           berat_kg=berat_kg, harga=harga, deskripsi=deskripsi, image_url=image_url)
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
            product.image_url = request.form.get('image_url', '').strip()

            if product.berat_kg <= 0 or product.berat_kg > 50 or product.harga <= 0:
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
    jumlah = int(request.form.get('jumlah', 1))
    cart = session.get('cart', [])

    existing = next((item for item in cart if item['product_id'] == product_id), None)
    if existing:
        existing['jumlah'] += jumlah
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
        nama_penerima = request.form['nama_penerima']
        alamat = request.form['alamat']
        telp = request.form['telp']

        total_harga = 0
        for item in cart:
            product = Product.query.get(item['product_id'])
            if product:
                total_harga += product.harga * item['jumlah']

        order = Order(buyer_id=current_user.id, total_harga=total_harga,
                     nama_penerima=nama_penerima, alamat=alamat, telp=telp)
        db.session.add(order)
        db.session.commit()

        for item in cart:
            product = Product.query.get(item['product_id'])
            if product:
                order_item = OrderItem(order_id=order.id, product_id=product.id,
                                   jumlah=item['jumlah'], harga_saat_beli=product.harga,
                                   nama_product=product.name, nama_peternak=product.seller.username)
                db.session.add(order_item)

        db.session.commit()
        session['cart'] = []
        flash('Pesanan berhasil dibuat!', 'success')
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

@app.route('/pesanan')
@login_required
def pesanan():
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    items = OrderItem.query.filter_by(nama_peternak=current_user.username).all()
    return render_template('pesanan.html', items=items)

@app.route('/pesanan/update/<int:id>', methods=['POST'])
@login_required
def pesanan_update(id):
    if current_user.role != 'peternak':
        return redirect(url_for('index'))
    order = Order.query.get_or_404(id)
    order.status = request.form['status']
    db.session.commit()
    flash('Status pesanan diupdate', 'success')
    return redirect(url_for('pesanan'))

@app.route('/admin')
@login_required
def dashboard_admin():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    users = User.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('dashboard_admin.html', users=users, orders=orders)