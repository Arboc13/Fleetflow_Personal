import { useMemo, useState, type FormEvent } from "react";
import { AllocationsApi, HandoverApi, VehiclesApi } from "../../api/resources";
import type { HandoverDirection } from "../../api/types";
import {
  Badge,
  Button,
  Card,
  Empty,
  ErrorText,
  Field,
  Input,
  Loading,
  Select,
  Textarea,
  cls,
} from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";

const CLEANLINESS = ["clean", "acceptable", "dirty"];

export default function DriverHandoverPage() {
  const allocations = useLoad(() => AllocationsApi.list());
  const vehicles = useLoad(() => VehiclesApi.list());
  const reports = useLoad(() => HandoverApi.list());

  const active = (allocations.data ?? []).filter((a) => a.status === "active");
  const vehicleById = useMemo(
    () => new Map((vehicles.data ?? []).map((v) => [v.id, v])),
    [vehicles.data],
  );

  const [allocationId, setAllocationId] = useState("");
  const [direction, setDirection] = useState<HandoverDirection>("handover");
  const [km, setKm] = useState("");
  const [fuelPct, setFuelPct] = useState("50");
  const [cleanliness, setCleanliness] = useState("clean");
  const [observations, setObservations] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [savedId, setSavedId] = useState<number | null>(null);

  const selectedAllocation =
    active.length === 1 ? active[0] : active.find((a) => String(a.id) === allocationId);

  async function submit(e: FormEvent, close: boolean) {
    e.preventDefault();
    if (!selectedAllocation) return;
    setBusy(true);
    setError(null);
    try {
      const report = await HandoverApi.create({
        allocation_id: selectedAllocation.id,
        direction,
        km: Number(km),
        fuel_level_pct: Number(fuelPct),
        cleanliness,
        visual_observations: observations || null,
      });
      if (close) await HandoverApi.close(report.id);
      setSavedId(report.id);
      setKm("");
      setObservations("");
      reports.reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const myReports = reports.data ?? [];

  return (
    <>
      <Card title="Vehicle handover report (proces-verbal)">
        {allocations.loading ? (
          <Loading />
        ) : active.length === 0 ? (
          <Empty>No active allocation — nothing to hand over.</Empty>
        ) : (
          <form className="space-y-3">
            {active.length > 1 && (
              <Field label="Allocation">
                <Select
                  value={allocationId}
                  onChange={(e) => setAllocationId(e.target.value)}
                  required
                >
                  <option value="">Choose…</option>
                  {active.map((a) => (
                    <option key={a.id} value={a.id}>
                      {vehicleById.get(a.vehicle_id)?.plate ?? `Vehicle #${a.vehicle_id}`}
                    </option>
                  ))}
                </Select>
              </Field>
            )}
            {selectedAllocation && (
              <p className="text-sm font-medium text-slate-700">
                Vehicle:{" "}
                {vehicleById.get(selectedAllocation.vehicle_id)?.plate ??
                  `#${selectedAllocation.vehicle_id}`}
              </p>
            )}

            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  ["handover", "📤 Receiving"],
                  ["return", "📥 Returning"],
                ] as [HandoverDirection, string][]
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setDirection(value)}
                  className={cls(
                    "rounded-lg border py-3 text-sm font-medium",
                    direction === value
                      ? "border-sky-600 bg-sky-50 text-sky-700"
                      : "border-slate-200 bg-white text-slate-600",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>

            <Field label="Odometer (km)">
              <Input
                type="number"
                inputMode="numeric"
                min={0}
                value={km}
                onChange={(e) => setKm(e.target.value)}
                required
                className="py-3 text-lg"
              />
            </Field>
            <Field label={`Fuel level: ${fuelPct}%`}>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={fuelPct}
                onChange={(e) => setFuelPct(e.target.value)}
                className="w-full accent-sky-600"
              />
            </Field>
            <Field label="Cleanliness">
              <Select value={cleanliness} onChange={(e) => setCleanliness(e.target.value)}>
                {CLEANLINESS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Visual observations (scratches, damage…)">
              <Textarea value={observations} onChange={(e) => setObservations(e.target.value)} />
            </Field>

            {savedId && !error && (
              <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
                Report #{savedId} saved.
              </p>
            )}
            <ErrorText message={error} />
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="secondary"
                disabled={busy || !selectedAllocation || !km}
                onClick={(e) => submit(e, false)}
                className="py-3"
              >
                Save draft
              </Button>
              <Button
                disabled={busy || !selectedAllocation || !km}
                onClick={(e) => submit(e, true)}
                className="py-3"
              >
                {busy ? "Saving…" : "Sign & close"}
              </Button>
            </div>
            <p className="text-xs text-slate-500">
              A closed report is final and cannot be changed (rule 2.3).
            </p>
          </form>
        )}
      </Card>

      <Card title="My reports">
        {reports.loading ? (
          <Loading />
        ) : myReports.length === 0 ? (
          <Empty>No handover reports yet.</Empty>
        ) : (
          <ul className="divide-y divide-slate-100">
            {myReports.map((r) => (
              <li key={r.id} className="flex items-center gap-3 py-2.5 text-sm">
                <span className="text-lg" aria-hidden>
                  {r.direction === "handover" ? "📤" : "📥"}
                </span>
                <div className="flex-1">
                  <p className="font-medium">
                    {r.direction === "handover" ? "Received" : "Returned"} at{" "}
                    {r.km.toLocaleString("ro-RO")} km
                  </p>
                  <p className="text-xs text-slate-500">
                    Fuel {r.fuel_level_pct}% · {r.cleanliness ?? "—"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge value={r.status} />
                  {r.status === "draft" && (
                    <Button variant="ghost" onClick={() => HandoverApi.close(r.id).then(reports.reload)}>
                      Close
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
