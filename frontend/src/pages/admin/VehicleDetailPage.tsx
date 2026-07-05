import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { VehiclesApi } from "../../api/resources";
import { Badge, ErrorText, Loading, cls } from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { fmtKm } from "../../lib/fmt";
import DocumentsTab from "./vehicle-tabs/DocumentsTab";
import ServiceTab from "./vehicle-tabs/ServiceTab";
import MaintenanceTab from "./vehicle-tabs/MaintenanceTab";
import FuelTab from "./vehicle-tabs/FuelTab";

const TABS = ["Documents", "Service history", "Maintenance rules", "Fuel"] as const;
type Tab = (typeof TABS)[number];

export default function VehicleDetailPage() {
  const { id } = useParams();
  const vehicleId = Number(id);
  const { data: vehicle, loading, error } = useLoad(() => VehiclesApi.get(vehicleId), [vehicleId]);
  const [tab, setTab] = useState<Tab>("Documents");

  if (loading) return <Loading />;
  if (error) return <ErrorText message={error} />;
  if (!vehicle) return null;

  return (
    <>
      <div>
        <Link to="/admin/vehicles" className="text-sm text-sky-700 hover:underline">
          ← Vehicles
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-bold">{vehicle.plate}</h1>
          <span className="text-slate-600">
            {vehicle.make} {vehicle.model} ({vehicle.year})
          </span>
          <Badge value={vehicle.status} />
          <span className="text-sm text-slate-500">
            {fmtKm(vehicle.current_km)} · {vehicle.fuel_type} · tank {vehicle.tank_capacity_l} L
          </span>
        </div>
      </div>

      <div className="border-b border-slate-200">
        <nav className="-mb-px flex gap-4 text-sm">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cls(
                "border-b-2 px-1 py-2",
                tab === t
                  ? "border-sky-600 font-medium text-sky-700"
                  : "border-transparent text-slate-500 hover:text-slate-700",
              )}
            >
              {t}
            </button>
          ))}
        </nav>
      </div>

      {tab === "Documents" && <DocumentsTab vehicleId={vehicleId} />}
      {tab === "Service history" && <ServiceTab vehicleId={vehicleId} />}
      {tab === "Maintenance rules" && <MaintenanceTab vehicleId={vehicleId} />}
      {tab === "Fuel" && <FuelTab vehicleId={vehicleId} />}
    </>
  );
}
