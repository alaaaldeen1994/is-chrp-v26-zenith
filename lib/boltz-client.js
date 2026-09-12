'use strict';

const DEFAULT_BASE = 'https://api.boltz.bio';
const API_PREFIX = '/compute/v1';
const REQUEST_TIMEOUT_MS = 30_000;
const DOWNLOAD_TIMEOUT_MS = 60_000;

function getApiKey() {
  const key = String(process.env.BOLTZ_API_KEY || '').trim();
  if (!key) {
    const err = new Error('BOLTZ_API_KEY is not configured on the server.');
    err.statusCode = 503;
    throw err;
  }
  return key;
}

function keyMode(key = getApiKey()) {
  if (key.includes('_test_')) return 'test';
  if (key.includes('_live_')) return 'live';
  return 'unknown';
}

function baseUrl() {
  return String(process.env.BOLTZ_API_BASE || DEFAULT_BASE).replace(/\/$/, '');
}

function safeJsonParse(text) {
  if (!text) return null;
  try { return JSON.parse(text); } catch { return null; }
}

async function boltzRequest(path, { method = 'GET', body, timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  const key = getApiKey();
  const headers = {
    'accept': 'application/json',
    'x-api-key': key,
  };
  let payload;
  if (body !== undefined) {
    headers['content-type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(baseUrl() + path, {
      method,
      headers,
      body: payload,
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (cause) {
    const err = new Error(`Unable to reach Boltz API: ${cause?.message || cause}`);
    err.statusCode = 502;
    throw err;
  }

  const text = await response.text();
  const parsed = safeJsonParse(text);
  if (!response.ok) {
    const message = parsed?.error?.message || parsed?.message || parsed?.detail || text || `Boltz API error ${response.status}`;
    const err = new Error(String(message).slice(0, 2000));
    err.statusCode = response.status >= 400 && response.status < 500 ? response.status : 502;
    err.upstreamStatus = response.status;
    err.details = parsed?.error?.details || parsed?.details || undefined;
    throw err;
  }
  return parsed ?? {};
}

async function authenticate() {
  return boltzRequest(`${API_PREFIX}/auth/me`);
}

async function estimatePrediction(request) {
  return boltzRequest(`${API_PREFIX}/predictions/structure-and-binding/estimate-cost`, {
    method: 'POST',
    body: request,
  });
}

async function startPrediction(request) {
  return boltzRequest(`${API_PREFIX}/predictions/structure-and-binding`, {
    method: 'POST',
    body: request,
  });
}

async function getPrediction(id) {
  if (!/^[A-Za-z0-9_-]{6,160}$/.test(String(id || ''))) {
    const err = new Error('Invalid prediction ID.');
    err.statusCode = 400;
    throw err;
  }
  return boltzRequest(`${API_PREFIX}/predictions/structure-and-binding/${encodeURIComponent(id)}`);
}

async function downloadArtifact(url, { maxBytes = 100 * 1024 * 1024, timeoutMs = DOWNLOAD_TIMEOUT_MS } = {}) {
  let parsed;
  try { parsed = new URL(url); } catch {
    const err = new Error('Boltz returned an invalid artifact URL.');
    err.statusCode = 502;
    throw err;
  }
  if (parsed.protocol !== 'https:') {
    const err = new Error('Boltz artifact URL must use HTTPS.');
    err.statusCode = 502;
    throw err;
  }

  let response;
  try {
    response = await fetch(parsed.toString(), { signal: AbortSignal.timeout(timeoutMs) });
  } catch (cause) {
    const err = new Error(`Unable to download Boltz artifact: ${cause?.message || cause}`);
    err.statusCode = 502;
    throw err;
  }
  if (!response.ok) {
    const err = new Error(`Boltz artifact download failed (${response.status}).`);
    err.statusCode = 502;
    throw err;
  }

  const length = Number(response.headers.get('content-length'));
  if (Number.isFinite(length) && length > maxBytes) {
    const err = new Error(`Boltz artifact exceeds the ${Math.round(maxBytes / 1024 / 1024)} MB safety limit.`);
    err.statusCode = 413;
    throw err;
  }

  const buffer = Buffer.from(await response.arrayBuffer());
  if (buffer.length > maxBytes) {
    const err = new Error(`Boltz artifact exceeds the ${Math.round(maxBytes / 1024 / 1024)} MB safety limit.`);
    err.statusCode = 413;
    throw err;
  }
  return { buffer, contentType: response.headers.get('content-type') || '' };
}

module.exports = {
  API_PREFIX,
  authenticate,
  downloadArtifact,
  estimatePrediction,
  getApiKey,
  getPrediction,
  keyMode,
  startPrediction,
};
