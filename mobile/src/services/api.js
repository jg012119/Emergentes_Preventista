// mobile/src/services/api.js
// Wrapper around the FastAPI backend for chat and order operations.

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

let authToken = null;

export function setToken(token) {
  authToken = token || null;
}

async function request(endpoint, { method = "GET", body = null, token = null } = {}) {
  const headers = {
    "Content-Type": "application/json",
  };
  const bearer = token || authToken;
  if (bearer) {
    headers.Authorization = `Bearer ${bearer}`;
  }

  const resp = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers,
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  if (resp.status === 204) return null;

  const text = await resp.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (_) {
    data = text ? { detail: text } : null;
  }
  if (!resp.ok) {
    throw new Error(data?.detail || `Request ${method} ${endpoint} failed ${resp.status}`);
  }
  return data;
}

// Auth
export async function login(email, password) {
  return request("/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export async function register(nameOrPayload, email, phone, password) {
  const payload = typeof nameOrPayload === "object"
    ? nameOrPayload
    : { name: nameOrPayload, email, phone, password };
  return request("/auth/register", {
    method: "POST",
    body: payload,
  });
}

// Users
export async function getMe(token) {
  return request("/users/me", { token });
}

export async function updateMe(data, token) {
  return request("/users/me", {
    method: "PUT",
    body: data,
    token,
  });
}

// Stores
export async function getStores(token) {
  return request("/stores/", { token });
}

export async function createStore(data, token) {
  return request("/stores/", {
    method: "POST",
    body: data,
    token,
  });
}

export async function updateStore(id, data, token) {
  return request(`/stores/${id}`, {
    method: "PUT",
    body: data,
    token,
  });
}

export async function deleteStore(id, token) {
  return request(`/stores/${id}`, {
    method: "DELETE",
    token,
  });
}

// Products
export async function getProducts(token) {
  return request("/products/", { token });
}

// Orders
export async function createDraft(data, token) {
  return request("/orders/draft", {
    method: "POST",
    body: data,
    token,
  });
}

export async function updateDraft(id, data, token) {
  return request(`/orders/${id}/draft`, {
    method: "PUT",
    body: data,
    token,
  });
}

export async function getOrders(statusFilter = null, token) {
  const query = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : "";
  return request(`/orders/${query}`, { token });
}

export async function getOrder(id, token) {
  return request(`/orders/${id}`, { token });
}

export async function confirmOrder(orderId, token) {
  return request(`/orders/${orderId}/confirm`, {
    method: "POST",
    token,
  });
}

// Chat
export async function getGeneralChat(token) {
  return request("/chat/general/messages", { token });
}

export async function getChat(orderId, token) {
  return request(`/chat/${orderId}`, { token });
}

export async function sendMessage({ order_id = null, message, sender = "user", context = null }, token) {
  return request("/chat/message", {
    method: "POST",
    body: { order_id, message, sender, context },
    token,
  });
}

export async function rateChatMessage(messageId, { rating, comment = null, context = null } = {}, token) {
  return request(`/chat/messages/${messageId}/feedback`, {
    method: "POST",
    body: { rating, comment, context },
    token,
  });
}

// NLP
export async function parseOrderText(text, token) {
  return request("/nlp/parse", {
    method: "POST",
    body: { text },
    token,
  });
}
