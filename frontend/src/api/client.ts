// Thin fetch wrapper around the FastAPI backend. All calls go to the relative
// /api prefix: the Vite dev server proxies it to the backend, so the same code
// works from this PC and from a phone on the LAN.

const BASE = "/api";
const TOKEN_KEY = "fleetflow_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** FastAPI errors carry a `detail`: a string, or a list of validation errors. */
function detailToMessage(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        const loc = Array.isArray(e.loc) ? e.loc.slice(1).join(".") : "";
        return loc ? `${loc}: ${e.msg}` : String(e.msg ?? "");
      })
      .join("; ");
  }
  return fallback;
}

async function toApiError(res: Response): Promise<ApiError> {
  let message = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    message = detailToMessage(body.detail, message);
  } catch {
    // non-JSON error body — keep the fallback message
  }
  return new ApiError(res.status, message);
}

interface RequestOptions {
  method?: string;
  /** JSON-serialized request body. */
  body?: unknown;
  /** Form-encoded body (used by the OAuth2 login) or file upload. */
  form?: URLSearchParams | FormData;
  query?: Record<string, string | number | boolean | undefined | null>;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null) params.set(key, String(value));
  }
  const qs = params.toString();
  return `${BASE}${path}${qs ? `?${qs}` : ""}`;
}

async function rawRequest(path: string, opts: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let body: BodyInit | undefined;
  if (opts.form !== undefined) {
    body = opts.form; // fetch sets the correct Content-Type itself
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }

  const res = await fetch(buildUrl(path, opts.query), {
    method: opts.method ?? "GET",
    headers,
    body,
  });

  if (res.status === 401 && token) {
    // Token expired or revoked: drop it and send the user back to login.
    clearToken();
    window.location.assign("/login");
  }
  if (!res.ok) throw await toApiError(res);
  return res;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const res = await rawRequest(path, opts);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Fetch a file (report export) and trigger a browser download. */
export async function download(
  path: string,
  query: RequestOptions["query"],
  filename: string,
): Promise<void> {
  const res = await rawRequest(path, { query });
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
