import { useState, type FormEvent } from "react";
import { MaintenanceApi } from "../../../api/resources";
import type { MaintenanceRule } from "../../../api/types";
import Modal from "../../../components/Modal";
import {
  Button,
  Card,
  Empty,
  ErrorText,
  Field,
  Input,
  Loading,
  Table,
} from "../../../components/ui";
import { useLoad } from "../../../hooks/useLoad";
import { fmtDate, fmtKm, todayISO } from "../../../lib/fmt";

interface FormState {
  name: string;
  interval_km: string;
  interval_months: string;
  last_service_km: string;
  last_service_date: string;
}

const EMPTY: FormState = {
  name: "Revizie",
  interval_km: "15000",
  interval_months: "12",
  last_service_km: "0",
  last_service_date: todayISO(),
};

export default function MaintenanceTab({ vehicleId }: { vehicleId: number }) {
  const { data, loading, reload } = useLoad(() => MaintenanceApi.list(vehicleId), [vehicleId]);
  const [editing, setEditing] = useState<MaintenanceRule | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (patch: Partial<FormState>) => setForm((f) => ({ ...f, ...patch }));

  function openCreate() {
    setEditing(null);
    setForm(EMPTY);
    setError(null);
    setOpen(true);
  }

  function openEdit(rule: MaintenanceRule) {
    setEditing(rule);
    setForm({
      name: rule.name,
      interval_km: String(rule.interval_km),
      interval_months: String(rule.interval_months),
      last_service_km: String(rule.last_service_km),
      last_service_date: rule.last_service_date,
    });
    setError(null);
    setOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const payload = {
      name: form.name,
      interval_km: Number(form.interval_km),
      interval_months: Number(form.interval_months),
      last_service_km: Number(form.last_service_km),
      last_service_date: form.last_service_date,
    };
    try {
      if (editing) {
        await MaintenanceApi.update(editing.id, payload);
      } else {
        await MaintenanceApi.create({ ...payload, vehicle_id: vehicleId });
      }
      setOpen(false);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(rule: MaintenanceRule) {
    if (!window.confirm(`Hide rule "${rule.name}"?`)) return;
    await MaintenanceApi.remove(rule.id);
    reload();
  }

  return (
    <Card
      title="Maintenance rules (alerts fire at <1000 km or <30 days to due)"
      actions={<Button onClick={openCreate}>Add rule</Button>}
    >
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No maintenance rules — the alert engine skips this vehicle.</Empty>
      ) : (
        <Table headers={["Name", "Every (km)", "Every (months)", "Last service km", "Last service date", ""]}>
          {(data ?? []).map((rule) => (
            <tr key={rule.id}>
              <td className="px-3 py-2 font-medium">{rule.name}</td>
              <td className="px-3 py-2">{fmtKm(rule.interval_km)}</td>
              <td className="px-3 py-2">{rule.interval_months}</td>
              <td className="px-3 py-2">{fmtKm(rule.last_service_km)}</td>
              <td className="px-3 py-2">{fmtDate(rule.last_service_date)}</td>
              <td className="px-3 py-2 text-right">
                <Button variant="ghost" onClick={() => openEdit(rule)}>
                  Edit
                </Button>
                <Button variant="ghost" className="text-red-600" onClick={() => handleDelete(rule)}>
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </Table>
      )}

      <Modal
        title={editing ? "Edit maintenance rule" : "Add maintenance rule"}
        open={open}
        onClose={() => setOpen(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-3">
          <Field label="Name">
            <Input value={form.name} onChange={(e) => set({ name: e.target.value })} required />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Interval (km)">
              <Input
                type="number"
                min={1}
                value={form.interval_km}
                onChange={(e) => set({ interval_km: e.target.value })}
                required
              />
            </Field>
            <Field label="Interval (months)">
              <Input
                type="number"
                min={1}
                value={form.interval_months}
                onChange={(e) => set({ interval_months: e.target.value })}
                required
              />
            </Field>
            <Field label="Last service odometer (km)">
              <Input
                type="number"
                min={0}
                value={form.last_service_km}
                onChange={(e) => set({ last_service_km: e.target.value })}
                required
              />
            </Field>
            <Field label="Last service date">
              <Input
                type="date"
                value={form.last_service_date}
                onChange={(e) => set({ last_service_date: e.target.value })}
                required
              />
            </Field>
          </div>
          <ErrorText message={error} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? "Saving…" : "Save"}
            </Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
}
