import { useState, type FormEvent } from "react";
import { DocumentsApi } from "../../../api/resources";
import type { DocumentType, VehicleDocument } from "../../../api/types";
import Modal from "../../../components/Modal";
import {
  Button,
  Card,
  Empty,
  ErrorText,
  Field,
  Input,
  Loading,
  Select,
  Table,
} from "../../../components/ui";
import { useLoad } from "../../../hooks/useLoad";
import { fmtDate, fmtMoney, todayISO } from "../../../lib/fmt";

const DOC_TYPES: DocumentType[] = ["RCA", "CASCO", "ITP", "Rovinieta"];

/** Days until expiry drive the row indicator: red ≤ 5, yellow ≤ 30 (rule 2.2). */
function expiryTone(expiry: string): string {
  const days = Math.ceil((new Date(expiry).getTime() - Date.now()) / 86_400_000);
  if (days <= 5) return "text-red-700 font-semibold";
  if (days <= 30) return "text-yellow-700 font-semibold";
  return "";
}

interface FormState {
  type: DocumentType;
  series_number: string;
  issuer: string;
  cost: string;
  issue_date: string;
  expiry_date: string;
}

const EMPTY: FormState = {
  type: "RCA",
  series_number: "",
  issuer: "",
  cost: "0",
  issue_date: todayISO(),
  expiry_date: todayISO(365),
};

export default function DocumentsTab({ vehicleId }: { vehicleId: number }) {
  const { data, loading, reload } = useLoad(() => DocumentsApi.list(vehicleId), [vehicleId]);
  const [editing, setEditing] = useState<VehicleDocument | null>(null);
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

  function openEdit(doc: VehicleDocument) {
    setEditing(doc);
    setForm({
      type: doc.type,
      series_number: doc.series_number,
      issuer: doc.issuer ?? "",
      cost: String(doc.cost),
      issue_date: doc.issue_date,
      expiry_date: doc.expiry_date,
    });
    setError(null);
    setOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const payload = {
      type: form.type,
      series_number: form.series_number,
      issuer: form.issuer || null,
      cost: Number(form.cost),
      issue_date: form.issue_date,
      expiry_date: form.expiry_date,
    };
    try {
      if (editing) {
        await DocumentsApi.update(editing.id, payload);
      } else {
        await DocumentsApi.create({ ...payload, vehicle_id: vehicleId });
      }
      setOpen(false);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(doc: VehicleDocument) {
    if (!window.confirm(`Hide ${doc.type} ${doc.series_number}?`)) return;
    await DocumentsApi.remove(doc.id);
    reload();
  }

  return (
    <Card
      title="Legal documents (RCA / CASCO / ITP / Rovinietă)"
      actions={<Button onClick={openCreate}>Add document</Button>}
    >
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No documents recorded.</Empty>
      ) : (
        <Table headers={["Type", "Series", "Issuer", "Cost", "Issued", "Expires", ""]}>
          {(data ?? []).map((doc) => (
            <tr key={doc.id}>
              <td className="px-3 py-2 font-medium">{doc.type}</td>
              <td className="px-3 py-2">{doc.series_number}</td>
              <td className="px-3 py-2">{doc.issuer ?? "—"}</td>
              <td className="px-3 py-2">{fmtMoney(doc.cost)}</td>
              <td className="px-3 py-2">{fmtDate(doc.issue_date)}</td>
              <td className={`px-3 py-2 ${expiryTone(doc.expiry_date)}`}>
                {fmtDate(doc.expiry_date)}
              </td>
              <td className="px-3 py-2 text-right">
                <Button variant="ghost" onClick={() => openEdit(doc)}>
                  Edit
                </Button>
                <Button variant="ghost" className="text-red-600" onClick={() => handleDelete(doc)}>
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </Table>
      )}

      <Modal
        title={editing ? "Edit document" : "Add document"}
        open={open}
        onClose={() => setOpen(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Type">
              <Select value={form.type} onChange={(e) => set({ type: e.target.value as DocumentType })}>
                {DOC_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Series / number">
              <Input
                value={form.series_number}
                onChange={(e) => set({ series_number: e.target.value })}
                required
              />
            </Field>
            <Field label="Issuer">
              <Input value={form.issuer} onChange={(e) => set({ issuer: e.target.value })} />
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
            <Field label="Issue date">
              <Input
                type="date"
                value={form.issue_date}
                onChange={(e) => set({ issue_date: e.target.value })}
                required
              />
            </Field>
            <Field label="Expiry date">
              <Input
                type="date"
                value={form.expiry_date}
                onChange={(e) => set({ expiry_date: e.target.value })}
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
