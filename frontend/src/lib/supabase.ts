import { createClient } from "@supabase/supabase-js";
import { env } from "./env";

/**
 * Shared browser-side Supabase client.
 * Uses client-safe environment variables.
 */
export const supabase = createClient(env.VITE_SUPABASE_URL, env.VITE_SUPABASE_ANON_KEY);

/**
 * Retrieve the active user's access token (JWT) from the current Supabase session.
 * Returns null if the user is not authenticated.
 */
export async function getAccessToken(): Promise<string | null> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  } catch (error) {
    console.error("Failed to retrieve Supabase session access token:", error);
    return null;
  }
}
