// mobile/src/services/api.js
// Wrapper around the FastAPI backend for chat, auth, stores, products, and order operations.

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://10.253.2.79:8000";

let _token = null;

export const setToken = (t) => { _token = t; };
export const getToken = () => _token;

/** Helper to perform a fetch request with JSON handling */
async function request(endpoint, { method = "GET", body = null, headers = {} } = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const allHeaders = {
    "Content-Type": "application/json",
    ...(_token ? { "Authorization": `Bearer ${_token}` } : {}),
    ...headers,
  };
  const options = {
    method,
    headers: allHeaders,
    ...(body ? { body: JSON.stringify(body) } : {}),
  };
  const resp = await fetch(url, options);
  if (resp.status === 204) return null;
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.detail || `Request ${method} ${endpoint} failed ${resp.status}`);
  }
  return data;
}

// --- Auth ---
export const register = (name, email, phone, password) =>
  request('/auth/register', { method: 'POST', body: { name, email, phone, password } });

export const login = (email, password) =>
  request('/auth/login', { method: 'POST', body: { email, password } });

export const getMe = () => request('/users/me');

export const updateMe = (data) =>
  request('/users/me', { method: 'PUT', body: data });

// --- Stores ---
export const createStore = (data) =>
  request('/stores/', { method: 'POST', body: data });

export const getStores = () => request('/stores/');

export const updateStore = (id, data) =>
  request(`/stores/${id}`, { method: 'PUT', body: data });

export const deleteStore = (id) =>
  request(`/stores/${id}`, { method: 'DELETE' });

// --- Products ---
export const getProducts = () => request('/products/');

// --- Orders ---
export const createDraft = (data) =>
  request('/orders/draft', { method: 'POST', body: data });

export const confirmOrder = (id) =>
  request(`/orders/${id}/confirm`, { method: 'POST' });

export const getOrders = (status) =>
  request(`/orders${status ? `?status_filter=${status}` : ''}`);

export const getOrder = (id) => request(`/orders/${id}`);

// --- Chat ---
export const sendMessage = (data) =>
  request('/chat/message', { method: 'POST', body: data });

export const getGeneralChat = () => request('/chat/general/messages');

export const getChat = (orderId) => request(`/chat/${orderId}`);

// --- NLP / Voice ---
export const parseOrderText = (text, store_id = null) =>
  request('/nlp/parse', { method: 'POST', body: { text, store_id } });

// --- Notifications ---
export const getNotifications = () => request('/notifications/');
