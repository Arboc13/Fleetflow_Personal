import { Link } from "react-router-dom";
import { AllocationsApi, NotificationsApi, TripSheetsApi, VehiclesApi } from "../../api/resources";
import { Badge, Card, Empty, Loading } from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { fmtDateTime } from "../../lib/fmt";

// The backend filters every list to the logged-in driver's own records,
// so these calls need no driver_id.
export default function DriverHomePage() {
  const allocations = useLoad(() => AllocationsApi.list());
  const trips = useLoad(() => TripSheetsApi.list({ status_filter: "draft" }));
  const alerts = useLoad(() => NotificationsApi.list(true));
  const vehicles = useLoad(() => VehiclesApi.list());

  const active = (allocations.data ?? []).filter((a) => a.status === "active");
  const openTrip = (trips.data ?? [])[0];
  const vehicleById = new Map((vehicles.data ?? []).map((v) => [v.id, v]));

  return (
    <>
      <Card title="My vehicle">
        {allocations.loading ? (
          <Loading />
        ) : active.length === 0 ? (
          <Empty>No vehicle allocated to you right now.</Empty>
        ) : (
          <ul className="space-y-2">
            {active.map((a) => {
              const v = vehicleById.get(a.vehicle_id);
              return (
                <li key={a.id} className="rounded-lg bg-slate-50 p-3">
                  <p className="text-lg font-bold">{v?.plate ?? `Vehicle #${a.vehicle_id}`}</p>
                  {v && (
                    <p className="text-sm text-slate-600">
                      {v.make} {v.model} · {v.current_km.toLocaleString("ro-RO")} km
                    </p>
                  )}
                  <p className="mt-1 text-xs text-slate-500">
                    {a.type} allocation · since {fmtDateTime(a.start_at)}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      {/* Big one-tap actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link
          to="/driver/trips"
          className="flex flex-col items-center gap-1 rounded-xl bg-sky-600 py-6 text-white shadow active:bg-sky-700"
        >
          <span className="text-3xl" aria-hidden>
            {openTrip ? "🏁" : "🚗"}
          </span>
          <span className="font-semibold">{openTrip ? "Finish trip" : "Start trip"}</span>
        </Link>
        <Link
          to="/driver/handover"
          className="flex flex-col items-center gap-1 rounded-xl bg-slate-700 py-6 text-white shadow active:bg-slate-800"
        >
          <span className="text-3xl" aria-hidden>
            🔑
          </span>
          <span className="font-semibold">Handover</span>
        </Link>
      </div>

      <Card title="My alerts">
        {alerts.loading ? (
          <Loading />
        ) : (alerts.data ?? []).length === 0 ? (
          <Empty>Nothing needs your attention.</Empty>
        ) : (
          <ul className="space-y-2">
            {(alerts.data ?? []).map((n) => (
              <li key={n.id} className="flex items-start gap-2 text-sm">
                <Badge value={n.severity} />
                <span>{n.message}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
