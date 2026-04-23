# E-Commerce Marketplace Entok - Specification

## 1. Project Overview
- **Nama**: EntokMart - Marketplace Penjualan Entok
- **Tipe**: E-commerce marketplace multi-vendor
- **Tech Stack**: Python (Flask) + SQLite + Bootstrap 5

## 2. Fitur Utama

### 2.1 Untuk Peternak (Seller)
- Registrasi/login akun peternak
-/upload foto entok (jenis, berat, harga, deskripsi)
- Kelola daftar produk
- Lihat pesanan masuk

### 2.2 Untuk Pembeli (Buyer)
- Registrasi/login akun buyer  
- Browse katalog entok dari semua peternak
- Tambah ke keranjang belanja
- Checkout dan pembayaran
- Tracking status pesanan

### 2.3 Admin
- Kelola semua user (peternak/buyer)
- Kelola semua pesanan

## 3. Data Model

### User
- id, username, email, password_hash, role (peternak/buyer/admin), created_at

### Product
- id, seller_id, name, jenis (entok muda/entokAFKIR/entok培), berat_kg, harga, deskripsi, image_url, created_at

### Order
- id, buyer_id, total_harga, status (pending/diproses/dikirim/selesai), created_at

### OrderItem
- id, order_id, product_id, jumlah, harga_saat_beli

## 4. halaman
- / (home - katalog)
- /login, /register
- /dashboard-peternak
- /dashboard-buyer
- /produk/baru (tambah produk)
- /keranjang
- /checkout
- /pesanan (tracking)
- /admin

## 5. Hujan Langkah
1. Setup Flask + SQLAlchemy
2. Buat model database
3. Buat auth (register/login)
4. Buat CRUD produk
5. Buat keranjang +checkout
6. Buat tracking pesanan
7. Template + styling