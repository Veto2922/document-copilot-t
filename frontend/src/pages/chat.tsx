import React, { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { LogOut, ShieldCheck, Server, User, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Chat: React.FC = () => {
  const { user, signOut } = useAuth();
  const [authResponse, setAuthResponse] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTestAuth = async () => {
    setLoading(true);
    setError(null);
    setAuthResponse(null);

    try {
      // Calls the /api/test-auth endpoint with the automatically injected JWT token
      const res = await api.get<unknown>("/api/test-auth");
      setAuthResponse(res);
    } catch (err: unknown) {
      console.error("Test auth request failed:", err);
      const message = err instanceof Error ? err.message : "Failed to call backend authenticated endpoint.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-slate-950 px-4 font-sans text-white">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(99,102,241,0.12),transparent_50%)]"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,rgba(168,85,247,0.08),transparent_50%)]"></div>

      <div className="relative w-full max-w-2xl rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl transition-all duration-300">
        {/* Header */}
        <div className="mb-6 flex flex-col items-center justify-between border-b border-white/10 pb-6 md:flex-row">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400">
              <User className="h-5 w-5" />
            </div>
            <div className="text-center md:text-left">
              <h1 className="bg-gradient-to-r from-white to-slate-400 bg-clip-text text-xl font-bold tracking-tight text-transparent">
                Research Dashboard
              </h1>
              <p className="text-xs text-slate-400">Authenticated user workspace</p>
            </div>
          </div>

          <Button
            onClick={() => signOut()}
            variant="ghost"
            className="mt-4 gap-2 text-slate-400 hover:bg-white/5 hover:text-white md:mt-0"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </Button>
        </div>

        {/* User Card */}
        <div className="mb-6 rounded-xl border border-white/5 bg-white/[0.02] p-5">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Active Supabase Profile
          </h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">Email:</span>
              <span className="font-mono text-indigo-300">{user?.email}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">User ID (UUID):</span>
              <span className="font-mono text-indigo-300">{user?.id}</span>
            </div>
          </div>
        </div>

        {/* Backend Verification Section */}
        <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-slate-200">Verify Token Gateway</h3>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Clicking the button will transmit the Supabase JWT token to the FastAPI backend at{" "}
                <code className="text-indigo-300 font-mono">/api/test-auth</code>. The backend verifies the signature via Supabase API before returning user context.
              </p>

              <div className="mt-5 flex flex-wrap gap-3">
                <Button
                  onClick={handleTestAuth}
                  disabled={loading}
                  className="bg-indigo-600 font-semibold text-white shadow-lg shadow-indigo-600/10 hover:bg-indigo-500"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      <span>Verifying...</span>
                    </>
                  ) : (
                    <>
                      <Server className="mr-2 h-4 w-4" />
                      <span>Test Backend Auth</span>
                    </>
                  )}
                </Button>
              </div>

              {/* Status Output */}
              {(authResponse !== null || error !== null) && (
                <div className="mt-5 animate-fadeIn space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Verification Output
                  </h4>

                  {error && (
                    <div className="flex items-start gap-2.5 rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive-foreground">
                      <AlertCircle className="h-5 w-5 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  {authResponse !== null && (
                    <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4 font-mono text-xs text-slate-300">
                      <div className="flex items-center gap-2 mb-2 text-emerald-400 font-semibold">
                        <ShieldCheck className="h-4 w-4" />
                        <span>Success: Backend Authenticated</span>
                      </div>
                      <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-slate-950/80 p-3">
                        {JSON.stringify(authResponse, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
