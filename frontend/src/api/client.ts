const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
export function token() { return localStorage.getItem("bb_token"); }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token()) headers.set("Authorization", `Bearer ${token()}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}
export async function login(username: string, password: string) {
  return api<any>("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
}
export async function demoLogin(role: string) {
  return api<any>(`/auth/demo-login/${role}`, { method: "POST" });
}
