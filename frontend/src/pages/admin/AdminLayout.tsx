import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import NotificationBell from "../../components/NotificationBell";
import { cls } from "../../components/ui";

const NAV = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/vehicles", label: "Vehicles" },
  { to: "/admin/drivers", label: "Drivers" },
  { to: "/admin/allocations", label: "Allocations" },
  { to: "/admin/trip-sheets", label: "Trip sheets" },
  { to: "/admin/fuel", label: "Fuel" },
  { to: "/admin/reports", label: "Reports" },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="bg-slate-900 text-slate-100">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
          <span className="text-lg font-bold">FleetFlow</span>
          <nav className="flex flex-1 flex-wrap gap-1 text-sm">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cls(
                    "rounded-md px-3 py-1.5 hover:bg-slate-700",
                    isActive && "bg-slate-700 font-medium",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <NotificationBell to="/admin/notifications" />
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-slate-300 sm:inline">{user?.full_name}</span>
            <button onClick={logout} className="rounded-md px-2 py-1 hover:bg-slate-700">
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl space-y-4 px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
