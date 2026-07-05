import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { Role } from "../api/types";
import { useAuth } from "./AuthContext";

/** Route guard: renders child routes only for the given roles. */
export default function RequireRole({ roles }: { roles: Role[] }) {
  const { user, initializing } = useAuth();
  const location = useLocation();

  if (initializing) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (!roles.includes(user.role)) {
    // Logged in but wrong area (e.g. a driver typing /admin): send them home.
    return <Navigate to={user.role === "driver" ? "/driver" : "/admin"} replace />;
  }
  return <Outlet />;
}
