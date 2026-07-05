import { useMemo, useState, type FormEvent } from "react";
import { AllocationsApi, TripSheetsApi, VehiclesApi } from "../../api/resources";
import type { TripSheet } from "../../api/types";
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
} from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { fmtDateTime, fmtKm, fromLocalInput, toLocalInput } from "../../lib/fmt";

export default function DriverTripsPage() {
  const trips = useLoad(() => TripSheetsApi.list());
  const allocations = useLoad(() => AllocationsApi.list());
  const vehicles = useLoad(() => VehiclesApi.list());

  const vehicleById = useMemo(
    () => new Map((vehicles.data ?? []).map((v) => [v.id, v])),
    [vehicles.data],
  );
  const myVehicleIds = useMemo(
    () =>
      [...new Set(
        (allocations.data ?? [])
          .filter((a) => a.status === "active")
          .map((a) => a.vehicle_id),
      )],
    [allocations.data],
  );

  const all = trips.data ?? [];
  const openTrip = all.find((t) => t.status === "draft");
  const history = all.filter((t) => t.status === "closed");

  return (
    <>
      {trips.loading ? (
        <Loading />
      ) : openTrip ? (
        <CloseTripCard trip={openTrip} plate={vehicleById.get(openTrip.vehicle_id)?.plate} onDone={trips.reload} />
      ) : (
        <StartTripCard
          vehicleIds={myVehicleIds}
          vehicleById={vehicleById}
          onDone={trips.reload}
        />
      )}

      <Card title="Past trips">
        {history.length === 0 ? (
          <Empty>No closed trips yet.</Empty>
        ) : (
          <ul className="divide-y divide-slate-100">
            {history.map((t) => (
              <li key={t.id} className="py-2.5 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {vehicleById.get(t.vehicle_id)?.plate ?? `#${t.vehicle_id}`}
                  </span>
                  <Badge value={t.status} />
                </div>
                <p className="text-xs text-slate-500">
                  {fmtDateTime(t.departure_at)} → {fmtDateTime(t.arrival_at)} ·{" "}
                  {t.end_km !== null ? `${t.end_km - t.start_km} km` : ""}
                </p>
                {t.purpose && <p className="text-xs text-slate-400">{t.purpose}</p>}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}

function StartTripCard({
  vehicleIds,
  vehicleById,
  onDone,
}: {
  vehicleIds: number[];
  vehicleById: Map<number, { plate: string; current_km: number }>;
  onDone: () => void;
}) {
  const [vehicleId, setVehicleId] = useState(vehicleIds.length === 1 ? String(vehicleIds[0]) : "");
  const [startKm, setStartKm] = useState("");
  const [purpose, setPurpose] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const selected = vehicleId ? vehicleById.get(Number(vehicleId)) : undefined;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      // driver_id omitted on purpose — the backend uses the caller's profile
      await TripSheetsApi.create({
        vehicle_id: Number(vehicleId),
        departure_at: new Date().toISOString(),
        start_km: Number(startKm),
        purpose: purpose || null,
      });
      onDone();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (vehicleIds.length === 0) {
    return (
      <Card title="Start a trip">
        <Empty>You have no allocated vehicle — ask your fleet manager.</Empty>
      </Card>
    );
  }

  return (
    <Card title="Start a trip">
      <form onSubmit={handleSubmit} className="space-y-3">
        <Field label="Vehicle">
          <Select value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} required>
            <option value="">Choose…</option>
            {vehicleIds.map((id) => (
              <option key={id} value={id}>
                {vehicleById.get(id)?.plate ?? `#${id}`}
              </option>
            ))}
          </Select>
        </Field>
        <Field
          label="Odometer now (km)"
          hint={selected ? `Last known: ${fmtKm(selected.current_km)}` : undefined}
        >
          {/* inputMode brings up the phone's numeric keypad */}
          <Input
            type="number"
            inputMode="numeric"
            min={0}
            value={startKm}
            onChange={(e) => setStartKm(e.target.value)}
            placeholder={selected ? String(selected.current_km) : ""}
            required
            className="py-3 text-lg"
          />
        </Field>
        <Field label="Purpose (optional)">
          <Input value={purpose} onChange={(e) => setPurpose(e.target.value)} className="py-3" />
        </Field>
        <ErrorText message={error} />
        <Button type="submit" disabled={busy} className="w-full py-3 text-base">
          {busy ? "Starting…" : "🚗 Start trip now"}
        </Button>
      </form>
    </Card>
  );
}

function CloseTripCard({
  trip,
  plate,
  onDone,
}: {
  trip: TripSheet;
  plate: string | undefined;
  onDone: () => void;
}) {
  const [endKm, setEndKm] = useState("");
  const [arrival, setArrival] = useState(toLocalInput());
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const kmError =
    endKm !== "" && Number(endKm) <= trip.start_km
      ? `Must be more than the departure odometer (${fmtKm(trip.start_km)})`
      : null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await TripSheetsApi.close(trip.id, fromLocalInput(arrival), Number(endKm));
      onDone();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title={`Trip in progress — ${plate ?? `vehicle #${trip.vehicle_id}`}`}>
      <p className="mb-3 text-sm text-slate-600">
        Departed {fmtDateTime(trip.departure_at)} at {fmtKm(trip.start_km)}.
        {trip.purpose ? ` Purpose: ${trip.purpose}.` : ""}
      </p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <Field label="Arrival time">
          <Input
            type="datetime-local"
            value={arrival}
            onChange={(e) => setArrival(e.target.value)}
            required
            className="py-3"
          />
        </Field>
        <Field label="Odometer now (km)" error={kmError}>
          <Input
            type="number"
            inputMode="numeric"
            min={trip.start_km + 1}
            value={endKm}
            onChange={(e) => setEndKm(e.target.value)}
            required
            className="py-3 text-lg"
          />
        </Field>
        <p className="text-xs text-slate-500">
          Closing the sheet is final — it can't be edited afterwards.
        </p>
        <ErrorText message={error} />
        <Button type="submit" disabled={busy} className="w-full py-3 text-base">
          {busy ? "Closing…" : "🏁 Finish trip"}
        </Button>
      </form>
    </Card>
  );
}
