import { request, type RequestOptions } from "./http";

export interface ChatThread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface ChatMessage {
  id: string;
  thread_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

/**
 * Shared API singleton.
 * All backend API interactions must go through this object.
 */
export const api = {
  /**
   * Perform a GET request.
   */
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),

  /**
   * Perform a POST request. Automatically serializes body to JSON if it's a plain object.
   */
  post: <T>(path: string, body?: unknown, options?: RequestOptions) => {
    const headers = new Headers(options?.headers);
    let requestBody: BodyInit | null | undefined = undefined;

    if (body !== undefined) {
      if (body instanceof FormData) {
        requestBody = body;
      } else {
        if (!headers.has("Content-Type")) {
          headers.set("Content-Type", "application/json");
        }
        requestBody = JSON.stringify(body);
      }
    }

    return request<T>(path, {
      ...options,
      method: "POST",
      headers,
      body: requestBody,
    });
  },

  /**
   * Perform a PUT request. Automatically serializes body to JSON if it's a plain object.
   */
  put: <T>(path: string, body?: unknown, options?: RequestOptions) => {
    const headers = new Headers(options?.headers);
    let requestBody: BodyInit | null | undefined = undefined;

    if (body !== undefined) {
      if (body instanceof FormData) {
        requestBody = body;
      } else {
        if (!headers.has("Content-Type")) {
          headers.set("Content-Type", "application/json");
        }
        requestBody = JSON.stringify(body);
      }
    }

    return request<T>(path, {
      ...options,
      method: "PUT",
      headers,
      body: requestBody,
    });
  },

  /**
   * Perform a PATCH request. Automatically serializes body to JSON if it's a plain object.
   */
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) => {
    const headers = new Headers(options?.headers);
    let requestBody: BodyInit | null | undefined = undefined;

    if (body !== undefined) {
      if (body instanceof FormData) {
        requestBody = body;
      } else {
        if (!headers.has("Content-Type")) {
          headers.set("Content-Type", "application/json");
        }
        requestBody = JSON.stringify(body);
      }
    }

    return request<T>(path, {
      ...options,
      method: "PATCH",
      headers,
      body: requestBody,
    });
  },

  /**
   * Perform a DELETE request.
   */
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),

  // --- Product Level Calls ---

  /**
   * Load all chat threads for the current authenticated user.
   */
  async getThreads(): Promise<ChatThread[]> {
    return this.get<ChatThread[]>("/chat/threads");
  },

  /**
   * Create a new chat thread.
   */
  async createThread(title?: string): Promise<ChatThread> {
    return this.post<ChatThread>("/chat/threads", { title });
  },

  /**
   * Fetch the message history for a specific chat thread.
   */
  async getMessages(threadId: string): Promise<ChatMessage[]> {
    return this.get<ChatMessage[]>(`/chat/threads/${threadId}/messages`);
  },
};
