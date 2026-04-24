from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship('User', backref='products')

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