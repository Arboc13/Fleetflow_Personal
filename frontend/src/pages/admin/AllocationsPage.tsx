import { useMemo, useState, type FormEvent } from "react";
import { AllocationsApi, DriversApi, HandoverApi, VehiclesApi } from "../../api/resources";
import type { Allocation, AllocationType } from "../../api/types";
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
import { fmtDateTime, fromLocalInput, toLocalInput } from "../../lib/fmt";

function HandoverReportsModal({
  allocation,
  onClose,
}: {
  allocation: Allocation;
  onClose: () => void;
}) {
  const { data, loading } = useLoad(() => HandoverApi.list(allocation.id), [allocation.id]);
  return (
    <Modal title={`Handover reports — allocation #${allocation.id}`} open onClose={onClose}>
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No handover reports for this allocation.</Empty>
      ) : (
        <Table headers={["Direction", "Odometer", "Fuel %", "Cleanliness", "Observations", "Status"]}>
          {(data ?? []).map((r) => (
            <tr key={r.id}>
              <td className="px-3 py-2">{r.direction === "handover" ? "Handover" : "Return"}</td>
              <td className="px-3 py-2">{r.km.toLocaleString("ro-RO")} km</td>
              <td className="px-3 py-2">{r.fuel_level_pct}%</td>
              <td className="px-3 py-2">{r.cleanliness ?? "—"}</td>
              <td className="max-w-xs px-3 py-2">{r.visual_observations ?? "—"}</td>
              <td className="px-3 py-2">
                <Badge value={r.status} />
              </td>
            </tr>
          ))}
        </Table>
      )}
    </Modal>
  );
}

export default function AllocationsPage() {
  const allocations = useLoad(() => AllocationsApi.list());
  const vehicles = useLoad(() => VehiclesApi.list());
  const drivers = useLoad(() => DriversApi.list());

  const [open, setOpen] = useState(false);
  const [reportsFor, setReportsFor] = useState<Allocation | null>(null);
  const [form, setForm] = useState({
    vehicle_id: "",
    driver_id: "",
    start_at: toLocalInput(),
    end_at: "",
    type: "trip" as AllocationType,
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

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await AllocationsApi.create({
        vehicle_id: Number(form.vehicle_id),
        driver_id: Number(form.driver_id),
        start_at: fromLocalInput(form.start_at),
        end_at: form.end_at ? fromLocalInput(form.end_at) : null,
        type: form.type,
      });
      setOpen(false);
      allocations.reload();
    } catch (err) {
      // A 409 here is the DB exclusion constraint: vehicle or driver already
      // allocated in an overlapping period (rule 2.1).
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(a: Allocation) {
    if (!window.confirm(`Hide allocation #${a.id}?`)) return;
    await AllocationsApi.remove(a.id);
    allocations.reload();
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Allocations</h1>
        <Button onClick={() => setOpen(true)}>New allocation</Button>
      </div>
      <ErrorText message={allocations.error} />
      {allocations.loading ? (
        <Loading />
      ) : (allocations.data ?? []).length === 0 ? (
        <Empty>No allocations yet.</Empty>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <Table headers={["Vehicle", "Driver", "From", "To", "Type", "Status", ""]}>
            {(allocations.data ?? []).map((a) => (
              <tr key={a.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-medium">
                  {vehicleById.get(a.vehicle_id)?.plate ?? `#${a.vehicle_id}`}
                </td>
                <td className="px-3 py-2">
                  {driverById.get(a.driver_id)?.full_name ?? `#${a.driver_id}`}
                </td>
                <td className="px-3 py-2">{fmtDateTime(a.start_at)}</td>
                <td className="px-3 py-2">{a.end_at ? fmtDateTime(a.end_at) : "open-ended"}</td>
                <td className="px-3 py-2">{a.type}</td>
                <td className="px-3 py-2">
                  <Badge value={a.status} />
                </td>
                <td className="px-3 py-2 text-right">
                  <Button variant="ghost" onClick={() => setReportsFor(a)}>
                    Reports
                  </Button>
                  <Button variant="ghost" className="text-red-600" onClick={() => handleDelete(a)}>
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
        </div>
      )}

      <Modal title="New allocation" open={open} onClose={() => setOpen(false)}>
        <form onSubmit={handleSubmit} className="space-y-3">
          <Field label="Vehicle">
            <Select
              value={form.vehicle_id}
              onChange={(e) => setForm((f) => ({ ...f, vehicle_id: e.target.value }))}
              required
            >
              <option value="">Select a vehicle…</option>
              {(vehicles.data ?? [])
                .filter((v) => v.status === "active")
                .map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.plate} — {v.make} {v.model}
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
            <Field label="From">
              <Input
                type="datetime-local"
                value={form.start_at}
                onChange={(e) => setForm((f) => ({ ...f, start_at: e.target.value }))}
                required
              />
            </Field>
            <Field label="To" hint="Leave empty for an open-ended (permanent) allocation">
              <Input
                type="datetime-local"
                value={form.end_at}
                onChange={(e) => setForm((f) => ({ ...f, end_at: e.target.value }))}
              />
            </Field>
          </div>
          <Field label="Type">
            <Select
              value={form.type}
              onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as AllocationType }))}
            >
              <option value="trip">trip</option>
              <option value="permanent">permanent</option>
            </Select>
          </Field>
          <ErrorText message={error} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? "Saving…" : "Allocate"}
            </Button>
          </div>
        </form>
      </Modal>

      {reportsFor && (
        <HandoverReportsModal allocation={reportsFor} onClose={() => setReportsFor(null)} />
      )}
    </>
  );
}
