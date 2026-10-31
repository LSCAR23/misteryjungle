export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export const TOKEN_KEY = "mj_token";
export const USER_KEY = "mj_user";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function clearSession() {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
  } catch {
    /* ignore */
  }
}

function parseDetail(data: unknown, status: number): string {
  const d = (data as { detail?: unknown } | null)?.detail;
  if (typeof d === "string" && d) return d;
  if (Array.isArray(d)) {
    const msgs = d
      .map((e) =>
        e && typeof e === "object" && "msg" in e
          ? String((e as { msg: unknown }).msg)
          : "",
      )
      .filter(Boolean);
    if (msgs.length) return msgs.join(". ");
  }
  if (status === 401) return "Sesión expirada. Inicia sesión de nuevo.";
  if (status === 403) return "No tienes permiso para esta acción";
  if (status === 404) return "No encontrado";
  if (status >= 500) return "Error del servidor. Intenta de nuevo.";
  return "Ocurrió un error inesperado";
}

export async function apiFetch<T>(
  path: string,
  opts: { method?: string; body?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      method: opts.method ?? (opts.body !== undefined ? "POST" : "GET"),
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      signal: opts.signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new ApiError(0, "No se pudo conectar con el servidor");
  }

  if (res.status === 401 && path !== "/auth/login" && typeof window !== "undefined") {
    clearSession();
    if (window.location.pathname !== "/login") {
      // Recarga completa intencional: limpia el estado en memoria (SWR, etc.).
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/login");
    }
  }

  if (res.status === 204) return undefined as T;

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) throw new ApiError(res.status, parseDetail(data, res.status));
  return data as T;
}

export const swrFetcher = <T = unknown>(path: string): Promise<T> =>
  apiFetch<T>(path);
