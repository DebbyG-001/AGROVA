// One place that knows where the backend is. See docs/API_CONTRACT.md for what it must return.

const RAW = process.env.NEXT_PUBLIC_API_URL ?? "";

/** Backend address without a trailing slash. Empty string means "no backend configured". */
export const API_URL = RAW.replace(/\/+$/, "");

/** True when NEXT_PUBLIC_API_URL is set. When false the app runs on built-in demo data. */
export const backendConfigured = API_URL !== "";

export class ApiError extends Error {
  status: number | null;
  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Call the backend and return parsed JSON.
 * Throws ApiError with a message that is safe to show the farmer.
 */
export async function api<T>(path: string, init: RequestInit = {}, timeoutMs = 45_000): Promise<T> {
  if (!backendConfigured) throw new ApiError("No backend is configured.");

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    // Don't set Content-Type for FormData: the browser adds the multipart boundary itself.
    const isForm = typeof FormData !== "undefined" && init.body instanceof FormData;
    const res = await fetch(`${API_URL}${path}`, {
      ...init,
      signal: ctrl.signal,
      headers: { Accept: "application/json", ...(init.body && !isForm ? { "Content-Type": "application/json" } : {}), ...init.headers },
    });

    if (!res.ok) {
      let detail = "";
      try {
        const body = await res.json();
        if (typeof body?.detail === "string") detail = body.detail;
      } catch {
        // body was not JSON; fall through to the generic message
      }
      if (res.status === 404) throw new ApiError("This feature isn't available on the server yet.", 404);
      throw new ApiError(detail || "The server had a problem. Please try again.", res.status);
    }
    return (await res.json()) as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e instanceof DOMException && e.name === "AbortError")
      throw new ApiError("The server took too long to answer. Please try again.");
    throw new ApiError("Can't reach the server. Check your connection and try again.");
  } finally {
    clearTimeout(timer);
  }
}
