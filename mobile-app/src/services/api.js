import axios from 'axios';
import { API_URL } from '../utils/constants';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const apiKey = global.API_KEY || null;
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

export const ProductService = {
  getAll: (page = 1, perPage = 20, category = null, search = null) => {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', perPage);
    if (category) params.append('category', category);
    if (search) params.append('search', search);
    return apiClient.get(`/products?${params.toString()}`);
  },

  getById: (id) => apiClient.get(`/products/${id}`),
};

export const CategoryService = {
  getAll: () => apiClient.get('/categories'),
};

export const SellerService = {
  getAll: () => apiClient.get('/sellers'),
  getByUsername: (username) => apiClient.get(`/sellers/${username}`),
};

export const ShippingService = {
  getZones: () => apiClient.get('/zones'),
  calculateShipping: (zoneCode, weight) => 
    apiClient.post('/calculate-shipping', { zone_code: zoneCode, weight }),
};

export const OrderService = {
  getById: (orderId) => apiClient.get(`/orders/${orderId}`),
};

export const PaymentService = {
  getMethods: () => apiClient.get('/payment/methods'),
  
  createSnapToken: (orderId, amount) => 
    apiClient.post('/payment/create-snap', { order_id: orderId, amount }),
  
  getStatus: (orderId) => apiClient.get(`/payment/status/${orderId}`),
  
  getClientKey: () => apiClient.get('/payment/client-key'),
};

export const setApiKey = (key) => {
  global.API_KEY = key;
};

export default apiClient;