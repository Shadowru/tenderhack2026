const BASE = '/api';

// Generate a stable session ID once per browser tab lifetime.
// crypto.randomUUID() is available in all modern browsers; fall back to
// a timestamp+random string for environments that don't support it.
export const SESSION_ID =
  (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function')
    ? crypto.randomUUID()
    : Date.now().toString(36) + Math.random().toString(36).slice(2);

export async function searchProducts(query, { userId = 'anonymous', size = 20, offset = 0, category = null, sessionId = SESSION_ID } = {}) {
  const params = new URLSearchParams({ q: query, user_id: userId, size, offset, session_id: sessionId });
  if (category) params.set('category', category);
  const res = await fetch(`${BASE}/search?${params}`);
  return res.json();
}

export async function searchBaseline(query, params) {
  return searchProducts(query, { ...params, userId: 'anonymous' });
}

export async function getSuggestions(query, userId = 'anonymous') {
  const params = new URLSearchParams({ q: query, user_id: userId });
  const res = await fetch(`${BASE}/search/suggest?${params}`);
  return res.json();
}

export async function trackEvent({ userId, eventType, productId = '', category = '', query = '', position = null, sessionId = SESSION_ID }) {
  const params = new URLSearchParams({ user_id: userId, event_type: eventType, session_id: sessionId });
  if (productId) params.set('product_id', productId);
  if (category) params.set('category', category);
  if (query) params.set('query', query);
  if (position !== null) params.set('position', String(position));
  return fetch(`${BASE}/search/event?${params}`, { method: 'POST' });
}

export async function expandSearch(query, { userId = 'anonymous', size = 10 } = {}) {
  const params = new URLSearchParams({ q: query, user_id: userId, size });
  const res = await fetch(`${BASE}/search/expand?${params}`);
  return res.json();
}

export async function getProduct(productId, userId = 'anonymous', sessionId = SESSION_ID) {
  const params = new URLSearchParams({ user_id: userId, session_id: sessionId });
  const res = await fetch(`${BASE}/search/product/${productId}?${params}`);
  return res.json();
}

export async function getCart(userId) {
  const res = await fetch(`${BASE}/cart?user_id=${userId}`);
  return res.json();
}

export async function addToCart(userId, productId, productName = '', category = '') {
  const params = new URLSearchParams({ user_id: userId, product_id: productId, product_name: productName, category });
  return fetch(`${BASE}/cart/add?${params}`, { method: 'POST' }).then(r => r.json());
}

export async function removeFromCart(userId, productId) {
  const params = new URLSearchParams({ user_id: userId, product_id: productId });
  return fetch(`${BASE}/cart/remove?${params}`, { method: 'POST' }).then(r => r.json());
}

export async function clearCart(userId) {
  return fetch(`${BASE}/cart/clear?user_id=${userId}`, { method: 'POST' }).then(r => r.json());
}

export async function getFavorites(userId) {
  const res = await fetch(`${BASE}/cart/favorites?user_id=${userId}`);
  return res.json();
}

export async function addFavorite(userId, productId, productName = '', category = '') {
  const params = new URLSearchParams({ user_id: userId, product_id: productId, product_name: productName, category });
  return fetch(`${BASE}/cart/favorites/add?${params}`, { method: 'POST' }).then(r => r.json());
}

export async function removeFavorite(userId, productId) {
  const params = new URLSearchParams({ user_id: userId, product_id: productId });
  return fetch(`${BASE}/cart/favorites/remove?${params}`, { method: 'POST' }).then(r => r.json());
}

export async function clearFavorites(userId) {
  return fetch(`${BASE}/cart/favorites/clear?user_id=${userId}`, { method: 'POST' }).then(r => r.json());
}

export async function getLiveMetrics(hours = 24) {
  const res = await fetch(`${BASE}/metrics/live?hours=${hours}`);
  return res.json();
}

export async function getMetricHistory(metricName, days = 7) {
  const res = await fetch(`${BASE}/metrics/history/${metricName}?days=${days}`);
  return res.json();
}

export async function getUserStats(userId) {
  const res = await fetch(`${BASE}/metrics/user/${userId}`);
  return res.json();
}
