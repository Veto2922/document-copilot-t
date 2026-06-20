import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

/**
 * Route guard component that redirects unauthenticated users to the login screen.
 * Displays a loading placeholder while the Supabase session is being checked.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background text-foreground font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <p className="text-sm text-muted-foreground animate-pulse">Verifying authentication session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    // Redirect unauthenticated user to login, preserving the route they tried to access
    return <Navigate to="/login" replace />;
  }

  return children ? <>{children}</> : null;
};
