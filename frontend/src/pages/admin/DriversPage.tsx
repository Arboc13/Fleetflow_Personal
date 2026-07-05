import { useState, type FormEvent } from "react";
import { DriversApi } from "../../api/resources";
import type { Driver } from "../../api/types";
import Modal from "../../components/Modal";
import {
  Button,
  Empty,
  ErrorText,
  Field,
  Input,
  Loading,
  Table,
} from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { fmtDate, todayISO } from "../../lib/fmt";

const CNP_RE = /^\d{13}$/;

interface FormState {
  email: string;
  full_name: string;
  password: string;
  cnp: string;
  phone: string;
  license_number: string;
  license_series: string;
  license_category: string;
  license_expiry: string;
}

const EMPTY: FormState = {
  email: "",
  full_name: "",
  password: "",
  cnp: "",
  phone: "",
  license_number: "",
  license_series: "",
  license_category: "B",
  license_expiry: todayISO(365),
};

export default function DriversPage() {
  const { data, loading, error, reload } = useLoad(() => DriversApi.list());
  const [editing, setEditing] = useState<Driver | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (patch: Partial<FormState>) => setForm((f) => ({ ...f, ...patch }));

  // Live hint while typing (NFR-3); the backend enforces the same rule.
  const cnpError =
    form.cnp && !CNP_RE.test(form.cnp) ? "CNP must be exactly 13 digits" : null;

  function openCreate() {
    setEditing(null);
    setForm(EMPTY);
    setFormError(null);
    setOpen(true);
  }

  function openEdit(driver: Driver) {
    setEditing(driver);
    setForm({
      ...EMPTY,
      email: driver.email,
      full_name: driver.full_name,
      phone: driver.phone ?? "",
      cnp: "", // never shown back; leave empty to keep unchanged
      license_number: driver.license_number,
      license_series: driver.license_series ?? "",
      license_category: driver.license_category,
      license_expiry: driver.license_expiry,
    });
    setFormError(null);
    setOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFormError(null);
    try {
      if (editing) {
        await DriversApi.update(editing.id, {
          phone: form.phone || null,
          license_number: form.license_number,
          license_series: form.license_series || null,
          license_category: form.license_category,
          license_expiry: form.license_expiry,
          ...(form.cnp ? { cnp: form.cnp } : {}),
        });
      } else {
        await DriversApi.create({
          email: form.email,
          full_name: form.full_name,
          password: form.password,
          cnp: form.cnp,
          phone: form.phone || null,
          license_number: form.license_number,
          license_series: form.license_series || null,
          license_category: form.license_category,
          license_expiry: form.license_expiry,
        });
      }
      setOpen(false);
      reload();
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(driver: Driver) {
    if (!window.confirm(`Hide driver ${driver.full_name}? Their login is deactivated.`)) return;
    await DriversApi.remove(driver.id);
    reload();
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Drivers</h1>
        <Button onClick={openCreate}>Add driver</Button>
      </div>
      <ErrorText message={error} />
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No drivers yet.</Empty>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <Table headers={["Name", "Email", "Phone", "CNP", "License", "Expires", ""]}>
            {(data ?? []).map((d) => (
              <tr key={d.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-medium">{d.full_name}</td>
                <td className="px-3 py-2">{d.email}</td>
                <td className="px-3 py-2">{d.phone ?? "—"}</td>
                {/* masked by the API — the raw CNP never leaves the backend */}
                <td className="px-3 py-2 font-mono text-xs">{d.cnp_masked}</td>
                <td className="px-3 py-2">
                  {d.license_series ? `${d.license_series} ` : ""}
                  {d.license_number} ({d.license_category})
                </td>
                <td className="px-3 py-2">{fmtDate(d.license_expiry)}</td>
                <td className="px-3 py-2 text-right">
                  <Button variant="ghost" onClick={() => openEdit(d)}>
                    Edit
                  </Button>
                  <Button variant="ghost" className="text-red-600" onClick={() => handleDelete(d)}>
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
        </div>
      )}

      <Modal
        title={editing ? `Edit ${editing.full_name}` : "Add driver"}
        open={open}
        onClose={() => setOpen(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            {!editing && (
              <>
                <Field label="Full name">
                  <Input
                    value={form.full_name}
                    onChange={(e) => set({ full_name: e.target.value })}
                    required
                  />
                </Field>
                <Field label="Email (login)">
                  <Input
                    type="email"
                    value={form.email}
                    onChange={(e) => set({ email: e.target.value })}
                    required
                  />
                </Field>
                <Field label="Password" hint="At least 8 characters">
                  <Input
                    type="password"
                    minLength={8}
                    value={form.password}
                    onChange={(e) => set({ password: e.target.value })}
                    required
                  />
                </Field>
              </>
            )}
            <Field
              label={editing ? "New CNP (leave empty to keep)" : "CNP"}
              error={cnpError}
              hint="Stored encrypted, always shown masked"
            >
              <Input
                inputMode="numeric"
                maxLength={13}
                value={form.cnp}
                onChange={(e) => set({ cnp: e.target.value.replace(/\D/g, "") })}
                required={!editing}
              />
            </Field>
            <Field label="Phone">
              <Input value={form.phone} onChange={(e) => set({ phone: e.target.value })} />
            </Field>
            <Field label="License number">
              <Input
                value={form.license_number}
                onChange={(e) => set({ license_number: e.target.value })}
                required
              />
            </Field>
            <Field label="License series">
              <Input
                value={form.license_series}
                onChange={(e) => set({ license_series: e.target.value })}
              />
            </Field>
            <Field label="Category">
              <Input
                value={form.license_category}
                onChange={(e) => set({ license_category: e.target.value })}
                required
              />
            </Field>
            <Field label="License expiry">
              <Input
                type="date"
                value={form.license_expiry}
                onChange={(e) => set({ license_expiry: e.target.value })}
                required
              />
            </Field>
          </div>
          <ErrorText message={formError} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? "Saving…" : editing ? "Save changes" : "Create driver + login"}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
