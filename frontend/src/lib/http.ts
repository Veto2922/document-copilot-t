import { env } from "./env";
import { getAccessToken } from "./supabase";

/**
 * Custom error class representing failure responses from the backend API,
 * as well as network/CORS issues and timeouts.
 */
export class ApiError extends Error {
  status?: number;
  statusText?: string;
  isNetworkError: boolean;
  body?: unknown;

  constructor({
    message,
    status,
    statusText,
    isNetworkError = false,
    body,
  }: {
    message: string;
    status?: number;
    statusText?: string;
    isNetworkError?: boolean;
    body?: unknown;
  }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.isNetworkError = isNetworkError;
    this.body = body;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

export interface RequestOptions extends RequestInit {
  timeout?: number;
}

/**
 * Custom fetch wrapper that prepends the base URL, sets default headers,
 * injects the Supabase JWT token, handles timeouts, and formats network or HTTP errors.
 */
export async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeout = 30000, headers = {}, ...rest } = options;

  // Build full, clean URL
  const baseUrl = env.VITE_API_BASE_URL.replace(/\/$/, "");
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${baseUrl}${cleanPath}`;

  const reqHeaders = new Headers(headers);

  // Automatically set Authorization header if we have an active Supabase session
  const token = await getAccessToken();
  if (token) {
    reqHeaders.set("Authorization", `Bearer ${token}`);
  }

  // Handle timeout abort logic
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeout);

  try {
    const response = await fetch(url, {
      ...rest,
      headers: reqHeaders,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let body: unknown = null;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          body = await response.json();
        } catch {
          // Ignore json parsing failures
        }
      } else {
        try {
          body = await response.text();
        } catch {
          // Ignore text parsing failures
        }
      }

      const bodyObj = body && typeof body === "object" ? (body as Record<string, unknown>) : null;
      const detail = bodyObj?.detail as string | undefined;
      const bodyMessage = bodyObj?.message as string | undefined;

      throw new ApiError({
        message: detail || bodyMessage || `API request failed with status ${response.status}`,
        status: response.status,
        statusText: response.statusText,
        isNetworkError: false,
        body,
      });
    }

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return (await response.json()) as T;
    }
    return (await response.text()) as unknown as T;
  } catch (error: unknown) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError({
        message: `Request timed out after ${timeout}ms`,
        isNetworkError: true,
      });
    }

    const message = error instanceof Error ? error.message : "Network request failed";
    throw new ApiError({
      message,
      isNetworkError: true,
    });
  }
}
