import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ReportsApi } from "../../api/resources";
import type { TCOReport } from "../../api/types";
import { Button, Card, Empty, ErrorText, Field, Input, Loading, Table } from "../../components/ui";
import { fmtKm, fmtMoney, todayISO } from "../../lib/fmt";

export default function ReportsPage() {
  const [dateFrom, setDateFrom] = useState(todayISO(-30));
  const [dateTo, setDateTo] = useState(todayISO());
  const [report, setReport] = useState<TCOReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<"xlsx" | "pdf" | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      setReport(await ReportsApi.tco(dateFrom, dateTo));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function exportAs(format: "xlsx" | "pdf") {
    setExporting(format);
    setError(null);
    try {
      await ReportsApi.export(dateFrom, dateTo, format);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setExporting(null);
    }
  }

  const chartData = (report?.rows ?? [])
    .filter((r) => r.cost_per_km !== null)
    .map((r) => ({ plate: r.plate, "cost / km": r.cost_per_km }));

  return (
    <>
      <h1 className="text-xl font-bold">Cost & utilization report (TCO)</h1>

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <Field label="From">
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </Field>
          <Field label="To">
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </Field>
          <Button onClick={run} disabled={loading}>
            {loading ? "Computing…" : "Run report"}
          </Button>
          {report && (
            <>
              <Button
                variant="secondary"
                onClick={() => exportAs("xlsx")}
                disabled={exporting !== null}
              >
                {exporting === "xlsx" ? "Exporting…" : "Export Excel"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => exportAs("pdf")}
                disabled={exporting !== null}
              >
                {exporting === "pdf" ? "Exporting…" : "Export PDF"}
              </Button>
            </>
          )}
        </div>
      </Card>

      <ErrorText message={error} />
      {loading && <Loading />}

      {report && !loading && (
        <>
          <Card title={`Per vehicle — ${report.date_from} → ${report.date_to}`}>
            {report.rows.length === 0 ? (
              <Empty>No vehicles in this period.</Empty>
            ) : (
              <Table
                headers={[
                  "Vehicle",
                  "Fuel",
                  "Service",
                  "Documents",
                  "Total",
                  "Km driven",
                  "Cost / km",
                  "Utilization",
                ]}
              >
                {report.rows.map((r) => (
                  <tr key={r.vehicle_id}>
                    <td className="px-3 py-2 font-medium">
                      {r.plate}{" "}
                      <span className="text-xs text-slate-500">
                        {r.make} {r.model}
                      </span>
                    </td>
                    <td className="px-3 py-2">{fmtMoney(r.fuel_cost)}</td>
                    <td className="px-3 py-2">{fmtMoney(r.service_cost)}</td>
                    <td className="px-3 py-2">{fmtMoney(r.document_cost)}</td>
                    <td className="px-3 py-2 font-medium">{fmtMoney(r.total_cost)}</td>
                    <td className="px-3 py-2">{fmtKm(r.km_driven)}</td>
                    <td className="px-3 py-2">
                      {r.cost_per_km === null ? "— (no km driven)" : fmtMoney(r.cost_per_km)}
                    </td>
                    <td className="px-3 py-2">{r.utilization_pct.toFixed(1)}%</td>
                  </tr>
                ))}
                <tr className="border-t-2 border-slate-300 bg-slate-50 font-semibold">
                  <td className="px-3 py-2">Fleet total</td>
                  <td className="px-3 py-2">{fmtMoney(report.fleet.fuel_cost)}</td>
                  <td className="px-3 py-2">{fmtMoney(report.fleet.service_cost)}</td>
                  <td className="px-3 py-2">{fmtMoney(report.fleet.document_cost)}</td>
                  <td className="px-3 py-2">{fmtMoney(report.fleet.total_cost)}</td>
                  <td className="px-3 py-2">{fmtKm(report.fleet.km_driven)}</td>
                  <td className="px-3 py-2">
                    {report.fleet.cost_per_km === null ? "—" : fmtMoney(report.fleet.cost_per_km)}
                  </td>
                  <td className="px-3 py-2">{report.fleet.utilization_pct.toFixed(1)}%</td>
                </tr>
              </Table>
            )}
          </Card>

          {chartData.length > 0 && (
            <Card title="Cost per km by vehicle">
              <div className="h-64">
                <ResponsiveContainer>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="plate" fontSize={12} />
                    <YAxis fontSize={12} />
                    <Tooltip formatter={(v) => `${Number(v).toFixed(2)} lei`} />
                    <Bar dataKey="cost / km" fill="#0284c7" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
        </>
      )}
    </>
  );
}
