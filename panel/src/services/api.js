const API_URL = import.meta.env.VITE_API_URL || 'http://192.168.125.130:8000';

function getHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Error del servidor');
  return data;
}

// Auth
export const login = (email, password) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });

// Orders
export const getOrders = (status) =>
  request(`/orders/all${status ? `?status_filter=${status}` : ''}`);
export const getOrder = (id) => request(`/orders/${id}`);
export const updateOrderStatus = (id, status) =>
  request(`/orders/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) });

// Products
export const getProducts = () => request('/products/all');
export const createProduct = (data) =>
  request('/products/', { method: 'POST', body: JSON.stringify(data) });
export const updateProduct = (id, data) =>
  request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteProduct = (id) =>
  request(`/products/${id}`, { method: 'DELETE' });

// Users / Clients
export const getUsers = () => request('/users/me'); // Admin would need a list endpoint

export default {
  login, getOrders, getOrder, updateOrderStatus,
  getProducts, createProduct, updateProduct, deleteProduct,
};
