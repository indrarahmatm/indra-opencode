export const API_URL = 'http://YOUR_SERVER_IP:5003/api/v1';

export const COLORS = {
  primary: '#2E7D32',
  primaryDark: '#1B5E20',
  primaryLight: '#4CAF50',
  secondary: '#FF9800',
  background: '#FFFFFF',
  surface: '#F5F5F5',
  text: '#212121',
  textSecondary: '#757575',
  border: '#E0E0E0',
  error: '#D32F2F',
  success: '#388E3C',
  warning: '#F57C00',
};

export const STORAGE_KEYS = {
  API_TOKEN: 'api_token',
  USER_DATA: 'user_data',
  CART: 'cart',
  RECENT_SEARCH: 'recent_search',
  FAVORITES: 'favorites',
};

export const SHIPPING_ZONES = {
  JABODETABEK: 'JABODETABEK',
  JAWA: 'JAWA',
  SUMATERA: 'SUMATERA',
  KALIMANTAN: 'KALIMANTAN',
};

export const PAYMENT_METHODS = {
  COD: 'cod',
  MANUAL: 'manual',
};

export const ORDER_STATUS = {
  PENDING: 'pending',
  DIPROSES: 'diproses',
  DIKIRIM: 'dikirim',
  SELESAI: 'selesai',
  DIBATALKAN: 'dibatalkan',
};

export const formatCurrency = (amount) => {
  return 'Rp ' + amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
};

export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('id-ID', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
};

export const truncateText = (text, maxLength) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};