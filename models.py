from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta

def get_wib():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Vendor/Store fields
    nama_toko = db.Column(db.String(150), nullable=True)
    deskripsi_toko = db.Column(db.Text, nullable=True)
    no_hp = db.Column(db.String(20), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    verifikasi = db.Column(db.Boolean, default=False)
    
    token_reset = db.Column(db.String(100), nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    jenis = db.Column(db.String(50), nullable=False)
    berat_kg = db.Column(db.Float, nullable=False)
    harga = db.Column(db.Integer, nullable=False)
    deskripsi = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    stok = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship('User', backref='products')
    reviews = db.relationship('Review', backref='product', cascade='all, delete-orphan')
    images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan')

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    komentar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    buyer = db.relationship('User', backref='reviews')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='wishlists')
    product = db.relationship('Product')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    
    @staticmethod
    def get_default_categories():
        defaults = [
            {'name': 'Entok Muda (Bibit)', 'slug': 'entok-muda', 'description': 'Entok usia muda untuk bibit'},
            {'name': 'Entok Afkir (Dewasa)', 'slug': 'entok-afkir', 'description': 'Entok dewasa afkir produktif'},
            {'name': 'Entok Pandet', 'slug': 'entok-pandet', 'description': 'Entok pandet berkualitas'},
            {'name': 'Telur Entok', 'slug': 'telur-entok', 'description': 'Telur entok segar'},
            {'name': 'Daging Entok', 'slug': 'daging-entok', 'description': 'Daging entok segar'},
            {'name': 'Pakan & Obat', 'slug': 'pakan-obat', 'description': 'Pakan dan obat-obatan ternak'},
        ]
        for d in defaults:
            if not Category.query.filter_by(slug=d['slug']).first():
                cat = Category(**d)
                db.session.add(cat)


class ShippingCourier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    logo = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ShippingZone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zone_code = db.Column(db.String(20), nullable=False, unique=True)
    base_cost = db.Column(db.Integer, default=0)
    cost_per_kg = db.Column(db.Integer, default=0)
    estimated_days = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)


class FreeShippingPromo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    minpurchase = db.Column(db.Integer, default=0)
    max_discount = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Setting(db.Model):
    """App settings stored in database"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get(key, default=''):
        s = Setting.query.filter_by(key=key).first()
        return s.value if s else default
    
    @staticmethod
    def set(key, value):
        s = Setting.query.filter_by(key=key).first()
        if s:
            s.value = value
        else:
            s = Setting(key=key, value=value)
            db.session.add(s)
        db.session.commit()


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pesan = db.Column(db.Text, nullable=False)
    is_from_admin = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='chats')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_harga = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default='pending')
    nama_penerima = db.Column(db.String(150))
    alamat = db.Column(db.Text)
    telp = db.Column(db.String(20))
    # Payment fields
    payment_method = db.Column(db.String(20), default='cod')  # 'cod', 'manual'
    payment_status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'failed'
    bank_name = db.Column(db.String(50))
    bank_account = db.Column(db.String(50))
    transfer_proof_url = db.Column(db.String(300))
    # Shipping
    resi = db.Column(db.String(50))
    ongkir = db.Column(db.Integer, default=0)
    # Seller payment
    seller_paid = db.Column(db.Boolean, default=False)
    seller_paid_at = db.Column(db.DateTime)
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    harga_saat_beli = db.Column(db.Integer, nullable=False)
    nama_product = db.Column(db.String(150))
    nama_peternak = db.Column(db.String(150))

    product = db.relationship('Product')