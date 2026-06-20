/**
 * Validate that the required environment variables are set and are valid.
 * Throws a runtime error if any of the required variables are missing.
 */
const requiredEnvVars = {
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
  VITE_SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
} as const;

for (const [key, value] of Object.entries(requiredEnvVars)) {
  if (!value) {
    throw new Error(`Missing environment variable: ${key}`);
  }
}

export const env = {
  VITE_API_BASE_URL: requiredEnvVars.VITE_API_BASE_URL,
  VITE_SUPABASE_URL: requiredEnvVars.VITE_SUPABASE_URL,
  VITE_SUPABASE_ANON_KEY: requiredEnvVars.VITE_SUPABASE_ANON_KEY,
} as const;
