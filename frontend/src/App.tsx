import { Navigate, Route, Routes } from "react-router-dom";
import RequireRole from "./auth/RequireRole";
import { useAuth } from "./auth/AuthContext";
import LoginPage from "./pages/LoginPage";
import AdminLayout from "./pages/admin/AdminLayout";
import DashboardPage from "./pages/admin/DashboardPage";
import VehiclesPage from "./pages/admin/VehiclesPage";
import VehicleDetailPage from "./pages/admin/VehicleDetailPage";
import DriversPage from "./pages/admin/DriversPage";
import AllocationsPage from "./pages/admin/AllocationsPage";
import TripSheetsPage from "./pages/admin/TripSheetsPage";
import FuelImportsPage from "./pages/admin/FuelImportsPage";
import ReportsPage from "./pages/admin/ReportsPage";
import NotificationsPage from "./pages/admin/NotificationsPage";
import DriverLayout from "./pages/driver/DriverLayout";
import DriverHomePage from "./pages/driver/DriverHomePage";
import DriverTripsPage from "./pages/driver/DriverTripsPage";
import DriverHandoverPage from "./pages/driver/DriverHandoverPage";

function HomeRedirect() {
  const { user, initializing } = useAuth();
  if (initializing) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "driver" ? "/driver" : "/admin"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Desktop dashboard for staff */}
      <Route element={<RequireRole roles={["admin", "fleet_manager"]} />}>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="vehicles" element={<VehiclesPage />} />
          <Route path="vehicles/:id" element={<VehicleDetailPage />} />
          <Route path="drivers" element={<DriversPage />} />
          <Route path="allocations" element={<AllocationsPage />} />
          <Route path="trip-sheets" element={<TripSheetsPage />} />
          <Route path="fuel" element={<FuelImportsPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>
      </Route>

      {/* Mobile-first driver UI (installable PWA) */}
      <Route element={<RequireRole roles={["driver"]} />}>
        <Route path="/driver" element={<DriverLayout />}>
          <Route index element={<DriverHomePage />} />
          <Route path="trips" element={<DriverTripsPage />} />
          <Route path="handover" element={<DriverHandoverPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
