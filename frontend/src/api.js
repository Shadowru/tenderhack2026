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
