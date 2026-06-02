// mobile/src/services/api.js
// Wrapper around the FastAPI backend for chat and order operations.
// Adjust BASE_URL to point to your deployed server (or local dev server).

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

/** Helper to perform a fetch request with JSON handling */
async function request(endpoint, { method = "GET", body = null, token = null } = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const options = {
    method,
    headers,
    ...(body ? { body: JSON.stringify(body) } : {}),
  };
  const resp = await fetch(url, options);
  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Request ${method} ${endpoint} failed ${resp.status}: ${errText}`);
  }
  return resp.json();
}

/** Get general chat messages (no order context) */
export async function getGeneralChat(token) {
  return request("/chat/general/messages", { token });
}

/** Get chat messages for a specific order */
export async function getChat(orderId, token) {
  return request(`/chat/${orderId}`, { token });
}

/** Send a chat message */
export async function sendMessage({ order_id = null, message, sender = "user" }, token) {
  return request("/chat/message", {
    method: "POST",
    body: { order_id, message, sender },
    token,
  });
}

/** Parse order text (used for voice interpretation) */
export async function parseOrderText(text, token) {
  // The backend parses order text via the same chat endpoint; we can send a dummy message.
  return request("/chat/message", {
    method: "POST",
    body: { order_id: null, message: `@@parse ${text}`.trim(), sender: "user" },
    token,
  });
}

/** Confirm an order (change status to 'pendiente') */
export async function confirmOrder(orderId, token) {
  // Placeholder – implement proper endpoint in backend if needed.
  return request(`/orders/${orderId}/confirm`, { method: "POST", token });
}
