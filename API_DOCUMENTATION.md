# EntokMart API Documentation

## Base URL
```
http://your-server:5003/api/v1
```

## Authentication
Untuk endpoints yang memerlukan auth, gunakan header:
```
X-API-Key: your-app-api-key
```

---

## Public Endpoints (No Auth Required)

### 1. Get All Products
```
GET /products
```
**Query Parameters:**
- `page` (optional, default: 1)
- `per_page` (optional, default: 20)
- `category` (optional) - Filter by category name
- `search` (optional) - Search by product name

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Entok Muda Bibit",
      "jenis": "Entok Muda (Bibit)",
      "harga": 75000,
      "berat_kg": 1.5,
      "stok": 10,
      "deskripsi": "Entok muda usia 1 bulan",
      "image_url": "https://...",
      "seller": {
        "id": 1,
        "username": "peternak_test",
        "nama_toko": "Toko Entok Maju"
      },
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3
  }
}
```

### 2. Get Product Detail
```
GET /products/{id}
```

### 3. Get Categories
```
GET /categories
```
**Response:**
```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "Entok Muda (Bibit)", "slug": "entok-muda", "description": "..."},
    {"id": 2, "name": "Entok Dewasa", "slug": "entok-dewasa", "description": "..."}
  ]
}
```

### 4. Get All Sellers
```
GET /sellers
```

### 5. Get Seller Detail with Products
```
GET /sellers/{username}
```

### 6. Get Shipping Zones
```
GET /zones
```
**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Jabodetabek",
      "zone_code": "JABODETABEK",
      "base_cost": 5000,
      "cost_per_kg": 3000,
      "estimated_days": "1-2 hari"
    }
  ]
}
```

### 7. Calculate Shipping Cost
```
POST /calculate-shipping
```
**Body:**
```json
{
  "weight": 2.5,
  "zone_code": "JAWA"
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "weight_kg": 2.5,
    "zone_code": "JAWA",
    "cost": 18000
  }
}
```

### 8. Track Order
```
GET /orders/{order_id}?code={order_code}
```

---

## App API Key

Generate API key di admin: **Dashboard → Kelola Ongkir → Generate App API Key**

Gunakan key tersebut di header `X-API-Key` untuk akses yang memerlukan autentikasi.

---

## Mobile App Integration

### React Native / Expo
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://your-server:5003/api/v1',
});

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('api_token');
  if (token) {
    config.headers['X-API-Key'] = token;
  }
  return config;
});

// Get products
const response = await api.get('/products');
```

### Flutter
```dart
import 'package:http/http.dart' as http;

final response = await http.get(
  Uri.parse('http://your-server:5003/api/v1/products'),
  headers: {'X-API-Key': 'your-api-key'},
);
```

---

## Error Responses

```json
{
  "success": false,
  "message": "Error description"
}
```

Status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Server Error

---

## Payment Endpoints

### 1. Get Payment Methods
```
GET /payment/methods
```
**Response:**
```json
{
  "success": true,
  "methods": [
    {"code": "credit_card", "name": "Kartu Kredit", "icon": "💳"},
    {"code": "bca_va", "name": "BCA VA", "icon": "🏦"},
    ...
  ],
  "midtrans_enabled": true
}
```

### 2. Create Snap Payment Token (Auth Required)
```
POST /payment/create-snap
```
**Headers:** `X-API-Key: your-api-key`

**Body:**
```json
{
  "order_id": 1,
  "amount": 150000
}
```

**Response:**
```json
{
  "success": true,
  "token": "midtrans-token-here",
  "redirect_url": "https://..."
}
```

### 3. Check Payment Status (Auth Required)
```
GET /payment/status/{order_id}
```
**Headers:** `X-API-Key: your-api-key`

**Response:**
```json
{
  "success": true,
  "order_id": 1,
  "payment_status": "confirmed",
  "midtrans_status": "settlement",
  "data": {...}
}
```

### 4. Get Client Key (Public)
```
GET /payment/client-key
```
**Response:**
```json
{
  "success": true,
  "client_key": "your-client-key",
  "enabled": true
}
```

### 5. Payment Notification (Webhook)
```
POST /payment/notification
```
Midtrans webhook callback - tidak perlu menggunakan ini dari mobile app.