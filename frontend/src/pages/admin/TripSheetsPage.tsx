import { useMemo, useState, type FormEvent } from "react";
import { DriversApi, TripSheetsApi, VehiclesApi } from "../../api/resources";
import type { TripSheet } from "../../api/types";
import Modal from "../../components/Modal";
import {
  Badge,
  Button,
  Empty,
  ErrorText,
  Field,
  Input,
  Loading,
  Select,
  Table,
} from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { fmtDateTime, fmtKm, fromLocalInput, toLocalInput } from "../../lib/fmt";

function CloseTripModal({
  trip,
  onDone,
  onClose,
}: {
  trip: TripSheet;
  onDone: () => void;
  onClose: () => void;
}) {
  const [arrival, setArrival] = useState(toLocalInput());
  const [endKm, setEndKm] = useState(String(trip.start_km));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const kmError =
    endKm !== "" && Number(endKm) <= trip.start_km
      ? `Must be greater than the start odometer (${trip.start_km} km)`
      : null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await TripSheetsApi.close(trip.id, fromLocalInput(arrival), Number(endKm));
      onDone();
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={`Close trip sheet #${trip.id}`} open onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <p className="text-sm text-slate-600">
          Closing is final: the sheet becomes read-only and the vehicle's odometer is
          advanced to the end value.
        </p>
        <Field label="Arrival time">
          <Input
            type="datetime-local"
            value={arrival}
            onChange={(e) => setArrival(e.target.value)}
            required
          />
        </Field>
        <Field label="End odometer (km)" error={kmError}>
          <Input
            type="number"
            min={trip.start_km + 1}
            value={endKm}
            onChange={(e) => setEndKm(e.target.value)}
            required
          />
        </Field>
        <ErrorText message={error} />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy}>
            {busy ? "Closing…" : "Close trip"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function TripSheetsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const trips = useLoad(
    () => TripSheetsApi.list(statusFilter ? { status_filter: statusFilter } : undefined),
    [statusFilter],
  );
  const vehicles = useLoad(() => VehiclesApi.list());
  const drivers = useLoad(() => DriversApi.list());
  // Closing a trip advances the vehicle odometer, so refetch vehicles too.
  const refresh = () => {
    trips.reload();
    vehicles.reload();
  };

  const [createOpen, setCreateOpen] = useState(false);
  const [closing, setClosing] = useState<TripSheet | null>(null);
  const [form, setForm] = useState({
    vehicle_id: "",
    driver_id: "",
    departure_at: toLocalInput(),
    start_km: "",
    purpose: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const vehicleById = useMemo(
    () => new Map((vehicles.data ?? []).map((v) => [v.id, v])),
    [vehicles.data],
  );
  const driverById = useMemo(
    () => new Map((drivers.data ?? []).map((d) => [d.id, d])),
    [drivers.data],
  );

  function openCreate() {
    setForm({
      vehicle_id: "",
      driver_id: "",
      departure_at: toLocalInput(),
      start_km: "",
      purpose: "",
    });
    setError(null);
    setCreateOpen(true);
  }

  function pickVehicle(id: string) {
    const v = vehicleById.get(Number(id));
    setForm((f) => ({
      ...f,
      vehicle_id: id,
      // pre-fill from the vehicle's odometer; still editable
      start_km: v ? String(v.current_km) : f.start_km,
    }));
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await TripSheetsApi.create({
        vehicle_id: Number(form.vehicle_id),
        driver_id: Number(form.driver_id),
        departure_at: fromLocalInput(form.departure_at),
        start_km: Number(form.start_km),
        purpose: form.purpose || null,
      });
      setCreateOpen(false);
      refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(trip: TripSheet) {
    if (!window.confirm(`Hide trip sheet #${trip.id}?`)) return;
    try {
      await TripSheetsApi.remove(trip.id);
      trips.reload();
    } catch (err) {
      window.alert((err as Error).message); // closed sheets are immutable (rule 2.3)
    }
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Trip sheets</h1>
        <div className="flex items-center gap-3">
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-36"
          >
            <option value="">All statuses</option>
            <option value="draft">draft</option>
            <option value="closed">closed</option>
          </Select>
          <Button onClick={openCreate}>New trip sheet</Button>
        </div>
      </div>
      <ErrorText message={trips.error} />
      {trips.loading ? (
        <Loading />
      ) : (trips.data ?? []).length === 0 ? (
        <Empty>No trip sheets.</Empty>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <Table
            headers={["#", "Vehicle", "Driver", "Departure", "Arrival", "Start km", "End km", "Status", ""]}
          >
            {(trips.data ?? []).map((t) => (
              <tr key={t.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 text-slate-400">{t.id}</td>
                <td className="px-3 py-2 font-medium">
                  {vehicleById.get(t.vehicle_id)?.plate ?? `#${t.vehicle_id}`}
                </td>
                <td className="px-3 py-2">
                  {driverById.get(t.driver_id)?.full_name ?? `#${t.driver_id}`}
                </td>
                <td className="px-3 py-2">{fmtDateTime(t.departure_at)}</td>
                <td className="px-3 py-2">{fmtDateTime(t.arrival_at)}</td>
                <td className="px-3 py-2">{fmtKm(t.start_km)}</td>
                <td className="px-3 py-2">{fmtKm(t.end_km)}</td>
                <td className="px-3 py-2">
                  <Badge value={t.status} />
                </td>
                <td className="px-3 py-2 text-right">
                  {t.status === "draft" && (
                    <>
                      <Button variant="ghost" onClick={() => setClosing(t)}>
                        Close
                      </Button>
                      <Button
                        variant="ghost"
                        className="text-red-600"
                        onClick={() => handleDelete(t)}
                      >
                        Delete
                      </Button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        </div>
      )}

      <Modal title="New trip sheet" open={createOpen} onClose={() => setCreateOpen(false)}>
        <form onSubmit={handleCreate} className="space-y-3">
          <Field label="Vehicle">
            <Select value={form.vehicle_id} onChange={(e) => pickVehicle(e.target.value)} required>
              <option value="">Select a vehicle…</option>
              {(vehicles.data ?? []).map((v) => (
                <option key={v.id} value={v.id}>
                  {v.plate} — {v.make} {v.model} ({fmtKm(v.current_km)})
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Driver">
            <Select
              value={form.driver_id}
              onChange={(e) => setForm((f) => ({ ...f, driver_id: e.target.value }))}
              required
            >
              <option value="">Select a driver…</option>
              {(drivers.data ?? []).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_name}
                </option>
              ))}
            </Select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Departure">
              <Input
                type="datetime-local"
                value={form.departure_at}
                onChange={(e) => setForm((f) => ({ ...f, departure_at: e.target.value }))}
                required
              />
            </Field>
            <Field label="Start odometer (km)">
              <Input
                type="number"
                min={0}
                value={form.start_km}
                onChange={(e) => setForm((f) => ({ ...f, start_km: e.target.value }))}
                required
              />
            </Field>
          </div>
          <Field label="Purpose">
            <Input
              value={form.purpose}
              onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))}
              placeholder="e.g. delivery to Cluj warehouse"
            />
          </Field>
          <ErrorText message={error} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? "Saving…" : "Create"}
            </Button>
          </div>
        </form>
      </Modal>

      {closing && (
        <CloseTripModal trip={closing} onDone={refresh} onClose={() => setClosing(null)} />
      )}
    </>
  );
}
