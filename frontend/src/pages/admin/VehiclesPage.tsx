import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { VehiclesApi } from "../../api/resources";
import type { FuelType, Vehicle, VehicleStatus } from "../../api/types";
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
import { fmtKm } from "../../lib/fmt";

// Mirrors the backend's validators (backend/app/schemas/vehicle.py) so the
// form gives feedback on every keystroke (NFR-3) without a round-trip.
const PLATE_RE = /^[A-Z]{1,2}-\d{2,3}-[A-Z]{3}$/;
const VIN_RE = /^[A-HJ-NPR-Z0-9]{17}$/;

const FUEL_TYPES: FuelType[] = ["petrol", "diesel", "electric", "hybrid", "lpg"];
const STATUSES: VehicleStatus[] = ["active", "in_service", "unavailable"];

interface FormState {
  plate: string;
  vin: string;
  make: string;
  model: string;
  year: string;
  fuel_type: FuelType;
  tank_capacity_l: string;
  fuel_card_number: string;
  status: VehicleStatus;
  current_km: string;
}

const EMPTY_FORM: FormState = {
  plate: "",
  vin: "",
  make: "",
  model: "",
  year: String(new Date().getFullYear()),
  fuel_type: "diesel",
  tank_capacity_l: "50",
  fuel_card_number: "",
  status: "active",
  current_km: "0",
};

function VehicleForm({
  initial,
  editing,
  onSaved,
  onClose,
}: {
  initial: FormState;
  editing: Vehicle | null;
  onSaved: () => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (patch: Partial<FormState>) => setForm((f) => ({ ...f, ...patch }));

  const plateInput = form.plate.trim().toUpperCase();
  const vinInput = form.vin.trim().toUpperCase();
  const plateError =
    plateInput && !PLATE_RE.test(plateInput)
      ? "Expected format like B-123-ABC or CJ-99-XYZ"
      : null;
  const vinError =
    vinInput && !VIN_RE.test(vinInput)
      ? "VIN must be exactly 17 characters (A–Z except I/O/Q, digits)"
      : null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const common = {
        make: form.make,
        model: form.model,
        year: Number(form.year),
        fuel_type: form.fuel_type,
        tank_capacity_l: Number(form.tank_capacity_l),
        fuel_card_number: form.fuel_card_number || null,
        status: form.status,
        current_km: Number(form.current_km),
      };
      if (editing) {
        await VehiclesApi.update(editing.id, common);
      } else {
        await VehiclesApi.create({ ...common, plate: plateInput, vin: vinInput });
      }
      onSaved();
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Plate" error={plateError} hint={editing ? "Plate cannot be changed" : undefined}>
          <Input
            value={form.plate}
            onChange={(e) => set({ plate: e.target.value.toUpperCase() })}
            placeholder="B-123-ABC"
            required
            disabled={!!editing}
          />
        </Field>
        <Field label="VIN" error={vinError} hint={editing ? "VIN cannot be changed" : undefined}>
          <Input
            value={form.vin}
            onChange={(e) => set({ vin: e.target.value.toUpperCase() })}
            maxLength={17}
            required
            disabled={!!editing}
          />
        </Field>
        <Field label="Make">
          <Input value={form.make} onChange={(e) => set({ make: e.target.value })} required />
        </Field>
        <Field label="Model">
          <Input value={form.model} onChange={(e) => set({ model: e.target.value })} required />
        </Field>
        <Field label="Year">
          <Input
            type="number"
            min={1950}
            max={2100}
            value={form.year}
            onChange={(e) => set({ year: e.target.value })}
            required
          />
        </Field>
        <Field label="Fuel type">
          <Select value={form.fuel_type} onChange={(e) => set({ fuel_type: e.target.value as FuelType })}>
            {FUEL_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Tank capacity (L)">
          <Input
            type="number"
            min={1}
            step="0.1"
            value={form.tank_capacity_l}
            onChange={(e) => set({ tank_capacity_l: e.target.value })}
            required
          />
        </Field>
        <Field label="Fuel card number" hint="Used to match fuel-import rows">
          <Input
            value={form.fuel_card_number}
            onChange={(e) => set({ fuel_card_number: e.target.value })}
          />
        </Field>
        <Field label="Status">
          <Select value={form.status} onChange={(e) => set({ status: e.target.value as VehicleStatus })}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </Select>
        </Field>
        <Field
          label="Odometer (km)"
          hint={editing ? "Manual edits are recorded in the audit log" : undefined}
        >
          <Input
            type="number"
            min={0}
            value={form.current_km}
            onChange={(e) => set({ current_km: e.target.value })}
            required
          />
        </Field>
      </div>
      <ErrorText message={error} />
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? "Saving…" : editing ? "Save changes" : "Add vehicle"}
        </Button>
      </div>
    </form>
  );
}

export default function VehiclesPage() {
  const { data, loading, error, reload } = useLoad(() => VehiclesApi.list());
  const [modal, setModal] = useState<{ open: boolean; editing: Vehicle | null }>({
    open: false,
    editing: null,
  });

  function openCreate() {
    setModal({ open: true, editing: null });
  }

  function openEdit(v: Vehicle) {
    setModal({ open: true, editing: v });
  }

  async function handleDelete(v: Vehicle) {
    if (!window.confirm(`Hide vehicle ${v.plate}? (soft delete — an admin can still purge it)`)) return;
    await VehiclesApi.remove(v.id);
    reload();
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Vehicles</h1>
        <Button onClick={openCreate}>Add vehicle</Button>
      </div>
      <ErrorText message={error} />
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No vehicles yet — add the first one.</Empty>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <Table headers={["Plate", "Make / Model", "Year", "Fuel", "Odometer", "Status", ""]}>
            {(data ?? []).map((v) => (
              <tr key={v.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-medium">
                  <Link to={`/admin/vehicles/${v.id}`} className="text-sky-700 hover:underline">
                    {v.plate}
                  </Link>
                </td>
                <td className="px-3 py-2">
                  {v.make} {v.model}
                </td>
                <td className="px-3 py-2">{v.year}</td>
                <td className="px-3 py-2">{v.fuel_type}</td>
                <td className="px-3 py-2">{fmtKm(v.current_km)}</td>
                <td className="px-3 py-2">
                  <Badge value={v.status} />
                </td>
                <td className="px-3 py-2 text-right">
                  <Button variant="ghost" onClick={() => openEdit(v)}>
                    Edit
                  </Button>
                  <Button variant="ghost" className="text-red-600" onClick={() => handleDelete(v)}>
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
        </div>
      )}

      <Modal
        title={modal.editing ? `Edit ${modal.editing.plate}` : "Add vehicle"}
        open={modal.open}
        onClose={() => setModal({ open: false, editing: null })}
      >
        <VehicleForm
          initial={
            modal.editing
              ? {
                  plate: modal.editing.plate,
                  vin: modal.editing.vin,
                  make: modal.editing.make,
                  model: modal.editing.model,
                  year: String(modal.editing.year),
                  fuel_type: modal.editing.fuel_type,
                  tank_capacity_l: String(modal.editing.tank_capacity_l),
                  fuel_card_number: modal.editing.fuel_card_number ?? "",
                  status: modal.editing.status,
                  current_km: String(modal.editing.current_km),
                }
              : EMPTY_FORM
          }
          editing={modal.editing}
          onSaved={reload}
          onClose={() => setModal({ open: false, editing: null })}
        />
      </Modal>
    </>
  );
}
