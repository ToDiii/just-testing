const API_KEY = import.meta.env.VITE_API_KEY || "dev";

export async function api(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers || {});
  headers.set("X-API-Key", API_KEY);
  const res = await fetch(path, { ...init, headers });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}
