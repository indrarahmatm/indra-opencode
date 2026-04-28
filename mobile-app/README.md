# EntokMart Mobile App

React Native (Expo) Mobile Application for EntokMart E-Commerce Platform.

## 📱 Features

### Core Features
- ✅ Browse products by category
- ✅ Search products
- ✅ View product details
- ✅ Add to cart
- ✅ Cart management
- ✅ Order tracking
- ✅ Secure online payments (Midtrans integration)

### Tech Stack
- **Framework**: React Native with Expo
- **Navigation**: React Navigation (Bottom Tabs + Native Stack)
- **API Client**: Axios
- **Storage**: AsyncStorage

## 🚀 Installation

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn
- Expo CLI

### Steps

1. **Clone and Install Dependencies**
```bash
cd mobile-app
npm install
```

2. **Configure API URL**
Edit `src/utils/constants.js`:
```javascript
export const API_URL = 'http://YOUR_SERVER_IP:5003/api/v1';
```

Replace `YOUR_SERVER_IP` with your actual server IP address (for local testing use computer's local IP, not localhost).

3. **Generate API Key**
- Login to admin dashboard
- Go to **Kelola Ongkir** → **API Key**
- Click **Generate App API Key Baru**
- Copy the generated key

4. **Run Development Server**
```bash
npx expo start
```

5. **Run on Device/Emulator**
- Scan QR code with Expo Go app (Android/iOS)
- Or press 'a' for Android emulator
- Or press 'i' for iOS simulator

## 📁 Project Structure

```
mobile-app/
├── App.js                    # Main entry point
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Button.js
│   │   └── ProductCard.js
│   ├── context/              # State management
│   │   ├── AuthContext.js
│   │   └── CartContext.js
│   ├── navigation/          # Navigation config (future)
│   ├── screens/            # Screen components
│   │   ├── HomeScreen.js
│   │   ├── ProductDetailScreen.js
│   │   ├── CategoriesScreen.js
│   │   ├── CartScreen.js
│   │   ├── OrdersScreen.js
│   │   └── ProfileScreen.js
│   ├── services/            # API services
│   │   └── api.js
│   ├── utils/               # Utilities and constants
│   │   └── constants.js
│   └── hooks/               # Custom hooks (future)
└── package.json
```

## 🔌 API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/products` | GET | Get all products |
| `/products/{id}` | GET | Get product detail |
| `/categories` | GET | Get all categories |
| `/sellers` | GET | Get all sellers |
| `/zones` | GET | Get shipping zones |
| `/calculate-shipping` | POST | Calculate shipping cost |
| `/orders/{id}` | GET | Track order |

## 📱 Mobile Features by Role

### Guest (Unauthenticated)
- Browse products
- Search products
- View categories
- View product details

### Authenticated User
- All guest features
- Add to cart
- Manage cart
- Track orders

## 🔧 Configuration

### Changing API Base URL
Edit `src/utils/constants.js`:
```javascript
export const API_URL = 'http://192.168.1.100:5003/api/v1';
```

### Changing App Colors
Edit `src/utils/constants.js`:
```javascript
export const COLORS = {
  primary: '#2E7D32',    // Your brand color
  // ... other colors
};
```

## ⚠️ Important Notes

1. **Network**: Mobile app must be on same network as server for local testing
2. **Server IP**: Use local IP address (e.g., 192.168.x.x), not localhost
3. **API Key**: For authenticated features, generate API key from admin dashboard
4. **Login**: Currently login must be done through web interface

## 🛠️ Build for Production

### Android
```bash
npx expo build:android
```

### iOS
```bash
npx expo build:ios
```

## 📄 License

MIT License - EntokMart 2024

## 👨‍💻 Support

For issues or questions, please contact the development team.