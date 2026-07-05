import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertsApi, NotificationsApi, VehiclesApi } from "../../api/resources";
import { useLoad } from "../../hooks/useLoad";
import { fmtDateTime } from "../../lib/fmt";
import { Badge, Button, Card, Empty, Loading, cls } from "../../components/ui";

function StatCard({ label, value, tone }: { label: string; value: number; tone?: "green" | "yellow" | "red" }) {
  const toneCls =
    tone === "green"
      ? "text-green-700"
      : tone === "yellow"
        ? "text-yellow-700"
        : tone === "red"
          ? "text-red-700"
          : "text-slate-900";
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className={cls("mt-1 text-3xl font-bold", toneCls)}>{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const vehicles = useLoad(() => VehiclesApi.list());
  const alerts = useLoad(() => NotificationsApi.list(true));
  const [scanMessage, setScanMessage] = useState<string | null>(null);

  async function runScan() {
    setScanMessage("Running…");
    try {
      const { created } = await AlertsApi.run();
      setScanMessage(`Scan finished — ${created} new alert${created === 1 ? "" : "s"}.`);
      alerts.reload();
    } catch (err) {
      setScanMessage((err as Error).message);
    }
  }

  const list = vehicles.data ?? [];
  const unread = alerts.data ?? [];
  const critical = unread.filter((n) => n.severity === "critical");
  const warnings = unread.filter((n) => n.severity === "warning");

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-3">
          {scanMessage && <span className="text-sm text-slate-500">{scanMessage}</span>}
          <Button variant="secondary" onClick={runScan}>
            Run alert scan
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatCard label="Vehicles" value={list.length} />
        <StatCard label="Active" value={list.filter((v) => v.status === "active").length} tone="green" />
        <StatCard label="In service" value={list.filter((v) => v.status === "in_service").length} tone="yellow" />
        <StatCard label="Critical alerts" value={critical.length} tone="red" />
        <StatCard label="Warnings" value={warnings.length} tone="yellow" />
      </div>

      <Card
        title="Unread alerts"
        actions={
          <Link to="/admin/notifications" className="text-sm text-sky-700 hover:underline">
            View all
          </Link>
        }
      >
        {alerts.loading ? (
          <Loading />
        ) : unread.length === 0 ? (
          <Empty>No unread alerts — everything is green.</Empty>
        ) : (
          <ul className="divide-y divide-slate-100">
            {/* Critical (red) first, then warnings (yellow) */}
            {[...critical, ...warnings].slice(0, 8).map((n) => (
              <li key={n.id} className="flex items-center gap-3 py-2 text-sm">
                <Badge value={n.severity} />
                <span className="flex-1">{n.message}</span>
                <span className="whitespace-nowrap text-xs text-slate-400">
                  {fmtDateTime(n.created_at)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
