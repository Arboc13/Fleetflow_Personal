import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { cls } from "../../components/ui";

// Mobile-first shell: content area + fixed bottom tab bar with large touch
// targets, sized for one-hand phone use. Installable as a PWA.
const TABS = [
  { to: "/driver", label: "Home", icon: "🏠", end: true },
  { to: "/driver/trips", label: "Trips", icon: "🛣️" },
  { to: "/driver/handover", label: "Handover", icon: "🔑" },
];

export default function DriverLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col">
      <header className="flex items-center justify-between bg-slate-900 px-4 py-3 text-white">
        <span className="font-bold">FleetFlow</span>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-slate-300">{user?.full_name}</span>
          <button onClick={logout} className="rounded-md px-2 py-1 hover:bg-slate-700">
            Log out
          </button>
        </div>
      </header>

      <main className="flex-1 space-y-4 p-4 pb-24">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 mx-auto flex max-w-md border-t border-slate-200 bg-white">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              cls(
                "flex flex-1 flex-col items-center gap-0.5 py-3 text-xs",
                isActive ? "font-semibold text-sky-700" : "text-slate-500",
              )
            }
          >
            <span className="text-xl" aria-hidden>
              {tab.icon}
            </span>
            {tab.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
