/**
 * Single place that talks to the Flask backend.
 */

const API = import.meta.env.VITE_API_URL || "";

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function isAuthError(err) {
  if (!err) return false;
  if (err.status === 401) return true;
  const msg = String(err.message || "").toLowerCase();
  return msg.includes("please login") || msg.includes("login first") || msg.includes("unauthorized");
}

function authHeaders() {
  const token =
    localStorage.getItem("export_ai_token") ||
    sessionStorage.getItem("export_ai_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function parseJson(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(data.error || `Request failed (${res.status})`, res.status);
  }
  return data;
}

export function clearAuthStorage() {
  localStorage.removeItem("export_ai_token");
  localStorage.removeItem("export_ai_user");
  sessionStorage.removeItem("export_ai_token");
  sessionStorage.removeItem("export_ai_user");
}

export function getStoredSession() {
  const token =
    localStorage.getItem("export_ai_token") ||
    sessionStorage.getItem("export_ai_token");
  const user =
    localStorage.getItem("export_ai_user") ||
    sessionStorage.getItem("export_ai_user");
  if (!token || !user || token === "mock") return null;
  return { token, user };
}

export async function login(username, password) {
  const res = await fetch(`${API}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return parseJson(res);
}

export async function logout() {
  try {
    await fetch(`${API}/api/logout`, { method: "POST", headers: authHeaders() });
  } catch {
    /* ignore */
  }
  clearAuthStorage();
}

export async function fetchHealth() {
  const res = await fetch(`${API}/api/health`);
  return parseJson(res);
}

export async function fetchSampleNews() {
  const res = await fetch(`${API}/api/sample-news`);
  return parseJson(res);
}

/** News Agent — live headlines (POST avoids browser cache; always fresh) */
export async function fetchLiveNews() {
  const res = await fetch(`${API}/api/fetch-live-news?_=${Date.now()}`, {
    method: "POST",
    headers: {
      ...authHeaders(),
      "Cache-Control": "no-cache",
    },
    cache: "no-store",
    body: JSON.stringify({ refresh: true, t: Date.now() }),
  });
  return parseJson(res);
}

export async function runPipeline(payload) {
  const res = await fetch(`${API}/api/pipeline`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ auto_news: true, ...payload }),
  });
  return parseJson(res);
}

export async function rebuildRag() {
  const res = await fetch(`${API}/api/rag/rebuild`, {
    method: "POST",
    headers: authHeaders(),
  });
  return parseJson(res);
}

export async function askRag(question) {
  const res = await fetch(`${API}/api/rag/ask`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ question }),
  });
  return parseJson(res);
}
