const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

let _token = null;

export const setToken = (t) => { _token = t; };
export const getToken = () => _token;

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(_token ? { Authorization: `Bearer ${_token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Error del servidor');
  return data;
}

// Auth
export const register = (name, email, phone, password) =>
  request('/auth/register', { method: 'POST', body: JSON.stringify({ name, email, phone, password }) });

export const login = (email, password) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });

export const getMe = () => request('/users/me');

export const updateMe = (data) =>
  request('/users/me', { method: 'PUT', body: JSON.stringify(data) });

// Stores
export const createStore = (data) =>
  request('/stores/', { method: 'POST', body: JSON.stringify(data) });

export const getStores = () => request('/stores/');

export const updateStore = (id, data) =>
  request(`/stores/${id}`, { method: 'PUT', body: JSON.stringify(data) });

export const deleteStore = (id) =>
  request(`/stores/${id}`, { method: 'DELETE' });

// Products
export const getProducts = () => request('/products/');

// Orders
export const createDraft = (data) =>
  request('/orders/draft', { method: 'POST', body: JSON.stringify(data) });

export const confirmOrder = (id) =>
  request(`/orders/${id}/confirm`, { method: 'POST' });

export const getOrders = (status) =>
  request(`/orders/${status ? `?status_filter=${status}` : ''}`);

export const getOrder = (id) => request(`/orders/${id}`);

// Chat
export const sendMessage = (data) =>
  request('/chat/message', { method: 'POST', body: JSON.stringify(data) });

export const getGeneralChat = () => request('/chat/general/messages');

export const getChat = (orderId) => request(`/chat/${orderId}`);

// NLP / Voice
export const parseOrderText = (text, store_id = null) =>
  request('/nlp/parse', { method: 'POST', body: JSON.stringify({ text, store_id }) });

// Notifications
export const getNotifications = () => request('/notifications/');
