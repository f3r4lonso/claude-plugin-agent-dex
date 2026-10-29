// Typed client for the local API. The launch token lives in memory (and tab session storage).

let token: string | null = null;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** Reads `#t=...` once, remembers it for this tab, and removes it from the address bar. */
export function initToken(): boolean {
  const match = /[#&]t=([^&]+)/.exec(window.location.hash);
  if (match?.[1]) {
    token = decodeURIComponent(match[1]);
    try {
      sessionStorage.setItem("dex-token", token);
    } catch {
      /* private mode: memory only */
    }
    history.replaceState(null, "", window.location.pathname + "#/dex");
  } else {
    try {
      token = sessionStorage.getItem("dex-token");
    } catch {
      token = null;
    }
  }
  return token !== null;
}

export function getToken(): string | null {
  return token;
}

export async function api<T>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = { Authorization: `Bearer ${token ?? ""}` };
  if (init.body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(path, {
    method: init.method ?? "GET",
    headers,
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const data = (await res.json()) as { detail?: unknown };
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) detail = "Los datos enviados no son válidos.";
    } catch {
      /* keep generic message */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}
