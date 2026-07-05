import { useState, type FormEvent } from "react";
import { ServiceRecordsApi } from "../../../api/resources";
import type { ServiceRecord } from "../../../api/types";
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
  Textarea,
} from "../../../components/ui";
import { useLoad } from "../../../hooks/useLoad";
import { fmtDate, fmtKm, fmtMoney, todayISO } from "../../../lib/fmt";

interface FormState {
  date: string;
  km_at_service: string;
  work_description: string;
  parts_replaced: string;
  cost: string;
}

const EMPTY: FormState = {
  date: todayISO(),
  km_at_service: "0",
  work_description: "",
  parts_replaced: "",
  cost: "0",
};

export default function ServiceTab({ vehicleId }: { vehicleId: number }) {
  const { data, loading, reload } = useLoad(() => ServiceRecordsApi.list(vehicleId), [vehicleId]);
  const [editing, setEditing] = useState<ServiceRecord | null>(null);
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

  function openEdit(rec: ServiceRecord) {
    setEditing(rec);
    setForm({
      date: rec.date,
      km_at_service: String(rec.km_at_service),
      work_description: rec.work_description,
      parts_replaced: rec.parts_replaced ?? "",
      cost: String(rec.cost),
    });
    setError(null);
    setOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const payload = {
      date: form.date,
      km_at_service: Number(form.km_at_service),
      work_description: form.work_description,
      parts_replaced: form.parts_replaced || null,
      cost: Number(form.cost),
    };
    try {
      if (editing) {
        await ServiceRecordsApi.update(editing.id, payload);
      } else {
        await ServiceRecordsApi.create({ ...payload, vehicle_id: vehicleId });
      }
      setOpen(false);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(rec: ServiceRecord) {
    if (!window.confirm("Hide this service record?")) return;
    await ServiceRecordsApi.remove(rec.id);
    reload();
  }

  return (
    <Card title="Service history" actions={<Button onClick={openCreate}>Add record</Button>}>
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No service records.</Empty>
      ) : (
        <Table headers={["Date", "Odometer", "Work", "Parts", "Cost", ""]}>
          {(data ?? []).map((rec) => (
            <tr key={rec.id}>
              <td className="px-3 py-2">{fmtDate(rec.date)}</td>
              <td className="px-3 py-2">{fmtKm(rec.km_at_service)}</td>
              <td className="max-w-sm px-3 py-2">{rec.work_description}</td>
              <td className="max-w-xs px-3 py-2">{rec.parts_replaced ?? "—"}</td>
              <td className="px-3 py-2">{fmtMoney(rec.cost)}</td>
              <td className="px-3 py-2 text-right">
                <Button variant="ghost" onClick={() => openEdit(rec)}>
                  Edit
                </Button>
                <Button variant="ghost" className="text-red-600" onClick={() => handleDelete(rec)}>
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </Table>
      )}

      <Modal
        title={editing ? "Edit service record" : "Add service record"}
        open={open}
        onClose={() => setOpen(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Date">
              <Input
                type="date"
                value={form.date}
                onChange={(e) => set({ date: e.target.value })}
                required
              />
            </Field>
            <Field label="Odometer at service (km)">
              <Input
                type="number"
                min={0}
                value={form.km_at_service}
                onChange={(e) => set({ km_at_service: e.target.value })}
                required
              />
            </Field>
          </div>
          <Field label="Work performed">
            <Textarea
              value={form.work_description}
              onChange={(e) => set({ work_description: e.target.value })}
              required
            />
          </Field>
          <Field label="Parts replaced">
            <Input
              value={form.parts_replaced}
              onChange={(e) => set({ parts_replaced: e.target.value })}
            />
          </Field>
          <Field label="Cost (lei)">
            <Input
              type="number"
              min={0}
              step="0.01"
              value={form.cost}
              onChange={(e) => set({ cost: e.target.value })}
            />
          </Field>
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
