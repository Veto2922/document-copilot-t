import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";
import { Lock, Mail, ArrowRight, UserPlus, LogIn, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Login: React.FC = () => {
  const { user, signIn, signUp } = useAuth();
  const navigate = useNavigate();

  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // If already logged in, redirect straight to dashboard
  if (user) {
    return <Navigate to="/chat" replace />;
  }

  const validateForm = () => {
    if (!email || !password) {
      setError("Please fill in all fields.");
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError("Please enter a valid email address.");
      return false;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return false;
    }
    if (isSignUp && password !== confirmPassword) {
      setError("Passwords do not match.");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setLoading(true);
    try {
      if (isSignUp) {
        const { error: signUpError } = await signUp({ email, password });
        if (signUpError) {
          setError(signUpError.message);
        } else {
          setError("Sign up successful! Please check your email or proceed to sign in.");
          setIsSignUp(false);
        }
      } else {
        const { error: signInError } = await signIn({ email, password });
        if (signInError) {
          setError(signInError.message);
        } else {
          navigate("/chat");
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-4 py-12 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Background radial gradients for dynamic look */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(99,102,241,0.15),transparent_40%)]"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.15),transparent_40%)]"></div>
      <div className="absolute -top-40 -left-40 h-80 w-80 rounded-full bg-indigo-600/10 blur-[100px]"></div>
      <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-purple-600/10 blur-[100px]"></div>

      {/* Main glassmorphic login card */}
      <div className="relative w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl transition-all duration-300 hover:border-white/15 hover:shadow-indigo-500/5">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 text-white shadow-lg shadow-indigo-500/20">
            <Lock className="h-6 w-6" />
          </div>
          <h2 className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
            {isSignUp ? "Create an account" : "Welcome back"}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            {isSignUp
              ? "Sign up to start searching the SEC database"
              : "Enter your credentials to access the research copilot"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div
              className={`flex items-start gap-2.5 rounded-lg border px-4 py-3 text-sm transition-all duration-200 ${
                error.includes("successful")
                  ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-400"
                  : "border-destructive/30 bg-destructive/5 text-destructive-foreground"
              }`}
            >
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-slate-500 transition-colors group-focus-within:text-indigo-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pr-4 pl-10 text-sm text-white placeholder-slate-500 outline-none transition-all duration-200 hover:border-white/15 focus:border-indigo-500 focus:bg-white/10 focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-slate-500 transition-colors group-focus-within:text-indigo-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pr-4 pl-10 text-sm text-white placeholder-slate-500 outline-none transition-all duration-200 hover:border-white/15 focus:border-indigo-500 focus:bg-white/10 focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>
          </div>

          {isSignUp && (
            <div className="space-y-1.5 animate-fadeIn">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pr-4 pl-10 text-sm text-white placeholder-slate-500 outline-none transition-all duration-200 hover:border-white/15 focus:border-indigo-500 focus:bg-white/10 focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            </div>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full justify-center bg-gradient-to-r from-indigo-500 to-purple-500 py-5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/10 transition-all hover:from-indigo-600 hover:to-purple-600 hover:shadow-indigo-500/20 focus:ring-2 focus:ring-indigo-500/50"
          >
            {loading ? (
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            ) : isSignUp ? (
              <>
                <span>Create Account</span>
                <UserPlus className="ml-2 h-4 w-4" />
              </>
            ) : (
              <>
                <span>Sign In</span>
                <LogIn className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </form>

        <div className="mt-6 border-t border-white/10 pt-4 text-center">
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
            }}
            className="inline-flex items-center gap-1.5 text-sm text-indigo-400 transition-colors hover:text-indigo-300"
          >
            {isSignUp ? (
              <>
                <span>Already have an account? Sign In</span>
                <LogIn className="h-4 w-4" />
              </>
            ) : (
              <>
                <span>Don't have an account? Sign Up</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
